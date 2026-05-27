"""Low-frequency acceptance smoke for real SMS registration/password reset.

This script intentionally supports a manual verification-code handoff. In a
real provider environment SMS_DEBUG_RETURN_CODE should be disabled, so the code
must come from the test phone or be passed explicitly by the operator.
"""

from __future__ import annotations

import argparse
import getpass
import secrets
import sys
import time
from typing import Any

import httpx


def _post(client: httpx.Client, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = client.post(path, json=payload)
    if response.status_code >= 400:
        raise RuntimeError(f"POST {path} failed: HTTP {response.status_code} {response.text[:300]}")
    return response.json()


def _code_from_response_or_operator(
    *,
    purpose: str,
    response: dict[str, Any],
    supplied_code: str,
    allow_debug_code: bool,
    prompt_codes: bool,
) -> str:
    if supplied_code:
        return supplied_code.strip()
    if allow_debug_code and response.get("debug_code"):
        return str(response["debug_code"])
    if prompt_codes:
        return getpass.getpass(f"请输入手机收到的 {purpose} 验证码: ").strip()
    raise RuntimeError(
        f"{purpose} verification code is required. Re-run with --{purpose}-code, "
        "--prompt-codes, or --allow-debug-code for mock/debug environments."
    )


def _login(client: httpx.Client, phone: str, password: str) -> bool:
    response = client.post("/api/auth/login", json={"username": phone, "password": password})
    return response.status_code == 200 and response.json().get("success") is True


def run(args: argparse.Namespace) -> dict[str, Any]:
    username = args.username or f"sms_{int(time.time())}_{secrets.token_hex(3)}"
    password = args.password
    new_password = args.new_password
    result: dict[str, Any] = {
        "base_url": args.base_url,
        "phone_suffix": args.phone[-4:],
        "mode": args.mode,
        "registered": False,
        "old_login_ok": False,
        "old_login_after_reset_rejected": False,
        "new_login_ok": False,
    }

    with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=args.timeout_seconds, trust_env=False) as client:
        if args.mode in {"full", "register"}:
            send_register = _post(client, "/api/auth/sms/send", {"phone": args.phone, "purpose": "register"})
            register_code = _code_from_response_or_operator(
                purpose="register",
                response=send_register,
                supplied_code=args.register_code,
                allow_debug_code=args.allow_debug_code,
                prompt_codes=args.prompt_codes,
            )
            register_payload = {
                "phone": args.phone,
                "sms_code": register_code,
                "password": password,
                "username": username,
                "email": args.email or f"{username}@real-sms.local.invalid",
                "full_name": args.full_name,
                "tenant_name": args.tenant_name,
                "tenant_type": args.tenant_type,
            }
            register = _post(client, "/api/auth/register/phone", register_payload)
            result["registered"] = register.get("success") is True
            result["username"] = register.get("user", {}).get("username", username)

        if args.mode in {"full", "password-reset"}:
            result["old_login_ok"] = _login(client, args.phone, password)
            if args.mode == "full" and not result["old_login_ok"]:
                raise RuntimeError("old password login failed before reset")

            send_reset = _post(client, "/api/auth/sms/send", {"phone": args.phone, "purpose": "password_reset"})
            reset_code = _code_from_response_or_operator(
                purpose="reset",
                response=send_reset,
                supplied_code=args.reset_code,
                allow_debug_code=args.allow_debug_code,
                prompt_codes=args.prompt_codes,
            )
            reset = _post(
                client,
                "/api/auth/password-reset/confirm",
                {"phone": args.phone, "sms_code": reset_code, "new_password": new_password},
            )
            result["reset_ok"] = reset.get("success") is True
            result["old_login_after_reset_rejected"] = not _login(client, args.phone, password)
            result["new_login_ok"] = _login(client, args.phone, new_password)
            if not result["new_login_ok"]:
                raise RuntimeError("new password login failed after reset")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Run real SMS auth acceptance smoke.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8080")
    parser.add_argument("--phone", required=True, help="Dedicated test phone number.")
    parser.add_argument("--mode", choices=["full", "register", "password-reset"], default="full")
    parser.add_argument("--username", default="")
    parser.add_argument("--email", default="")
    parser.add_argument("--password", default=f"OldSms#{secrets.token_hex(4)}")
    parser.add_argument("--new-password", default=f"NewSms#{secrets.token_hex(4)}")
    parser.add_argument("--tenant-name", default="真实短信验收租户")
    parser.add_argument("--tenant-type", default="law_firm")
    parser.add_argument("--full-name", default="真实短信验收用户")
    parser.add_argument("--register-code", default="")
    parser.add_argument("--reset-code", default="")
    parser.add_argument("--prompt-codes", action="store_true")
    parser.add_argument("--allow-debug-code", action="store_true")
    parser.add_argument("--timeout-seconds", type=float, default=30)
    args = parser.parse_args()

    try:
        result = run(args)
    except Exception as exc:
        print(f"REAL_SMS_AUTH_SMOKE_FAIL: {exc}", file=sys.stderr)
        return 1

    printable = {
        key: value
        for key, value in result.items()
        if key not in {"password", "new_password"}
    }
    print(f"REAL_SMS_AUTH_SMOKE_PASS: {printable}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
