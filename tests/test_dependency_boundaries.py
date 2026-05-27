from pathlib import Path


def _requirement_names(path: str) -> set[str]:
    names = set()
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or line.startswith("-"):
            continue
        markerless = line.split(";", 1)[0].strip()
        name = markerless.split("[", 1)[0]
        for operator in ("==", ">=", "<=", "~=", "!=", ">", "<"):
            name = name.split(operator, 1)[0]
        names.add(name.strip().lower().replace("_", "-"))
    return names


def test_core_requirements_exclude_optional_heavy_packages():
    core = _requirement_names("requirements-core.txt")

    forbidden = {
        "celery",
        "chromadb",
        "langchain",
        "langchain-core",
        "langchain-openai",
        "paddleocr",
        "paddlepaddle",
        "pytesseract",
        "sentence-transformers",
        "streamlit",
        "weasyprint",
    }

    assert core.isdisjoint(forbidden)


def test_optional_and_worker_requirements_keep_expected_boundaries():
    optional = _requirement_names("requirements-optional.txt")
    worker = _requirement_names("requirements-worker.txt")

    assert {
        "chromadb",
        "langchain",
        "langchain-core",
        "langchain-openai",
        "paddleocr",
        "sentence-transformers",
    }.issubset(optional)
    assert "celery" in worker
    assert worker.isdisjoint(optional)
