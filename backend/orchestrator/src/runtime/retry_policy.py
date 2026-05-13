"""Deterministic retry rules for O5A.

O5A constraints:
- single-threaded
- retries are deterministic and represented by RUNNING -> PENDING transition
- re-enqueue must be deterministic (append to FIFO)

Policy here is intentionally simple and fully deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple, Type


@dataclass(frozen=True)
class RetryPolicy:
    """Deterministic retry policy.

    Parameters:
      - max_attempts: total attempts including the first.
      - retry_on: optional tuple of exception types that are retryable.
                 If None, all exceptions are retryable.
    """

    max_attempts: int = 3
    retry_on: Optional[Tuple[Type[BaseException], ...]] = None

    def should_retry(self, *, attempt: int, exc: BaseException) -> bool:
        if attempt >= self.max_attempts:
            return False
        if self.retry_on is None:
            return True
        return isinstance(exc, self.retry_on)
