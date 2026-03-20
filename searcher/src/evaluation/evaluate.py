from .metric import Metric
from src.llm_providers import ChatProvider

from asyncio import TaskGroup, gather, Queue, Semaphore
from typing import AsyncGenerator, Iterable
import logging

logger = logging.getLogger(__name__)


LLM_OUTPUT_FORMAT_PROMPT = """

"""


async def try_call_llm(
    llm: ChatProvider,
    prompt: str,
    format_prompt: str,
    return_type: type,
    n_of_retries: int = 3,
):
    messages = [
        {"role": "system", "content": prompt},
        {"role": "system", "content": format_prompt},
    ]
    for _ in range(n_of_retries):
        try:
            response = await llm.chat_response_only(messages)
            return return_type.parse_raw(response)
        except Exception as ex:
            logger.warning(f"Got response: {response}")
            logger.warning(f"Got ex while trying to send request to llm: {ex}")


class Evaluator:
    def __init__(
        self,
        metrics: Iterable[Metric],
        llm_client: ChatProvider,
        n_of_parallel_requests: int = 1,
    ):
        self._metrics = metrics
        [i.get_response_class() for i in self._metrics]

        self._semapthore = Semaphore(n_of_parallel_requests)

        self._llm_client = llm_client
        self._n_of_parallel_requests = n_of_parallel_requests

    async def eval_row(self, data_instance: dict):
        async with self._semapthore:
            tasks = []
            for i in self._metrics:
                prompt = i.compile_prompt(**data_instance)
                format_prompt = i.get_output_format_prompt()
                return_type = i.get_response_class()

                tasks.append(
                    try_call_llm(
                        self._llm_client,
                        prompt,
                        format_prompt,
                        return_type,
                    )
                )

            return await gather(*tasks)

    async def eval_dataset(self, dataset: Iterable[dict]) -> AsyncGenerator[str, None]:
        input_queue = Queue(self._n_of_parallel_requests)
        output_queue = Queue(self._n_of_parallel_requests)

        async def reader():
            for i in dataset:
                await input_queue.put(i)

            for _ in range(self._n_of_parallel_requests):
                await input_queue.put(None)

        async def worker():
            row = await input_queue.get()
            while row is not None:
                await output_queue.put(await self.eval_row(row))

            await output_queue.put(None)

        async with TaskGroup() as tg:
            tg.create_task(reader())

            for _ in range(self._n_of_parallel_requests):
                tg.create_task(worker())

            n_of_nones = 0

            while n_of_nones < self._n_of_parallel_requests:
                response = await output_queue.get()
                if response is None:
                    n_of_nones += 1
                    continue

                yield response
