from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor
from typing import Callable, TypeVar

T = TypeVar("T")


class WorkerPool:
    """
    ThreadPool wrapper.
    Normativa: max_workers=1 deve essere behavior-identico a O5A (seriale).
    """

    def __init__(self, max_workers: int) -> None:
        if max_workers < 1:
            raise ValueError("max_workers must be >= 1")
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    def submit(self, fn: Callable[[], T]) -> Future[T]:
        return self._executor.submit(fn)

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)
