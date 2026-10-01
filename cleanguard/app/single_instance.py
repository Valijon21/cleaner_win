"""
Single-instance guard for CleanGuard.

Two instances cleaning the same folders at the same time race each other's
safety re-validation, so only one GUI (or headless Auto-Care run) may hold the
lock. A second GUI launch asks the running one to show its window and exits.
"""

import os
from typing import Optional
from PyQt5.QtCore import QLockFile, QObject, pyqtSignal
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from cleanguard.utils.logging import get_logger

logger = get_logger("single_instance")

SERVER_NAME = "CleanGuard.SingleInstance"
ACTIVATE_MESSAGE = b"activate"
# Covers a restart-as-administrator handover, where the previous instance is
# still shutting down while the elevated one starts.
HANDOVER_WAIT_MS = 8000


def _default_lock_path() -> str:
    """Lock lives next to config.json / cleanguard.db (per user)."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        base_dir = os.path.join(local_app_data, "CleanGuard")
    else:
        base_dir = os.path.join(os.path.expanduser("~"), ".cleanguard")
    try:
        os.makedirs(base_dir, exist_ok=True)
    except OSError:
        base_dir = "."
    return os.path.join(base_dir, "cleanguard.lock")


class SingleInstanceGuard(QObject):
    """Holds the instance lock and listens for activation requests."""

    activation_requested = pyqtSignal()

    def __init__(self, lock_path: Optional[str] = None, server_name: str = SERVER_NAME, parent=None):
        super().__init__(parent)
        self.lock_path = lock_path or _default_lock_path()
        self.server_name = server_name
        self._lock = QLockFile(self.lock_path)
        self._server: Optional[QLocalServer] = None

    def try_acquire(self, timeout_ms: int = 0) -> bool:
        """Take the lock, waiting up to timeout_ms for a previous holder to exit."""
        return bool(self._lock.tryLock(timeout_ms))

    def notify_running_instance(self, timeout_ms: int = 1000) -> bool:
        """Ask the instance holding the lock to bring its window forward."""
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        if not socket.waitForConnected(timeout_ms):
            return False
        socket.write(ACTIVATE_MESSAGE)
        socket.flush()
        socket.waitForBytesWritten(timeout_ms)
        socket.disconnectFromServer()
        return True

    def start_listening(self) -> None:
        """Accept activation requests from later launches (lock holder only)."""
        QLocalServer.removeServer(self.server_name)  # clear a stale pipe from a crash
        self._server = QLocalServer(self)
        if not self._server.listen(self.server_name):
            logger.warning(f"Single-instance server unavailable: {self._server.errorString()}")
            return
        self._server.newConnection.connect(self._on_new_connection)

    def _on_new_connection(self) -> None:
        while self._server is not None and self._server.hasPendingConnections():
            conn = self._server.nextPendingConnection()
            conn.readyRead.connect(lambda c=conn: self._on_ready_read(c))
            conn.disconnected.connect(conn.deleteLater)

    def _on_ready_read(self, conn: QLocalSocket) -> None:
        if bytes(conn.readAll()).startswith(ACTIVATE_MESSAGE):
            self.activation_requested.emit()

    def release(self) -> None:
        if self._server is not None:
            self._server.close()
            self._server = None
        if self._lock.isLocked():
            self._lock.unlock()
