"""Folder watcher startup and shutdown lifecycle helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from app.monitoring.readiness import check_schema_tables

logger = logging.getLogger(__name__)


def _incremental_scan_callback(case_id: int, file_paths: list[str]) -> None:
    from app.services.evidence_folder_service import EvidenceFolderService

    service = EvidenceFolderService(case_id)
    try:
        service.incremental_scan(file_paths)
        logger.info("[FolderWatcher] Incremental scan completed: case_id=%s", case_id)
    except Exception as exc:
        logger.error(
            "[FolderWatcher] Incremental scan failed: case_id=%s, error=%s",
            case_id,
            exc,
        )
    finally:
        service.close()


def resume_folder_watchers() -> None:
    """Restore enabled evidence-folder watchers after application startup."""
    from app.db.database import SessionLocal
    from app.models.case import Case
    from app.services.folder_watcher import FolderWatcherService

    schema_check = check_schema_tables()
    if schema_check.get("status") != "ok":
        logger.info("Skipping folder watcher restore until database schema is ready.")
        return

    db = SessionLocal()
    try:
        enabled_cases = (
            db.query(Case)
            .filter(
                Case.evidence_folder_enabled == True,
                Case.evidence_folder_path.isnot(None),
            )
            .all()
        )

        for case in enabled_cases:
            folder_path = case.evidence_folder_path
            if not folder_path:
                continue

            if not Path(folder_path).exists():
                logger.warning(
                    "[FolderWatcher] Configured path does not exist: case_id=%s, path=%s",
                    case.id,
                    folder_path,
                )
                continue

            watcher = FolderWatcherService.get_instance(case.id)
            success = watcher.start_watching(
                folder_path=folder_path,
                callback=_incremental_scan_callback,
            )
            if success:
                logger.info(
                    "[FolderWatcher] Restored watcher: case_id=%s, path=%s",
                    case.id,
                    folder_path,
                )
            else:
                logger.warning(
                    "[FolderWatcher] Failed to restore watcher: case_id=%s",
                    case.id,
                )
    except Exception as exc:
        logger.error("[FolderWatcher] Failed to restore watchers: %s", exc)
    finally:
        db.close()


def stop_folder_watchers() -> None:
    from app.services.folder_watcher import FolderWatcherService

    FolderWatcherService.stop_all()
