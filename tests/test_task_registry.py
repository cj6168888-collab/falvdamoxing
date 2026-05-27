import app.tasks.registry as registry


def test_register_task_handlers_imports_declared_modules(monkeypatch):
    imported_modules = []

    monkeypatch.setattr(
        registry.importlib,
        "import_module",
        lambda module_name: imported_modules.append(module_name),
    )

    registry.register_task_handlers()

    assert imported_modules == list(registry.TASK_HANDLER_MODULES)
