"""HTTP SMS gateway adapter for Aliyun Dysmsapi.

The backend already speaks a provider-neutral HTTP contract:
POST /send with {phone, code, purpose, message}. This adapter keeps that
contract stable and translates it to Aliyun's SendSms API.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib import error, parse, request


ALIYUN_ENDPOINT = "https://dysmsapi.aliyuncs.com/"
SUCCESS_CODES = {"OK"}


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _required_env(name: str) -> str:
    value = _env(name)
    if not value:
        raise RuntimeError(f"{name} is required")
    return value


def _percent_encode(value: Any) -> str:
    return parse.quote(str(value), safe="~")


def _canonical_query(params: dict[str, Any]) -> str:
    return "&".join(
        f"{_percent_encode(key)}={_percent_encode(params[key])}"
        for key in sorted(params)
    )


def _sign(params: dict[str, Any], access_key_secret: str) -> str:
    canonical = _canonical_query(params)
    string_to_sign = f"POST&%2F&{_percent_encode(canonical)}"
    digest = hmac.new(
        f"{access_key_secret}&".encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _form_encode(params: dict[str, Any]) -> bytes:
    return _canonical_query(params).encode("utf-8")


def _template_code_for_purpose(purpose: str) -> str:
    purpose_key = purpose.upper().replace("-", "_")
    return (
        _env(f"ALIYUN_SMS_{purpose_key}_TEMPLATE_CODE")
        or _env("ALIYUN_SMS_TEMPLATE_CODE")
    )


def _build_send_sms_params(phone: str, code: str, purpose: str) -> dict[str, Any]:
    template_code = _template_code_for_purpose(purpose)
    if not template_code:
        raise RuntimeError("ALIYUN_SMS_TEMPLATE_CODE is required")

    access_key_id = _required_env("ALIYUN_SMS_ACCESS_KEY_ID")
    access_key_secret = _required_env("ALIYUN_SMS_ACCESS_KEY_SECRET")
    param_name = _env("ALIYUN_SMS_TEMPLATE_PARAM_NAME", "code")
    template_param = json.dumps({param_name: code}, ensure_ascii=False)

    params: dict[str, Any] = {
        "AccessKeyId": access_key_id,
        "Action": "SendSms",
        "Format": "JSON",
        "PhoneNumbers": phone,
        "RegionId": _env("ALIYUN_SMS_REGION_ID", "cn-hangzhou"),
        "SignName": _required_env("ALIYUN_SMS_SIGN_NAME"),
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": str(uuid.uuid4()),
        "SignatureVersion": "1.0",
        "TemplateCode": template_code,
        "TemplateParam": template_param,
        "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "Version": "2017-05-25",
    }
    params["Signature"] = _sign(params, access_key_secret)
    return params


def send_sms(phone: str, code: str, purpose: str) -> dict[str, Any]:
    params = _build_send_sms_params(phone, code, purpose)
    if _env("ALIYUN_SMS_DRY_RUN").lower() in {"1", "true", "yes", "on"}:
        return {"Code": "OK", "Message": "dry-run", "RequestId": "dry-run"}

    req = request.Request(
        ALIYUN_ENDPOINT,
        data=_form_encode(params),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=float(_env("ALIYUN_SMS_TIMEOUT_SECONDS", "10"))) as resp:
            body = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Aliyun SMS HTTP {exc.code}: {body[:500]}") from exc
    return json.loads(body)


def _masked_phone(phone: str) -> str:
    return f"{phone[:3]}****{phone[-4:]}" if len(phone) >= 7 else "****"


class AliyunSMSHandler(BaseHTTPRequestHandler):
    server_version = "LegalAliyunSMSGateway/1.0"

    def _write_json(self, status: int, body: dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path == "/health":
            missing = [
                key
                for key in (
                    "ALIYUN_SMS_ACCESS_KEY_ID",
                    "ALIYUN_SMS_ACCESS_KEY_SECRET",
                    "ALIYUN_SMS_SIGN_NAME",
                )
                if not _env(key)
            ]
            status = 503 if missing else 200
            self._write_json(status, {"status": "ok" if not missing else "missing_config", "missing": missing})
            return
        self._write_json(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path != "/send":
            self._write_json(404, {"detail": "not found"})
            return

        expected_token = _env("SMS_GATEWAY_TOKEN") or _env("SMS_HTTP_TOKEN") or _env("SMS_MOCK_TOKEN")
        authorization = self.headers.get("Authorization", "")
        if expected_token and authorization != f"Bearer {expected_token}":
            self._write_json(401, {"detail": "invalid token"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception:
            self._write_json(400, {"detail": "invalid json"})
            return

        missing = [key for key in ("phone", "code", "purpose") if not payload.get(key)]
        if missing:
            self._write_json(422, {"detail": f"missing fields: {', '.join(missing)}"})
            return

        started = time.perf_counter()
        try:
            provider_response = send_sms(
                phone=str(payload["phone"]),
                code=str(payload["code"]),
                purpose=str(payload["purpose"]),
            )
        except Exception as exc:
            print(f"aliyun_sms send failed phone={_masked_phone(str(payload.get('phone', '')))} error={exc}", flush=True)
            self._write_json(502, {"success": False, "detail": "aliyun sms send failed"})
            return

        elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
        provider_code = str(provider_response.get("Code", ""))
        if provider_code not in SUCCESS_CODES:
            print(
                "aliyun_sms provider rejected "
                f"phone={_masked_phone(str(payload['phone']))} code={provider_code} elapsed_ms={elapsed_ms}",
                flush=True,
            )
            self._write_json(
                502,
                {
                    "success": False,
                    "provider": "aliyun",
                    "provider_code": provider_code,
                    "request_id": provider_response.get("RequestId", ""),
                },
            )
            return

        print(
            f"aliyun_sms sent phone={_masked_phone(str(payload['phone']))} purpose={payload['purpose']} elapsed_ms={elapsed_ms}",
            flush=True,
        )
        self._write_json(
            200,
            {
                "success": True,
                "provider": "aliyun",
                "request_id": provider_response.get("RequestId", ""),
                "elapsed_ms": elapsed_ms,
            },
        )

    def log_message(self, format: str, *args: Any) -> None:
        print("%s - %s" % (self.address_string(), format % args), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Aliyun SMS HTTP gateway adapter.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8088)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), AliyunSMSHandler)
    print(f"Aliyun SMS gateway listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
