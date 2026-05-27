import types
import warnings
from collections import defaultdict

import pytest
from fastapi import FastAPI
from fastapi import APIRouter

from app.api import routes as route_module
from app.api.routes import RouterSpec
from app.api.routes import ROUTER_SPECS
from app.api.routes import register_routes
from app.app_factory import create_app
import app.app_factory as app_factory_module
from app.api import case_structure
from app.api import dashboard
from app.api import reminder
from app.api import report_api
from app.main import app
from app.tasks.registry import TASK_HANDLER_MODULES


def _route_paths(app: FastAPI) -> set[str]:
    return {route.path for route in app.routes}


def _route_method_paths(app: FastAPI) -> dict[tuple[str, str], list[str]]:
    method_paths = defaultdict(list)
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        endpoint = getattr(route, "endpoint", None)
        if not methods or not path:
            continue
        endpoint_name = getattr(endpoint, "__name__", "<unknown>")
        for method in methods - {"HEAD", "OPTIONS"}:
            method_paths[(method, path)].append(endpoint_name)
    return method_paths


def _route_endpoint_modules(app: FastAPI) -> dict[tuple[str, str], str]:
    endpoints = {}
    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)
        endpoint = getattr(route, "endpoint", None)
        if not methods or not path:
            continue
        for method in methods - {"HEAD", "OPTIONS"}:
            endpoints[(method, path)] = endpoint.__module__
    return endpoints


def test_main_app_registers_key_api_routes():
    paths = _route_paths(app)

    assert "/api/cases" in paths
    assert "/api/third-party/health" in paths
    assert "/api/streaming-analysis/create" in paths
    assert "/api/smart-chat/health" in paths
    assert "/api/config/api-keys" in paths
    assert "/api/auth/login" in paths


def test_create_app_mounts_static_file_route():
    test_app = create_app()

    assert any(
        route.path == "/api/files" and route.name == "files"
        for route in test_app.routes
    )


def test_create_app_can_skip_static_file_route():
    test_app = create_app(include_static_files=False)

    assert not any(route.path == "/api/files" for route in test_app.routes)


def test_create_app_registers_task_handlers(monkeypatch):
    calls = []

    monkeypatch.setattr(app_factory_module, "register_task_handlers", lambda: calls.append("tasks"))

    create_app()

    assert calls == ["tasks"]


def test_create_app_can_skip_task_handlers(monkeypatch):
    calls = []

    monkeypatch.setattr(app_factory_module, "register_task_handlers", lambda: calls.append("tasks"))

    create_app(include_task_handlers=False)

    assert calls == []


def test_create_app_has_no_duplicate_route_method_paths(lightweight_app):
    method_paths = _route_method_paths(lightweight_app)
    duplicates = {
        key: endpoints
        for key, endpoints in method_paths.items()
        if len(endpoints) > 1
    }

    assert duplicates == {}


def test_current_routes_do_not_depend_on_duplicate_rejection(monkeypatch):
    monkeypatch.setattr(
        route_module,
        "_reject_duplicate_routes",
        lambda *args, **kwargs: None,
    )

    test_app = FastAPI()
    register_routes(test_app)
    method_paths = _route_method_paths(test_app)
    duplicates = {
        key: endpoints
        for key, endpoints in method_paths.items()
        if len(endpoints) > 1
    }

    assert duplicates == {}


def test_register_routes_rejects_duplicate_method_paths():
    test_app = FastAPI()
    router = APIRouter()

    @router.get("/duplicate")
    def first_route():
        return {"route": "first"}

    test_app.include_router(router)

    duplicate_router = APIRouter()

    @duplicate_router.get("/duplicate")
    def second_route():
        return {"route": "second"}

    first_added_route_index = len(test_app.router.routes)
    test_app.include_router(duplicate_router)

    with pytest.raises(RuntimeError, match="Duplicate route registration blocked"):
        route_module._reject_duplicate_routes(
            test_app,
            existing_signatures={("GET", "/duplicate")},
            first_added_route_index=first_added_route_index,
            spec=RouterSpec("tests.duplicate"),
            logger=None,
        )


def test_openapi_schema_generation_has_no_duplicate_operation_warnings(lightweight_app):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        lightweight_app.openapi()

    duplicate_warnings = [
        item
        for item in caught
        if "Duplicate Operation ID" in str(item.message)
    ]
    assert duplicate_warnings == []


