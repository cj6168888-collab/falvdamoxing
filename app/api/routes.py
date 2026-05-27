"""Central API route registration."""

from __future__ import annotations

from dataclasses import dataclass
import importlib
import logging

from fastapi import FastAPI

HTTP_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD", "TRACE"})


@dataclass(frozen=True)
class RouterSpec:
    module_name: str
    router_name: str = "router"


ROUTER_SPECS = (
    RouterSpec("app.api.system"),
    RouterSpec("app.api.case"),
    RouterSpec("app.api.document"),
    RouterSpec("app.api.case_structure"),
    RouterSpec("app.api.claims"),
    RouterSpec("app.api.adversarial"),
    RouterSpec("app.api.adversarial", "router_en"),
    RouterSpec("app.api.time_control"),
    RouterSpec("app.api.time_control", "router_en"),
    RouterSpec("app.api.hearing"),
    RouterSpec("app.api.project"),
    RouterSpec("app.api.meeting"),
    RouterSpec("app.api.evidence"),
    RouterSpec("app.api.insight_api"),
    RouterSpec("app.api.evidence_guide_api"),
    RouterSpec("app.api.profile_api"),
    RouterSpec("app.api.assistant_api"),
    RouterSpec("app.api.evidence_graph_api"),
    RouterSpec("app.api.evidence_qa_api"),
    RouterSpec("app.api.report_api"),
    RouterSpec("app.api.conversation_api"),
    RouterSpec("app.api.senior_analysis_api"),
    RouterSpec("app.api.export_api"),
    RouterSpec("app.api.company_info_api"),
    RouterSpec("app.api.document_management"),
    RouterSpec("app.api.loan_api"),
    RouterSpec("app.api.contract_api"),
    RouterSpec("app.api.evidence_folder"),
    RouterSpec("app.api.reminder"),
    RouterSpec("app.api.tracking_api"),
    RouterSpec("app.api.ai_tasks"),
    RouterSpec("app.api.appeal"),
    RouterSpec("app.api.execution"),
    RouterSpec("app.api.dashboard"),
    RouterSpec("app.api.finance"),
    RouterSpec("app.api.legal_knowledge_api"),
    RouterSpec("app.api.llm_router_api"),
    RouterSpec("app.services.third_party_api"),
    RouterSpec("app.api.streaming_analysis"),
    RouterSpec("app.api.smart_chat"),
    RouterSpec("app.api.config_api"),
    RouterSpec("app.api.tenant_api"),
    RouterSpec("app.api.auth"),
)


def _route_signatures(route) -> frozenset[tuple[str, str]]:
    methods = getattr(route, "methods", None)
    path = getattr(route, "path", None)
    if not methods or not path:
        return frozenset()
    return frozenset((method, path) for method in methods if method in HTTP_METHODS)


def _reject_duplicate_routes(
    app: FastAPI,
    *,
    existing_signatures: set[tuple[str, str]],
    first_added_route_index: int,
    spec: RouterSpec,
    logger: logging.Logger | None,
) -> None:
    router = getattr(app, "router", None)
    routes = getattr(router, "routes", None)
    if routes is None:
        return

    seen_signatures = set(existing_signatures)
    duplicate_routes: list[str] = []

    for route in routes[first_added_route_index:]:
        signatures = _route_signatures(route)
        duplicate_signatures = signatures & seen_signatures
        if duplicate_signatures:
            endpoint = getattr(route, "endpoint", None)
            endpoint_name = getattr(endpoint, "__name__", "<unknown>")
            duplicate_routes.append(
                f"{spec.module_name}.{spec.router_name}:{endpoint_name} "
                f"{sorted(duplicate_signatures)}"
            )
            continue

        seen_signatures.update(signatures)

    if duplicate_routes:
        if logger is not None:
            logger.error("Duplicate route registration blocked: %s", duplicate_routes)
        raise RuntimeError(
            "Duplicate route registration blocked: " + "; ".join(duplicate_routes)
        )


def _include_router(app: FastAPI, spec: RouterSpec, logger: logging.Logger | None) -> None:
    module = importlib.import_module(spec.module_name)
    router = getattr(module, spec.router_name)
    app_router = getattr(app, "router", None)
    app_routes = getattr(app_router, "routes", [])
    existing_signatures = {
        signature
        for route in app_routes
        for signature in _route_signatures(route)
    }
    first_added_route_index = len(app_routes)

    if spec.module_name == "app.api.smart_chat" and logger is not None:
        logger.debug("[MAIN] smart_chat routes: %s", router.routes)

    app.include_router(router)
    _reject_duplicate_routes(
        app,
        existing_signatures=existing_signatures,
        first_added_route_index=first_added_route_index,
        spec=spec,
        logger=logger,
    )

    if spec.module_name == "app.api.smart_chat" and logger is not None:
        logger.debug("[MAIN] smart_chat loaded OK")


def register_routes(app: FastAPI, logger: logging.Logger | None = None) -> None:
    for spec in ROUTER_SPECS:
        _include_router(app, spec, logger)

    importlib.import_module("app.models")
