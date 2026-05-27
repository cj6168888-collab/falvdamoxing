from pathlib import Path

from scripts import import_runtime_api_keys


def test_parse_source_supports_key_value(tmp_path: Path):
    source = tmp_path / "keys.txt"
    source.write_text("DASHSCOPE_API_KEY=abc12345678901234567890\nLAW_API_KEY: law-secret\n", encoding="utf-8")

    values = import_runtime_api_keys._parse_source(source)

    assert values["DASHSCOPE_API_KEY"] == "abc12345678901234567890"
    assert values["LAW_API_KEY"] == "law-secret"


def test_parse_source_supports_local_summary_dashscope_label(tmp_path: Path):
    source = tmp_path / "summary.txt"
    source.write_text("通义千问\nsk-testdashscopevalue1234567890\n", encoding="utf-8")

    values = import_runtime_api_keys._parse_source(source)

    assert values == {"DASHSCOPE_API_KEY": "sk-testdashscopevalue1234567890"}
