"""
Scanner Engine: High-performance concurrent scanner orchestrator and aggregator.
"""

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Callable
from cleanguard.core.scanner.base import BaseScanner, CancellationToken
from cleanguard.core.scanner.temp_scanner import TempScanner
from cleanguard.core.scanner.cache_scanner import CacheScanner
from cleanguard.core.scanner.thumbnail_scanner import ThumbnailScanner
from cleanguard.core.scanner.log_scanner import LogScanner
from cleanguard.core.scanner.dump_scanner import CrashDumpScanner
from cleanguard.core.scanner.browser_scanner import BrowserScanner
from cleanguard.core.scanner.recycle_scanner import RecycleBinScanner
from cleanguard.core.contracts import ScanItem, ScanSummary, RiskLevel
from cleanguard.core.safety import SafetyEngine
from cleanguard.utils.filesystem import normalize_path
from cleanguard.utils.logging import get_logger

logger = get_logger("scanner_engine")


class ScannerEngine:
    """Orchestrates registered domain scanners with bounded thread parallelism."""

    def __init__(
        self,
        safety_engine: Optional[SafetyEngine] = None,
        max_threads: int = 4,
    ):
        self.safety_engine = safety_engine or SafetyEngine()
        self.max_threads = max_threads
        self.scanners: List[BaseScanner] = [
            TempScanner(self.safety_engine),
            CacheScanner(self.safety_engine),
            ThumbnailScanner(self.safety_engine),
            LogScanner(self.safety_engine),
            CrashDumpScanner(self.safety_engine),
            BrowserScanner(self.safety_engine),
            RecycleBinScanner(self.safety_engine),
        ]

    def register_scanner(self, scanner: BaseScanner) -> None:
        """Add custom or additional scanner."""
        self.scanners.append(scanner)

    def scan_all(
        self,
        cancel_token: Optional[CancellationToken] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> ScanSummary:
        """
        Execute concurrent scanning across all enabled scanners.
        Args:
            cancel_token: CancellationToken
            progress_callback: callback(status_msg, files_count, bytes_found)
        Returns:
            ScanSummary with aggregated metrics.
        """
        token = cancel_token or CancellationToken()
        scan_id = str(uuid.uuid4())
        start_time = time.time()

        all_items: Dict[str, ScanItem] = {}  # Deduplication by canonical path
        total_files = 0
        total_bytes = 0
        items_by_cat: Dict[str, int] = {}
        bytes_by_cat: Dict[str, int] = {}

        def sub_progress(count: int, cur_path: str, cur_bytes: int):
            if progress_callback:
                progress_callback(f"Scanning {cur_path}", total_files + count, total_bytes + cur_bytes)

        logger.info(f"Starting Scan session {scan_id} with {len(self.scanners)} scanners.")

        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(scanner.scan, token, sub_progress): scanner
                for scanner in self.scanners
            }

            for future in as_completed(futures):
                scanner = futures[future]
                try:
                    results = future.result()
                    for item in results:
                        norm = normalize_path(item.path)
                        if norm not in all_items:
                            all_items[norm] = item
                            total_files += 1
                            total_bytes += item.size

                            cat = item.category
                            items_by_cat[cat] = items_by_cat.get(cat, 0) + 1
                            bytes_by_cat[cat] = bytes_by_cat.get(cat, 0) + item.size
                except Exception as exc:
                    logger.error(f"Scanner {scanner.scanner_id} encountered exception: {exc}")

        safe_count = sum(1 for it in all_items.values() if it.risk_level == RiskLevel.SAFE)
        review_count = sum(1 for it in all_items.values() if it.risk_level == RiskLevel.REVIEW)
        blocked_count = sum(1 for it in all_items.values() if it.risk_level == RiskLevel.BLOCKED)

        summary = ScanSummary(
            scan_id=scan_id,
            started_at=start_time,
            finished_at=time.time(),
            drive_count=1,
            files_scanned=total_files,
            items_found=len(all_items),
            safe_items=safe_count,
            review_items=review_count,
            blocked_items=blocked_count,
            bytes_reclaimable=total_bytes,
            items_by_category=items_by_cat,
            bytes_by_category=bytes_by_cat,
        )

        logger.info(
            f"Scan session {scan_id} completed in {summary.finished_at - start_time:.2f}s. "
            f"Found {summary.items_found} items ({summary.bytes_reclaimable} bytes)."
        )
        return summary, list(all_items.values())
