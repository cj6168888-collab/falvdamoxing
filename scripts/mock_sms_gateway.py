"""Tiny HTTP SMS gateway for local staging tests.

This is not a production SMS provider. It implements the same HTTP contract
that the backend expects so a production-like Docker stack can be tested without
external SMS credentials.
"""

from __future__ import annotations

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


MESSAGES: list[dict] = []


class SMSMockHandler(BaseHTTPRequestHandler):
    server_version = "LegalSMSMock/1.0"

    def _write_json(self, status: int, body: dict) -> None:
        data = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path == "/health":
            self._write_json(200, {"status": "ok"})
            return
        if self.path == "/messages":
            self._write_json(200, {"messages": MESSAGES[-50:]})
            return
        self._write_json(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        if self.path != "/send":
            self._write_json(404, {"detail": "not found"})
            return

        expected_token = os.environ.get("SMS_MOCK_TOKEN", "")
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

        missing = [key for key in ("phone", "code", "purpose", "message") if not payload.get(key)]
        if missing:
            self._write_json(422, {"detail": f"missing fields: {', '.join(missing)}"})
            return

        MESSAGES.append(payload)
        self._write_json(200, {"success": True})

    def log_message(self, format: str, *args) -> None:
        print("%s - %s" % (self.address_string(), format % args), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a local staging SMS mock.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8088)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), SMSMockHandler)
    print(f"SMS mock listening on http://{args.host}:{args.port}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