def test_canonical_routes_own_legacy_duplicate_paths(lightweight_app):
    endpoints = _route_endpoint_modules(lightweight_app)

    expected_modules = {
        ("POST", "/api/cases/{case_id}/threads"): "app.api.case",
        ("GET", "/api/cases/{case_id}/threads"): "app.api.case",
        ("POST", "/api/cases/{case_id}/parties"): "app.api.case",
        ("GET", "/api/cases/{case_id}/parties"): "app.api.case",
        ("POST", "/api/cases/{case_id}/counter-claims"): "app.api.case",
        ("GET", "/api/cases/{case_id}/counter-claims"): "app.api.case",
        ("GET", "/api/reminders"): "app.api.tracking_api",
        ("POST", "/api/reminders"): "app.api.tracking_api",
        ("GET", "/api/reminders/stats"): "app.api.tracking_api",
        ("GET", "/api/reminders/{reminder_id}"): "app.api.tracking_api",
        ("PUT", "/api/reminders/{reminder_id}"): "app.api.tracking_api",
        ("DELETE", "/api/reminders/{reminder_id}"): "app.api.tracking_api",
        ("GET", "/api/dashboard"): "app.api.tracking_api",
        ("GET", "/api/dashboard/stats"): "app.api.tracking_api",
        ("GET", "/api/dashboard/urgent"): "app.api.tracking_api",
        ("GET", "/api/dashboard/upcoming"): "app.api.tracking_api",
        ("GET", "/api/reports/export/{report_id}"): "app.api.report_api",
    }

    for route_key, module_name in expected_modules.items():
        assert endpoints[route_key] == module_name


def test_extension_routes_remain_registered(lightweight_app):
    endpoints = _route_endpoint_modules(lightweight_app)

    expected_modules = {
        ("GET", "/api/cases/{case_id}/structure"): "app.api.case_structure",
        ("GET", "/api/cases/threads/{thread_id}"): "app.api.case_structure",
        ("PUT", "/api/cases/threads/{thread_id}"): "app.api.case_structure",
        ("DELETE", "/api/cases/threads/{thread_id}"): "app.api.case_structure",
        ("GET", "/api/cases/parties/{party_id}"): "app.api.case_structure",
        ("PUT", "/api/cases/parties/{party_id}"): "app.api.case_structure",
        ("DELETE", "/api/cases/parties/{party_id}"): "app.api.case_structure",
        ("GET", "/api/reminders/overdue"): "app.api.reminder",
        ("PUT", "/api/reminders/batch"): "app.api.reminder",
        ("PUT", "/api/reminders/mark-all-read"): "app.api.reminder",
        ("POST", "/api/reminders/auto-generate"): "app.api.reminder",
        ("POST", "/api/reminders/auto-generate-all"): "app.api.reminder",
        ("PUT", "/api/reminders/{reminder_id}/complete"): "app.api.reminder",
        ("PUT", "/api/reminders/{reminder_id}/snooze"): "app.api.reminder",
        ("GET", "/api/dashboard/recent-cases"): "app.api.dashboard",
        ("GET", "/api/dashboard/ai-suggestions"): "app.api.dashboard",
        ("GET", "/api/dashboard/activity"): "app.api.dashboard",
    }

    for route_key, module_name in expected_modules.items():
        assert endpoints[route_key] == module_name


def test_static_reminder_extension_routes_precede_legacy_dynamic_routes(lightweight_app):
    reminder_routes = [
        (route.path, frozenset(getattr(route, "methods", set())))
        for route in lightweight_app.routes
        if getattr(route, "path", "").startswith("/api/reminders")
    ]

    def route_index(path: str, method: str) -> int:
        for index, (candidate_path, methods) in enumerate(reminder_routes):
            if candidate_path == path and method in methods:
                return index
        raise AssertionError(f"Route not registered: {method} {path}")

    assert route_index("/api/reminders/overdue", "GET") < route_index("/api/reminders/{reminder_id}", "GET")
    assert route_index("/api/reminders/batch", "PUT") < route_index("/api/reminders/{reminder_id}", "PUT")


