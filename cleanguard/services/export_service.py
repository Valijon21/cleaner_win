"""
Export Service: Exports historical cleanup session reports to CSV and JSON formats.
Implements Master Plan T180 requirements.
"""

import os
import csv
import json
from typing import List, Dict, Any, Optional, Callable
from cleanguard.utils.formatting import format_bytes, format_timestamp
from cleanguard.utils.logging import get_logger

logger = get_logger("export_service")


def export_history_to_csv(file_path: str, history: List[Dict[str, Any]]) -> bool:
    """
    Export cleanup session records to a standard CSV file.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Session ID",
                "Date & Time",
                "Status",
                "Files Deleted",
                "Files Skipped",
                "Files Failed",
                "Bytes Recovered",
                "Human Readable Size",
            ])
            for entry in history:
                writer.writerow([
                    entry.get("id", ""),
                    format_timestamp(entry.get("started_at", 0.0)),
                    entry.get("status", ""),
                    entry.get("files_deleted", 0),
                    entry.get("files_skipped", 0),
                    entry.get("files_failed", 0),
                    entry.get("bytes_recovered", 0),
                    format_bytes(entry.get("bytes_recovered", 0)),
                ])
        logger.info(f"Successfully exported {len(history)} sessions to CSV: {file_path}")
        return True
    except Exception as exc:
        logger.error(f"Failed to export history to CSV '{file_path}': {exc}")
        return False


def export_history_to_json(
    file_path: str,
    history: List[Dict[str, Any]],
    items_provider: Optional[Callable[[str], List[Dict[str, Any]]]] = None,
) -> bool:
    """
    Export cleanup session records and optional itemized file lists to a JSON file.
    """
    try:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        export_data = []

        for entry in history:
            session_id = entry.get("id", "")
            session_dict = {
                "session_id": session_id,
                "started_at": entry.get("started_at", 0.0),
                "started_at_formatted": format_timestamp(entry.get("started_at", 0.0)),
                "finished_at": entry.get("finished_at", 0.0),
                "status": entry.get("status", ""),
                "files_deleted": entry.get("files_deleted", 0),
                "files_skipped": entry.get("files_skipped", 0),
                "files_failed": entry.get("files_failed", 0),
                "bytes_recovered": entry.get("bytes_recovered", 0),
                "bytes_recovered_formatted": format_bytes(entry.get("bytes_recovered", 0)),
            }

            if items_provider and session_id:
                try:
                    items = items_provider(session_id)
                    session_dict["items"] = items
                except Exception as exc:
                    logger.warning(f"Could not fetch items for session {session_id}: {exc}")
                    session_dict["items"] = []

            export_data.append(session_dict)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully exported {len(history)} sessions to JSON: {file_path}")
        return True
    except Exception as exc:
        logger.error(f"Failed to export history to JSON '{file_path}': {exc}")
        return False


def export_diagnostic_package(output_zip_path: str) -> bool:
    """
    Package active log files, recent crash dumps, and system specifications
    into a consolidated zip archive for troubleshooting and issue reporting.
    """
    import zipfile
    import sys
    import time
    from cleanguard.utils.logging import get_default_log_dir
    from cleanguard.app.version import get_version_string
    from cleanguard.windows.os_info import get_windows_version
    from cleanguard.windows.privileges import is_user_admin

    try:
        os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
        log_dir = get_default_log_dir()
        os_info = get_windows_version()

        sys_info = {
            "application": get_version_string(),
            "export_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "os_name": os_info.display_name,
            "os_build": os_info.build,
            "architecture": os_info.architecture,
            "admin_elevated": is_user_admin(),
            "python_version": sys.version,
            "python_executable": sys.executable,
        }

        with zipfile.ZipFile(output_zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 1. System specs report
            zf.writestr("system_diagnostics.json", json.dumps(sys_info, indent=2))

            # 2. Add log files
            if os.path.exists(log_dir):
                for fname in os.listdir(log_dir):
                    if fname.endswith(".log") or fname.startswith("crash_"):
                        full_path = os.path.join(log_dir, fname)
                        if os.path.isfile(full_path):
                            try:
                                zf.write(full_path, arcname=f"logs/{fname}")
                            except Exception as file_err:
                                logger.warning(f"Could not include {fname} in diagnostic zip: {file_err}")

        logger.info(f"Diagnostic report package created successfully: {output_zip_path}")
        return True
    except Exception as exc:
        logger.error(f"Failed to create diagnostic report package '{output_zip_path}': {exc}", exc_info=True)
        return False

