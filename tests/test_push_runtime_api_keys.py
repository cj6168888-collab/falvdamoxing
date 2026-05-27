from pathlib import Path

from scripts.push_runtime_api_keys import _login, _parse_env


def test_parse_env_ignores_comments_and_empty_values(tmp_path: Path):
    source = tmp_path / "api-keys.env"
    source.write_text(
        "# comment\nDASHSCOPE_API_KEY=abc123\nEMPTY=\nLAW_API_KEY='law123'\n",
        encoding="utf-8",
    )

    assert _parse_env(source) == {
        "DASHSCOPE_API_KEY": "abc123",
        "LAW_API_KEY": "law123",
    }


def test_login_returns_access_token():
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"tokens": {"access_token": "token-123"}}

    class FakeClient:
        def post(self, path, json):
            assert path == "/api/auth/login"
            assert json == {"username": "u", "password": "p"}
            return FakeResponse()

    assert _login(FakeClient(), "u", "p") == "token-123"