def test_extension_routes_publish_response_models(lightweight_app):
    schema = lightweight_app.openapi()
    paths = schema["paths"]

    expected_refs = {
        ("/api/dashboard/recent-cases", "get"): "#/components/schemas/RecentCasesResponse",
        ("/api/dashboard/activity", "get"): "#/components/schemas/ActivityLogResponse",
        ("/api/reminders/overdue", "get"): "#/components/schemas/ReminderListResponse",
        ("/api/reminders/batch", "put"): "#/components/schemas/BatchUpdateResponse",
        ("/api/reminders/mark-all-read", "put"): "#/components/schemas/MessageCountResponse",
        ("/api/reminders/auto-generate", "post"): "#/components/schemas/ReminderGenerateResponse",
        ("/api/reminders/auto-generate-all", "post"): "#/components/schemas/AutoGenerateAllResponse",
        ("/api/reminders/{reminder_id}/complete", "put"): "#/components/schemas/ReminderActionResponse",
        ("/api/reminders/{reminder_id}/snooze", "put"): "#/components/schemas/ReminderActionResponse",
        ("/api/cases/threads/{thread_id}", "get"): "#/components/schemas/ThreadResponse",
        ("/api/cases/threads/{thread_id}", "put"): "#/components/schemas/ThreadResponse",
        ("/api/cases/threads/{thread_id}", "delete"): "#/components/schemas/MessageResponse",
        ("/api/cases/parties/{party_id}", "get"): "#/components/schemas/PartyResponse",
        ("/api/cases/parties/{party_id}", "put"): "#/components/schemas/PartyResponse",
        ("/api/cases/parties/{party_id}", "delete"): "#/components/schemas/MessageResponse",
        ("/api/cases/counter-claims/{claim_id}", "put"): "#/components/schemas/CounterClaimResponse",
        ("/api/cases/counter-claims/{claim_id}", "delete"): "#/components/schemas/MessageResponse",
        ("/api/cases/{case_id}/structure", "get"): "#/components/schemas/CaseStructureResponse",
    }

    for (path, method), schema_ref in expected_refs.items():
        assert (
            paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            == schema_ref
        )


def test_canonical_case_routes_publish_response_models(lightweight_app):
    schema = lightweight_app.openapi()
    paths = schema["paths"]

    expected_refs = {
        ("/api/cases/{case_id}/threads", "post"): "#/components/schemas/CaseThreadItemResponse",
        ("/api/cases/{case_id}/threads/{thread_id}", "put"): "#/components/schemas/CaseThreadItemResponse",
        ("/api/cases/{case_id}/threads/{thread_id}", "delete"): "#/components/schemas/CaseMessageResponse",
        ("/api/cases/{case_id}/parties", "post"): "#/components/schemas/CasePartyItemResponse",
        ("/api/cases/{case_id}/parties/{party_id}", "put"): "#/components/schemas/CasePartyItemResponse",
        ("/api/cases/{case_id}/parties/{party_id}", "delete"): "#/components/schemas/CaseMessageResponse",
        ("/api/cases/{case_id}/counter-claims", "post"): "#/components/schemas/CaseCounterClaimItemResponse",
        ("/api/cases/{case_id}/counter-claims/{claim_id}", "put"): "#/components/schemas/CaseCounterClaimItemResponse",
        ("/api/cases/{case_id}/counter-claims/{claim_id}", "delete"): "#/components/schemas/CaseMessageResponse",
    }
    expected_array_refs = {
        ("/api/cases/{case_id}/threads", "get"): "#/components/schemas/CaseThreadItemResponse",
        ("/api/cases/{case_id}/parties", "get"): "#/components/schemas/CasePartyItemResponse",
        ("/api/cases/{case_id}/counter-claims", "get"): "#/components/schemas/CaseCounterClaimItemResponse",
    }

    for (path, method), schema_ref in expected_refs.items():
        assert (
            paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            == schema_ref
        )

    for (path, method), item_ref in expected_array_refs.items():
        response_schema = paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["type"] == "array"
        assert response_schema["items"]["$ref"] == item_ref


def test_auth_routes_publish_response_models(lightweight_app):
    schema = lightweight_app.openapi()
    paths = schema["paths"]

    expected_refs = {
        ("/api/auth/register", "post"): "#/components/schemas/RegisterResponse",
        ("/api/auth/login", "post"): "#/components/schemas/AuthResponse",
        ("/api/auth/refresh", "post"): "#/components/schemas/RefreshResponse",
        ("/api/auth/me", "get"): "#/components/schemas/CurrentUserResponse",
    }

    for (path, method), schema_ref in expected_refs.items():
        assert (
            paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            == schema_ref
        )


