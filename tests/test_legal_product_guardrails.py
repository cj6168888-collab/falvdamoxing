from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SCAN_ROOTS = [
    PROJECT_ROOT / "frontend" / "src",
    PROJECT_ROOT / "app" / "api",
    PROJECT_ROOT / "app" / "services",
    PROJECT_ROOT / "app" / "models",
    PROJECT_ROOT / "docs",
]

TEXT_SUFFIXES = {".md", ".py", ".ts", ".tsx"}

ALLOWLISTED_DOCS = {
    "docs/legal-ai-product-guardrails.md",
    "docs/lawyer-workflow-upgrade-roadmap.md",
}

FORBIDDEN_TERMS = {
    "AI律师",
    "AI 律师",
    "胜诉概率",
    "胜诉率",
    "一键生成",
    "深度创作",
    "攻击点",
    "精准预测",
    "必然胜诉",
}


def _is_compatibility_exception(path: Path, term: str, line: str) -> bool:
    rel = path.relative_to(PROJECT_ROOT).as_posix()

    if rel == "app/api/adversarial.py" and term == "胜诉概率":
        return (
            "胜诉概率: Optional[float]" in line
            or "data.胜诉概率" in line
        )

    if rel in ALLOWLISTED_DOCS:
        return True

    return False


def _iter_scan_files():
    for root in SCAN_ROOTS:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in TEXT_SUFFIXES:
                yield path


def test_user_facing_legal_ai_wording_stays_inside_guardrails():
    violations: list[str] = []

    for path in _iter_scan_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), 1):
            for term in FORBIDDEN_TERMS:
                if term in line and not _is_compatibility_exception(path, term, line):
                    rel = path.relative_to(PROJECT_ROOT).as_posix()
                    violations.append(f"{rel}:{line_no}: contains {term!r}: {line.strip()}")

    assert not violations, "High-risk legal AI wording found:\n" + "\n".join(violations)


def test_user_facing_evidence_score_wording_uses_workpaper_language():
    files = [
        PROJECT_ROOT / "app" / "api" / "evidence_graph_api.py",
        PROJECT_ROOT / "app" / "api" / "streaming_analysis.py",
        PROJECT_ROOT / "app" / "services" / "evidence_context_injector.py",
        PROJECT_ROOT / "app" / "services" / "evidence_qa.py",
        PROJECT_ROOT / "app" / "services" / "smart_qa_v2.py",
        PROJECT_ROOT / "frontend" / "src" / "components" / "evidence",
        PROJECT_ROOT / "frontend" / "src" / "components" / "smart-chat",
        PROJECT_ROOT / "frontend" / "src" / "components" / "senior-analysis",
        PROJECT_ROOT / "frontend" / "src" / "pages" / "cases" / "[id]" / "evidence.tsx",
        PROJECT_ROOT / "frontend" / "src" / "pages" / "insight" / "[caseId].tsx",
    ]
    forbidden = ["信度评分", "可信度/强度", "信度 ", "信度：", "/信度", "低信度", "高信度"]
    violations: list[str] = []

    for item in files:
        paths = item.rglob("*") if item.is_dir() else [item]
        for path in paths:
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for line_no, line in enumerate(text.splitlines(), 1):
                for term in forbidden:
                    if term in line:
                        rel = path.relative_to(PROJECT_ROOT).as_posix()
                        violations.append(f"{rel}:{line_no}: contains {term!r}: {line.strip()}")

    assert not violations, "Evidence score wording should use proof-strength/workpaper language:\n" + "\n".join(violations)
