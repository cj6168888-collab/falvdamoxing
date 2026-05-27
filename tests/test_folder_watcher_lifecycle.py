import types

import app.services.folder_watcher_lifecycle as lifecycle


class FakeColumn:
    def __eq__(self, other):
        return ("eq", other)

    def isnot(self, other):
        return ("isnot", other)


FakeCaseModel = types.SimpleNamespace(
    evidence_folder_enabled=FakeColumn(),
    evidence_folder_path=FakeColumn(),
)


class FakeQuery:
    def __init__(self, cases):
        self.cases = cases
        self.filtered = False

    def filter(self, *criteria):
        self.filtered = bool(criteria)
        return self

    def all(self):
        return self.cases


class FakeSession:
    def __init__(self, cases):
        self.cases = cases
        self.closed = False

    def query(self, model):
        assert model is FakeCaseModel
        return FakeQuery(self.cases)

    def close(self):
        self.closed = True


def _patch_case_query(monkeypatch, cases):
    import app.db.database as database_module
    import app.models.case as case_module

    session = FakeSession(cases)
    monkeypatch.setattr(database_module, "SessionLocal", lambda: session)
    monkeypatch.setattr(case_module, "Case", FakeCaseModel)
    return session


def test_resume_folder_watchers_skips_when_schema_is_not_ready(monkeypatch):
    import app.db.database as database_module

    monkeypatch.setattr(
        lifecycle,
        "check_schema_tables",
        lambda: {"status": "error", "missing_tables": ["cases"]},
    )
    monkeypatch.setattr(
        database_module,
        "SessionLocal",
        lambda: (_ for _ in ()).throw(AssertionError("database should not open")),
    )

    lifecycle.resume_folder_watchers()


def test_resume_folder_watchers_skips_missing_paths(monkeypatch, tmp_path):
    missing_path = tmp_path / "missing"
    case = types.SimpleNamespace(id=10, evidence_folder_path=str(missing_path))
    session = _patch_case_query(monkeypatch, [case])
    calls = []

    class FakeFolderWatcherService:
        @classmethod
        def get_instance(cls, case_id):
            calls.append(case_id)

    monkeypatch.setattr(lifecycle, "check_schema_tables", lambda: {"status": "ok"})
    import app.services.folder_watcher as folder_watcher_module

    monkeypatch.setattr(
        folder_watcher_module,
        "FolderWatcherService",
        FakeFolderWatcherService,
    )

    lifecycle.resume_folder_watchers()

    assert calls == []
    assert session.closed is True


def test_resume_folder_watchers_starts_existing_paths(monkeypatch, tmp_path):
    folder = tmp_path / "evidence"
    folder.mkdir()
    case = types.SimpleNamespace(id=20, evidence_folder_path=str(folder))
    session = _patch_case_query(monkeypatch, [case])
    calls = []

    class FakeWatcher:
        def start_watching(self, folder_path, callback):
            calls.append((folder_path, callback))
            return True

    class FakeFolderWatcherService:
        @classmethod
        def get_instance(cls, case_id):
            calls.append(("case_id", case_id))
            return FakeWatcher()

    monkeypatch.setattr(lifecycle, "check_schema_tables", lambda: {"status": "ok"})
    import app.services.folder_watcher as folder_watcher_module

    monkeypatch.setattr(
        folder_watcher_module,
        "FolderWatcherService",
        FakeFolderWatcherService,
    )

    lifecycle.resume_folder_watchers()

    assert calls[0] == ("case_id", 20)
    assert calls[1][0] == str(folder)
    assert calls[1][1] is lifecycle._incremental_scan_callback
    assert session.closed is True


def test_incremental_scan_callback_closes_service(monkeypatch):
    calls = []

    class FakeEvidenceFolderService:
        def __init__(self, case_id):
            calls.append(("init", case_id))

        def incremental_scan(self, file_paths):
            calls.append(("scan", file_paths))

        def close(self):
            calls.append(("close", None))

    import app.services.evidence_folder_service as evidence_folder_service_module

    monkeypatch.setattr(
        evidence_folder_service_module,
        "EvidenceFolderService",
        FakeEvidenceFolderService,
    )

    lifecycle._incremental_scan_callback(33, ["a.pdf"])

    assert calls == [("init", 33), ("scan", ["a.pdf"]), ("close", None)]


def test_stop_folder_watchers_calls_service(monkeypatch):
    calls = []

    class FakeFolderWatcherService:
        @classmethod
        def stop_all(cls):
            calls.append("stop")

    import app.services.folder_watcher as folder_watcher_module

    monkeypatch.setattr(
        folder_watcher_module,
        "FolderWatcherService",
        FakeFolderWatcherService,
    )

    lifecycle.stop_folder_watchers()

    assert calls == ["stop"]
