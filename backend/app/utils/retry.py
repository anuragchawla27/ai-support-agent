"""
Retry logic (Day 13). A small decorator for wrapping calls to external
APIs (Groq, in practice) that can fail transiently -- network blips,
momentary rate limits, connection resets. Retries once after a short
delay before giving up, which is enough to smooth over the exact kind
of "Connection error" we hit during Day 9-10 testing without masking a
genuinely broken call (it still raises after the final attempt, so
callers' existing safe-fallback handling still applies).
"""

import functools
import logging
import time

logger = logging.getLogger("app")


def retry(max_attempts: int = 2, delay_seconds: float = 1.0):
    """
    Retries the wrapped function up to max_attempts times, with a short
    delay between attempts. Re-raises the last exception if every
    attempt fails -- callers are expected to have their own fallback
    (see app.services.intent / app.services.response) for that case.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"[retry] {func.__name__} failed (attempt {attempt}/{max_attempts}): {e} -- retrying"
                        )
                        time.sleep(delay_seconds)
                    else:
                        logger.error(
                            f"[retry] {func.__name__} failed after {max_attempts} attempts: {e}"
                        )
            raise last_exception
        return wrapper
    return decorator
