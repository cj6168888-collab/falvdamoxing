import importlib
import builtins
import subprocess
import sys
import textwrap


def test_legal_agent_tools_import_without_langchain(monkeypatch):
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name.startswith("langchain") or name.startswith("langchain_openai"):
            raise ImportError(f"No module named {name}")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)

    module = importlib.reload(importlib.import_module("app.services.legal_agent_tools"))

    try:
        assert module.LANGCHAIN_AVAILABLE is False
        assert module.legal_agent_tools.get_tools() == []
        result = module.legal_agent_executor.execute("请分析证据和诉讼时效")
        assert result["success"] is True
        assert isinstance(result["tools_used"], list)
    finally:
        monkeypatch.undo()
        importlib.reload(module)


def test_app_imports_without_optional_heavy_dependencies():
    code = textwrap.dedent(
        """
        import builtins
        import importlib

        blocked = (
            "chromadb",
            "langchain",
            "langchain_openai",
            "paddleocr",
            "paddlepaddle",
            "pytesseract",
            "sentence_transformers",
            "streamlit",
            "weasyprint",
        )
        real_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith(blocked):
                raise ImportError(f"blocked optional dependency: {name}")
            return real_import(name, globals, locals, fromlist, level)

        builtins.__import__ = guarded_import
        module = importlib.import_module("app.main")
        assert module.app is not None
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, result.stderr
