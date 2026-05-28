"""Tenant column backfill helpers shared by dev startup and migrations."""

from __future__ import annotations

from sqlalchemy import inspect, text


PARENT_TENANT_BACKFILLS: dict[str, tuple[str, str, str]] = {
    "projects": ("user_id", "users", "id"),
    "report_sections": ("outline_id", "report_outlines", "id"),
    "section_references": ("outline_id", "report_outlines", "id"),
    "appeal_deadlines": ("appeal_record_id", "appeal_records", "id"),
    "appeal_arguments": ("appeal_record_id", "appeal_records", "id"),
    "appeal_documents": ("appeal_record_id", "appeal_records", "id"),
    "second_trial_strategies": ("appeal_record_id", "appeal_records", "id"),
    "hearing_statements": ("record_id", "hearing_records", "id"),
    "evidence_uses": ("record_id", "hearing_records", "id"),
    "hearing_warnings": ("record_id", "hearing_records", "id"),
    "adversarial_evidence_items": ("analysis_id", "adversarial_analyses", "id"),
    "action_plans": ("analysis_id", "adversarial_analyses", "id"),
    "conversation_messages": ("session_id", "conversation_sessions", "id"),
    "clarification_records": ("session_id", "conversation_sessions", "id"),
    "question_analyses": ("session_id", "conversation_sessions", "id"),
    "evidence_analysis_messages": (
        "session_id",
        "evidence_analysis_sessions",
        "id",
    ),
    "project_documents": ("project_id", "projects", "id"),
    "project_milestones": ("project_id", "projects", "id"),
    "project_communications": ("project_id", "projects", "id"),
    "project_evidence": ("project_id", "projects", "id"),
    "project_legal_advices": ("project_id", "projects", "id"),
    "project_events": ("project_id", "projects", "id"),
    "project_contracts": ("project_id", "projects", "id"),
    "project_risks": ("project_id", "projects", "id"),
    "project_case_mappings": ("project_id", "projects", "id"),
    "meeting_records": ("project_id", "projects", "id"),
}


def _column_map(inspector, table_names: set[str]) -> dict[str, set[str]]:
    return {
        table_name: {
            column["name"] for column in inspector.get_columns(table_name)
        }
        for table_name in table_names
    }


def _update_from_parent(
    connection,
    preparer,
    table_name: str,
    parent_column: str,
    parent_table: str,
    parent_pk: str,
) -> int:
    quoted_table = preparer.quote(table_name)
    quoted_tenant = preparer.quote("tenant_id")
    quoted_parent_column = preparer.quote(parent_column)
    quoted_parent_table = preparer.quote(parent_table)
    quoted_parent_pk = preparer.quote(parent_pk)

    result = connection.execute(
        text(
            f"""
            UPDATE {quoted_table}
            SET {quoted_tenant} = (
                SELECT {quoted_parent_table}.{quoted_tenant}
                FROM {quoted_parent_table}
                WHERE {quoted_parent_table}.{quoted_parent_pk} = {quoted_parent_column}
            )
            WHERE ({quoted_tenant} IS NULL OR {quoted_tenant} = '')
              AND {quoted_parent_column} IS NOT NULL
              AND EXISTS (
                  SELECT 1
                  FROM {quoted_parent_table}
                  WHERE {quoted_parent_table}.{quoted_parent_pk} = {quoted_parent_column}
                    AND {quoted_parent_table}.{quoted_tenant} IS NOT NULL
                    AND {quoted_parent_table}.{quoted_tenant} <> ''
              )
            """
        )
    )
    return max(result.rowcount or 0, 0)


def _fallback_update(
    connection,
    preparer,
    table_name: str,
    fallback_tenant_id: str,
) -> int:
    quoted_table = preparer.quote(table_name)
    quoted_tenant = preparer.quote("tenant_id")
    result = connection.execute(
        text(
            f"UPDATE {quoted_table} SET {quoted_tenant} = :tenant_id "
            f"WHERE {quoted_tenant} IS NULL OR {quoted_tenant} = ''"
        ),
        {"tenant_id": fallback_tenant_id},
    )
    return max(result.rowcount or 0, 0)


def backfill_tenant_columns(
    connection,
    metadata,
    fallback_tenant_id: str,
    skip_tables: set[str] | None = None,
) -> list[str]:
    """Backfill nullable tenant_id columns, preferring case or parent lineage."""

    skip_tables = skip_tables or set()
    inspector = inspect(connection)
    existing_tables = set(inspector.get_table_names())
    columns_by_table = _column_map(inspector, existing_tables)
    preparer = connection.engine.dialect.identifier_preparer
    updated: list[str] = []

    for table in metadata.sorted_tables:
        table_name = table.name
        columns = columns_by_table.get(table_name, set())
        if (
            table_name not in existing_tables
            or table_name in skip_tables
            or "tenant_id" not in table.columns
            or "tenant_id" not in columns
        ):
            continue

        row_count = 0
        if (
            "case_id" in columns
            and "cases" in existing_tables
            and "tenant_id" in columns_by_table.get("cases", set())
        ):
            row_count += _update_from_parent(
                connection,
                preparer,
                table_name,
                "case_id",
                "cases",
                "id",
            )

        parent_rule = PARENT_TENANT_BACKFILLS.get(table_name)
        if parent_rule:
            parent_column, parent_table, parent_pk = parent_rule
            parent_columns = columns_by_table.get(parent_table, set())
            if (
                parent_column in columns
                and parent_table in existing_tables
                and parent_pk in parent_columns
                and "tenant_id" in parent_columns
            ):
                row_count += _update_from_parent(
                    connection,
                    preparer,
                    table_name,
                    parent_column,
                    parent_table,
                    parent_pk,
                )

        row_count += _fallback_update(
            connection,
            preparer,
            table_name,
            fallback_tenant_id,
        )
        if row_count:
            updated.append(f"{table_name}:{row_count}")

    return updated
