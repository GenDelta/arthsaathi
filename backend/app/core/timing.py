"""Performance timing instrumentation."""

import contextlib
import logging
import time

logger = logging.getLogger("timing")

@contextlib.contextmanager
def timed(stage: str, **kw):
    """Context manager to measure and log execution time of a code block."""
    t0 = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        extras = " ".join(f"{k}={v}" for k, v in kw.items())
        logger.info("TIMING stage=%s elapsed_ms=%.1f %s", stage, elapsed_ms, extras)
