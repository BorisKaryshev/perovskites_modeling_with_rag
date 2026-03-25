from .interface import EntryPoint

from src.evaluation import Metric, Evaluator
from src.llm_providers import ChatProvider
from src.rag_pipelines import RagPipeline

import asyncio
from pathlib import Path
from typing import Literal, Union
from argparse import ArgumentParser, Namespace
import logging
import json
import sys
from csv import DictReader

logger = logging.getLogger(__name__)


class FileReader:
    def read(self, file: Path, file_format: Union[Literal["json"], Literal["csv"]]):
        if file_format == "json":
            return self._read_json(file)
        elif file_format == "csv":
            return self._read_csv(file)

    def _read_json(self, file: Path):
        with open(file) as f:
            for line in f:
                yield json.loads(line)

    def _read_csv(self, file: Path):
        with open(file) as f:
            yield from DictReader(f)


class EvalEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._n_of_parallel_requests = args.n_of_parallel_requests
        self._input_format = args.input_format
        self._dataset_file_path = args.dataset_file
        self._output_file_path = args.output_file

        self._rag = RagPipeline.create(
            self._config["rag"].pop("type"),
            config=self._config,
        )

        self._metrics = [
            Metric(
                name="correctnes",
                prompt="Check if the response contains points from correct answer, and return 'passed' or 'failed'\nRESPONSE: {response}\nCORRECT: {correct_answer}",
                available_values=["passed", "failed"],
            ),
            Metric(
                name="shortness",
                prompt="Response must answer on request fully, but be short. Check whether answer is short and easy to read or not. Return 'perfect', 'good' or 'bad'\nREQUEST: {query}\nRESPONSE: {response}",
                available_values=["perfect", "good", "bad"],
            ),
            Metric(
                name="spelling",
                prompt="Response must be free of typos, linguistic, syntactic, punctuation, or other errors. Check the correctness of response. Return 'perfect', 'good' or 'bad'\nREQUEST: {query}\nRESPONSE: {response}",
                available_values=["perfect", "good", "bad"],
            ),
        ]

        llm_for_eval = ChatProvider.create(
            self._config["eval"]["llm_options"].pop("type"),
            **self._config["eval"]["llm_options"],
        )
        self._evaluator = Evaluator(
            self._metrics,
            llm_for_eval,
            n_of_parallel_requests=self._n_of_parallel_requests,
        )

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "-o", "--output_file", type=Path, required=False, default=None
        )
        parser.add_argument(
            "-f",
            "--input_format",
            default="json",
            choices=["json", "csv"],
        )
        parser.add_argument(
            "-n",
            "--n_of_parallel_requests",
            default=10,
            type=int,
            required=False,
        )
        parser.add_argument(
            "dataset_file",
            type=Path,
            help="It must contain columns: query, correct_answer",
        )

    async def score_row(self, row: dict):
        response = await self._rag.search(row["query"], [])

        score_params = {
            "query": row["query"],
            "correct_answer": row["correct_answer"],
            "response": response.model_dump_json(),
        }

        scores = await self._evaluator.eval_row(score_params)

        result = {
            "query": row["query"],
            "response": response.response,
            **{i.metric_name: i.verdict.value for i in scores},
        }
        return result

    async def run(self) -> None:
        queue = asyncio.Queue(self._n_of_parallel_requests)
        output_queue = asyncio.Queue()

        async def worker():
            request = await queue.get()
            while request is not None:
                await output_queue.put(await self.score_row(request))
                request = await queue.get()
            await output_queue.put(None)

        async def reader():
            out_stream = sys.stdout
            if self._output_file_path:
                out_stream = open(self._output_file_path, mode="w")

            result = await output_queue.get()
            n_of_nones = 0 if result is not None else 1

            while n_of_nones < self._n_of_parallel_requests:
                result = await output_queue.get()
                if result is None:
                    n_of_nones += 1
                    continue

                out_stream.write(json.dumps(result))

        async with asyncio.TaskGroup() as tg:
            for _ in range(self._n_of_parallel_requests):
                tg.create_task(worker())

            tg.create_task(reader())

            for i in FileReader().read(self._dataset_file_path, self._input_format):
                await queue.put(i)

            for _ in range(self._n_of_parallel_requests):
                await queue.put(None)
