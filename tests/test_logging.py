"""
Unit Tests for CleanGuard Logging & Diagnostic System.
"""

import os
import time
import logging
import threading
import tempfile
import pytest
from cleanguard.utils.logging import (
    setup_logging,
    get_logger,
    get_memory_logs,
    clear_memory_logs,
    set_log_level,
    shutdown_logging,
    log_step,
    MemoryLogHandler,
)
from cleanguard.utils.crash_handler import write_crash_report


def test_memory_log_handler():
    handler = MemoryLogHandler(capacity=5)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("test_mem")
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(handler)

    for i in range(10):
        logger.info(f"Message {i}")

    entries = handler.get_entries()
    assert len(entries) == 5
    assert entries[-1]["message"] == "Message 9"


    handler.clear()
    assert len(handler.get_entries()) == 0


def test_logging_setup_and_dual_sinks(tmp_path):
    log_dir = str(tmp_path)
    setup_logging(
        log_level=logging.INFO,
        log_to_file=True,
        log_to_console=False,
        log_dir=log_dir,
    )


    logger = get_logger("test_dual")
    logger.info("Normal information message")
    logger.warning("Warning event occurred")
    logger.error("Error event occurred")

    # Allow queue listener thread to flush and close file handles
    time.sleep(0.3)
    shutdown_logging()

    general_log = os.path.join(log_dir, "cleanguard.log")
    error_log = os.path.join(log_dir, "cleanguard_errors.log")

    assert os.path.exists(general_log)
    assert os.path.exists(error_log)

    with open(general_log, "r", encoding="utf-8") as f:
        gen_content = f.read()
        assert "Normal information message" in gen_content
        assert "Warning event occurred" in gen_content
        assert "Error event occurred" in gen_content

    with open(error_log, "r", encoding="utf-8") as f:
        err_content = f.read()
        # INFO must NOT be in error log!
        assert "Normal information message" not in err_content
        assert "Warning event occurred" in err_content
        assert "Error event occurred" in err_content


def test_log_step_context_manager():
    setup_logging(log_level=logging.DEBUG, log_to_file=False, log_to_console=False)
    logger = get_logger("test_step")
    clear_memory_logs()

    with log_step("Unit Test Step", logger=logger, test_key="sample_val"):
        time.sleep(0.01)

    time.sleep(0.2)
    entries = get_memory_logs()
    messages = [e["message"] for e in entries]

    assert any("[STEP START] Unit Test Step" in m for m in messages)
    assert any("[STEP COMPLETE] Unit Test Step" in m for m in messages)
    shutdown_logging()


def test_log_step_captures_failure():
    setup_logging(log_level=logging.DEBUG, log_to_file=False, log_to_console=False)
    logger = get_logger("test_fail_step")

    with pytest.raises(ValueError):
        with log_step("Failing Step", logger=logger):
            raise ValueError("Intentional calculation error")

    time.sleep(0.2)
    entries = get_memory_logs()
    messages = [e["message"] for e in entries]
    assert any("[STEP FAILED] Failing Step" in m for m in messages)
    shutdown_logging()


def test_concurrent_multithread_logging(tmp_path):
    log_dir = str(tmp_path)
    setup_logging(log_level=logging.DEBUG, log_to_file=True, log_to_console=False, log_dir=log_dir)
    logger = get_logger("test_thread")

    def worker(thread_idx: int):
        for i in range(20):
            logger.info(f"Worker {thread_idx} log entry {i}")

    threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    time.sleep(0.5)
    shutdown_logging()

    general_log = os.path.join(log_dir, "cleanguard.log")
    assert os.path.exists(general_log)
    with open(general_log, "r", encoding="utf-8") as f:
        content = f.read()
        # 5 threads * 20 = 100 lines
        assert content.count("Worker") == 100


def test_write_crash_report(tmp_path):
    try:
        raise RuntimeError("Test crash simulation")
    except RuntimeError as exc:
        crash_path = write_crash_report(type(exc), exc, exc.__traceback__, target_dir=str(tmp_path))

        assert os.path.exists(crash_path)
        with open(crash_path, "r", encoding="utf-8") as f:
            report = f.read()
            assert "CLEANGUARD CRASH REPORT" in report
            assert "RuntimeError: Test crash simulation" in report
            assert "TRACEBACK:" in report


