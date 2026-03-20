import asyncio
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import logging
import inspect
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


DEFAULT_N_OF_WORKERS = multiprocessing.cpu_count() - 2


class WorkersPool:
    _pool = None
    _pool_lock = asyncio.Lock()

    __classes_per_threads: Dict[int, Dict[type, Any]] = {}

    @staticmethod
    async def create_pool(n_of_workers: int = DEFAULT_N_OF_WORKERS):
        logger.info(f"Creating worker pool with {n_of_workers = }")
        async with WorkersPool._pool_lock:
            if WorkersPool._pool is None:
                WorkersPool._pool = ProcessPoolExecutor(n_of_workers)

        class PoolContextManager:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_):
                async with WorkersPool._pool_lock:
                    if WorkersPool._pool is None:
                        return
                    logger.info("Waiting worker pool to join")
                    WorkersPool._pool.shutdown(wait=True)
                    WorkersPool._pool = None

        return PoolContextManager()

    async def apply(self, func, *args):
        if WorkersPool._pool is not None:
            loop = asyncio.get_running_loop()
            result = None
            async with WorkersPool._pool_lock:
                result = loop.run_in_executor(WorkersPool._pool, func, *args)
            return await result

        result = func(*args)
        if inspect.iscoroutine(result):
            return await result

        return result

    @staticmethod
    def get_class_instance(
        class_type: type,
        creator_of_new: Optional[Callable] = None,
    ) -> Any:
        process_id = multiprocessing.current_process().pid
        if process_id is None:
            raise RuntimeError(f"Got pid = None")

        if process_id not in WorkersPool.__classes_per_threads:
            WorkersPool.__classes_per_threads[process_id] = {}

        if class_type in WorkersPool.__classes_per_threads[process_id]:
            return WorkersPool.__classes_per_threads[process_id][class_type]
        if creator_of_new is None:
            raise ValueError("Could not find class and got empty creator")

        WorkersPool.__classes_per_threads[process_id][class_type] = creator_of_new()
        return WorkersPool.__classes_per_threads[process_id][class_type]
