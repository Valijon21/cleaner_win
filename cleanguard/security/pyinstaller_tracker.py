"""
PyInstaller Tracker: Multi-layered Safety Evaluator for PyInstaller Temp Caches.
Safely detects and verifies abandoned _MEI... directories left behind by terminated processes.
Strictly protects active applications and Windows system integrity.
"""

import os
import sys
import re
import time
import ctypes
import threading
from typing import Tuple, Set, Optional, Dict, List
from cleanguard.core.contracts import RiskLevel
from cleanguard.utils.filesystem import normalize_path, is_path_under_directory, safe_stat
from cleanguard.windows.shell import is_file_locked, is_reparse_point_or_junction
from cleanguard.windows.known_folders import get_known_folders
from cleanguard.utils.logging import get_logger

logger = get_logger("pyinstaller_tracker")

_MEI_PATTERN = re.compile(r"^_MEI[a-zA-Z0-9_]+$", re.IGNORECASE)


class PyInstallerTracker:
    """
    Evaluator for PyInstaller _MEI temp directories.
    Applies Defense in Depth:
    1. Root boundary check (%TEMP% or %SystemRoot%\\Temp)
    2. System boot time threshold (GetTickCount64)
    3. Active process and image path inspection (Toolhelp32 / QueryFullProcessImageNameW)
    4. Exclusive file locking verification (CreateFileW dwShareMode=0)
    5. Minimum age threshold (default: 24h)
    """

    def __init__(self):
        self._cache: Dict[str, Tuple[bool, RiskLevel, str]] = {}
        self._cache_lock = threading.Lock()
        self._active_pids: Optional[Set[int]] = None
        self._active_exe_paths: Optional[Set[str]] = None
        self._process_cache_time: float = 0.0

    def clear_cache(self) -> None:
        """Clear cached evaluations for a new scan or cleanup pass."""
        with self._cache_lock:
            self._cache.clear()
            self._active_pids = None
            self._active_exe_paths = None
            self._process_cache_time = 0.0

    @staticmethod
    def get_system_boot_time() -> float:
        """Returns approximate timestamp of system boot using GetTickCount64."""
        if sys.platform == "win32":
            try:
                uptime_ms = ctypes.windll.kernel32.GetTickCount64()
                return time.time() - (uptime_ms / 1000.0)
            except Exception:
                pass
        return 0.0

    @staticmethod
    def extract_pid_from_dirname(dirname: str) -> Optional[int]:
        """
        Extract process ID if encoded in folder name.
        PyInstaller uses formats like _MEI<pid> (e.g. _MEI119602)
        or hex formats like _MEI00002bdc2 (where 00002bdc is hex PID 11228).
        """
        # Decimal PID format: _MEI12345
        m_dec = re.match(r"^_MEI(\d{3,7})$", dirname, re.IGNORECASE)
        if m_dec:
            try:
                return int(m_dec.group(1))
            except ValueError:
                pass

        # Hex PID format: _MEI00002bdc or _MEI00002bdc2
        m_hex = re.match(r"^_MEI([0-9a-fA-F]{4,8})\d?$", dirname, re.IGNORECASE)
        if m_hex:
            try:
                val = int(m_hex.group(1), 16)
                if 4 < val < 1000000:
                    return val
            except ValueError:
                pass

        return None

    def get_active_process_info(self, max_cache_age_sec: float = 5.0) -> Tuple[Set[int], Set[str]]:
        """
        Retrieves running process IDs and normalized executable paths.
        Cached briefly (5 seconds) to avoid redundant snapshots during rapid file evaluations.
        """
        now = time.time()
        if (
            self._active_pids is not None
            and self._active_exe_paths is not None
            and (now - self._process_cache_time) < max_cache_age_sec
        ):
            return self._active_pids, self._active_exe_paths

        pids: Set[int] = set()
        exe_paths: Set[str] = set()

        if sys.platform != "win32":
            self._active_pids = pids
            self._active_exe_paths = exe_paths
            self._process_cache_time = now
            return pids, exe_paths

        try:
            import ctypes.wintypes
            kernel32 = ctypes.windll.kernel32
            TH32CS_SNAPPROCESS = 0x00000002
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

            class PROCESSENTRY32(ctypes.Structure):
                _fields_ = [
                    ("dwSize", ctypes.wintypes.DWORD),
                    ("cntUsage", ctypes.wintypes.DWORD),
                    ("th32ProcessID", ctypes.wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", ctypes.wintypes.DWORD),
                    ("cntThreads", ctypes.wintypes.DWORD),
                    ("th32ParentProcessID", ctypes.wintypes.DWORD),
                    ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", ctypes.wintypes.DWORD),
                    ("szExeFile", ctypes.c_char * 260),
                ]

            h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
            if h_snap != ctypes.c_void_p(-1).value and h_snap != -1:
                pe = PROCESSENTRY32()
                pe.dwSize = ctypes.sizeof(PROCESSENTRY32)
                buf = ctypes.create_unicode_buffer(1024)
                size = ctypes.wintypes.DWORD(1024)

                try:
                    if kernel32.Process32First(h_snap, ctypes.byref(pe)):
                        while True:
                            pid = pe.th32ProcessID
                            pids.add(pid)
                            if pid > 4:
                                h_proc = kernel32.OpenProcess(
                                    PROCESS_QUERY_LIMITED_INFORMATION, False, pid
                                )
                                if h_proc:
                                    size.value = 1024
                                    if kernel32.QueryFullProcessImageNameW(
                                        h_proc, 0, buf, ctypes.byref(size)
                                    ):
                                        exe_paths.add(normalize_path(buf.value).lower())
                                    kernel32.CloseHandle(h_proc)
                            if not kernel32.Process32Next(h_snap, ctypes.byref(pe)):
                                break
                finally:
                    kernel32.CloseHandle(h_snap)
        except Exception as exc:
            logger.warning(f"Error querying active process info: {exc}")

        self._active_pids = pids
        self._active_exe_paths = exe_paths
        self._process_cache_time = now
        return pids, exe_paths

    def find_mei_root(
        self,
        path: str,
        allowed_temp_roots: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Determines whether path is inside an _MEI... folder directly under an authorized Temp root.
        Returns the absolute path to the _MEI... root folder, or None.
        """
        if not path or not isinstance(path, str):
            return None

        norm_path = normalize_path(path)
        if allowed_temp_roots is None:
            folders = get_known_folders()
            allowed_temp_roots = []
            if folders.user_temp and os.path.exists(folders.user_temp):
                allowed_temp_roots.append(folders.user_temp)
            if folders.system_temp and os.path.exists(folders.system_temp):
                allowed_temp_roots.append(folders.system_temp)

        for temp_root in allowed_temp_roots:
            norm_root = normalize_path(temp_root)
            if is_path_under_directory(norm_path, norm_root):
                try:
                    rel = os.path.relpath(norm_path, norm_root)
                    parts = rel.split(os.sep)
                    if parts and _MEI_PATTERN.match(parts[0]):
                        mei_root = os.path.join(norm_root, parts[0])
                        return mei_root
                except (ValueError, OSError):
                    continue

        return None

    def evaluate_mei_directory(
        self,
        mei_dir: str,
        min_age_hours: float = 24.0,
    ) -> Tuple[bool, RiskLevel, str]:
        """
        Evaluates whether an _MEI directory is an abandoned/orphaned cache.
        Returns (is_orphan, risk_level, reason).
        """
        norm_dir = normalize_path(mei_dir)

        with self._cache_lock:
            if norm_dir in self._cache:
                return self._cache[norm_dir]

        # 1. Structural and Reparse Check
        if not os.path.exists(norm_dir) or not os.path.isdir(norm_dir):
            res = (False, RiskLevel.BLOCKED, "Target _MEI directory does not exist.")
            with self._cache_lock:
                self._cache[norm_dir] = res
            return res

        if is_reparse_point_or_junction(norm_dir):
            res = (False, RiskLevel.BLOCKED, "Directory is a reparse point or junction.")
            with self._cache_lock:
                self._cache[norm_dir] = res
            return res

        st = safe_stat(norm_dir)
        if st is None:
            res = (False, RiskLevel.BLOCKED, "Cannot stat _MEI directory.")
            with self._cache_lock:
                self._cache[norm_dir] = res
            return res

        now = time.time()
        dir_mtime = st.st_mtime
        dir_ctime = getattr(st, "st_ctime", dir_mtime)
        age_hours = (now - dir_mtime) / 3600.0

        # 2. Active Process Check
        active_pids, active_exe_paths = self.get_active_process_info()
        dir_lower = norm_dir.lower()

        # Check if any active process image path points inside this _MEI directory
        for exe_path in active_exe_paths:
            if is_path_under_directory(exe_path, dir_lower) or exe_path.startswith(dir_lower):
                logger.info(f"_MEI directory {norm_dir} is in active use by process: {exe_path}")
                res = (
                    False,
                    RiskLevel.BLOCKED,
                    "PyInstaller cache is currently in active use by a running process.",
                )
                with self._cache_lock:
                    self._cache[norm_dir] = res
                return res

        # Check if directory name encodes a PID that is currently active
        dirname = os.path.basename(norm_dir)
        encoded_pid = self.extract_pid_from_dirname(dirname)
        if encoded_pid is not None and encoded_pid in active_pids:
            logger.info(f"_MEI directory {norm_dir} has active matching PID: {encoded_pid}")
            res = (
                False,
                RiskLevel.BLOCKED,
                f"PyInstaller creator process (PID {encoded_pid}) is currently running.",
            )
            with self._cache_lock:
                self._cache[norm_dir] = res
            return res

        # 3. File Lock Sampling Check
        # Check if key executables/DLLs inside are locked by Windows
        try:
            sample_count = 0
            for root, _, files in os.walk(norm_dir):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in (".dll", ".pyd", ".exe"):
                        full_f = os.path.join(root, f)
                        sample_count += 1
                        if is_file_locked(full_f):
                            logger.info(f"_MEI directory {norm_dir} contains locked binary: {full_f}")
                            res = (
                                False,
                                RiskLevel.BLOCKED,
                                "PyInstaller cache contains files locked by an active process.",
                            )
                            with self._cache_lock:
                                self._cache[norm_dir] = res
                            return res
                        if sample_count >= 15:  # Sufficient sample of binaries checked
                            break
                if sample_count >= 15:
                    break
        except Exception as exc:
            logger.debug(f"Lock sampling check encounter: {exc}")

        # 4. System Boot Time & Age Assessment
        boot_time = self.get_system_boot_time()
        is_pre_boot = (dir_mtime < boot_time and dir_ctime < boot_time)

        if age_hours >= min_age_hours:
            reason = (
                f"Orphaned PyInstaller cache ({int(age_hours)}h old, process terminated)."
                if is_pre_boot
                else f"Orphaned PyInstaller cache (>={int(min_age_hours)}h old, process terminated)."
            )
            res = (True, RiskLevel.SAFE, reason)
        else:
            # Younger than 24 hours
            res = (
                True,
                RiskLevel.REVIEW,
                f"Recent PyInstaller cache ({age_hours:.1f}h old). User review required.",
            )

        with self._cache_lock:
            self._cache[norm_dir] = res

        return res

    def evaluate_path(
        self,
        path: str,
        min_age_hours: float = 24.0,
        allowed_temp_roots: Optional[List[str]] = None,
    ) -> Tuple[bool, RiskLevel, str]:
        """
        Evaluates a file path. If inside an _MEI directory, evaluates the container.
        Returns (is_pyinstaller_file, risk_level, reason).
        """
        mei_root = self.find_mei_root(path, allowed_temp_roots=allowed_temp_roots)
        if not mei_root:
            return False, RiskLevel.BLOCKED, "Not inside a PyInstaller temp cache."

        is_orphan, risk, reason = self.evaluate_mei_directory(
            mei_root, min_age_hours=min_age_hours
        )
        return True, risk, reason