def test_storage_crud_routes_publish_response_models(lightweight_app):
    schema = lightweight_app.openapi()
    paths = schema["paths"]

    expected_refs = {
        ("/api/contracts/", "post"): "#/components/schemas/ContractMutationResponse",
        ("/api/contracts/{contract_id}", "get"): "#/components/schemas/ContractResponse",
        ("/api/contracts/{contract_id}", "put"): "#/components/schemas/ContractMutationResponse",
        ("/api/contracts/{contract_id}", "delete"): "#/components/schemas/ContractMutationResponse",
        ("/api/loans/", "post"): "#/components/schemas/LoanMutationResponse",
        ("/api/loans/{loan_id}", "get"): "#/components/schemas/LoanResponse",
        ("/api/loans/{loan_id}", "put"): "#/components/schemas/LoanMutationResponse",
        ("/api/loans/{loan_id}", "delete"): "#/components/schemas/LoanMutationResponse",
    }
    expected_array_refs = {
        ("/api/contracts/", "get"): "#/components/schemas/ContractResponse",
        ("/api/loans/", "get"): "#/components/schemas/LoanResponse",
    }

    for (path, method), schema_ref in expected_refs.items():
        assert (
            paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            == schema_ref
        )

    for (path, method), item_ref in expected_array_refs.items():
        response_schema = paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]
        assert response_schema["type"] == "array"
        assert response_schema["items"]["$ref"] == item_ref


def test_project_core_routes_publish_response_models(lightweight_app):
    schema = lightweight_app.openapi()
    paths = schema["paths"]

    expected_refs = {
        ("/api/projects/", "post"): "#/components/schemas/ProjectMutationResponse",
        ("/api/projects/{project_id}", "get"): "#/components/schemas/ProjectDetailResponse",
        ("/api/projects/{project_id}", "put"): "#/components/schemas/ProjectMutationResponse",
        ("/api/projects/{project_id}", "delete"): "#/components/schemas/ProjectMutationResponse",
        ("/api/projects/{project_id}/archive", "post"): "#/components/schemas/ProjectMutationResponse",
        ("/api/projects/{project_id}/favorite", "post"): "#/components/schemas/ProjectFavoriteResponse",
        ("/api/projects/stats/summary", "get"): "#/components/schemas/ProjectStatsResponse",
    }

    for (path, method), schema_ref in expected_refs.items():
        assert (
            paths[path][method]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
            == schema_ref
        )

    response_schema = paths["/api/projects/"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert response_schema["type"] == "array"
    assert response_schema["items"]["$ref"] == "#/components/schemas/ProjectListItemResponse"


def test_legacy_duplicate_endpoint_names_are_not_exported():
    legacy_exports = {
        case_structure: [
            "create_thread",
            "list_threads",
            "create_party",
            "list_parties",
            "create_counter_claim",
            "list_counter_claims",
        ],
        reminder: [
            "list_reminders",
            "create_reminder",
            "get_reminder_stats",
            "get_reminder",
            "update_reminder",
            "delete_reminder",
        ],
        dashboard: [
            "get_dashboard",
            "get_statistics",
            "get_urgent_items",
            "get_upcoming_tasks",
        ],
        report_api: [
            "_legacy_export_report",
        ],
    }

    for module, names in legacy_exports.items():
        for name in names:
            assert not hasattr(module, name)


def test_register_routes_imports_routers_in_declared_order(monkeypatch):
    imported_modules = []
    included_routers = []

    class FakeApp:
        def include_router(self, router):
            included_routers.append(router)

    def fake_import_module(module_name):
        imported_modules.append(module_name)
        if module_name == "app.models":
            return types.SimpleNamespace()
        return types.SimpleNamespace(
            router=f"{module_name}:router",
            router_en=f"{module_name}:router_en",
        )

    monkeypatch.setattr(route_module.importlib, "import_module", fake_import_module)

    register_routes(FakeApp())

    assert included_routers == [
        f"{spec.module_name}:{spec.router_name}" for spec in ROUTER_SPECS
    ]
    for module_name in TASK_HANDLER_MODULES:
        assert module_name not in imported_modules
    assert imported_modules[-1] == "app.models"


def test_router_specs_keep_system_routes_first_and_auth_last():
    assert ROUTER_SPECS[0].module_name == "app.api.system"
    assert ROUTER_SPECS[-3].module_name == "app.api.config_api"
    assert ROUTER_SPECS[-2].module_name == "app.api.tenant_api"
    assert ROUTER_SPECS[-1].module_name == "app.api.auth"
