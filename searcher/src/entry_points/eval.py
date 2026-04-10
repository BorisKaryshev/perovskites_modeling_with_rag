import git
from .add_document import AddDocumentEntryPoint

from src.evaluation import Metric, Evaluator
from src.llm_providers import ChatProvider
from src.evaluation import ReportGenerator

import asyncio
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Literal, Union
from argparse import ArgumentParser, Namespace
import logging
import json
from csv import DictReader

import zstandard as zstd

logger = logging.getLogger(__name__)

DEFAULT_REPORTS_PATH = (
    Path(__file__).parent.parent.parent
    / Path("experimental_reports")
    / Path(datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))
)

FILENAMES = {
    "report": Path("README.md"),
    "report_json": Path("report.json"),
    "results": Path("detailed_resulsts.jsonl"),
}


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


class EvalEntryPoint(AddDocumentEntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._n_of_parallel_requests = args.n_of_parallel_requests
        self._input_format = args.input_format
        self._dataset_file_path = args.dataset_file
        self._output_path = args.output
        self._files_to_add = args.files_to_add

        if not self._output_path:
            self._output_path = DEFAULT_REPORTS_PATH
        self._output_path.mkdir(exist_ok=True, parents=True)

        self._not_compress = args.not_compress

        self._printer = ReportGenerator(
            skip_check=args.skip_check,
            knowledge_base_files_paths=self._files_to_add,
            eval_dataset_path=self._dataset_file_path,
            output_path=self._output_path / FILENAMES["report"],
            config_path=args.config,
            base_path=Path("../.."),
        )

        self._retrieval_metrics = [
            Metric(
                name="is_relevant",
                prompt="Check if chunk contains facts required to answer on questions correctly. Return true if contains and false if not.\nCORRECT ANSWER:\n{correct_answer}\n\nCHUNK:\n{chunk}",
                available_values=["true", "false"],
                is_boolean=True,
            )
        ]

        self._metrics = [
            Metric(
                name="correctnes",
                prompt="Check if the response contains points from correct answer, and return 'passed' or 'failed'. Return 'not found' if response says so. \nRESPONSE: {response}\nCORRECT: {correct_answer}",
                available_values=["passed", "failed", "not found"],
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
        self._retrieval_evaluator = Evaluator(
            self._retrieval_metrics,
            llm_for_eval,
            n_of_parallel_requests=self._n_of_parallel_requests,
        )

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        AddDocumentEntryPoint.add_subparser(parser)

        parser.add_argument("-s", "--skip_check", action="store_true", default=False)
        parser.add_argument("-o", "--output", type=Path, required=False, default=None)
        parser.add_argument(
            "-f",
            "--input_format",
            default="json",
            choices=["json", "csv"],
        )
        parser.add_argument(
            "-d",
            "--dataset_file",
            required=True,
            type=Path,
            help="It must contain columns: query, correct_answer",
        )
        parser.add_argument("--not-compress", type=bool, default=False, required=False)

    async def score_row(self, row: dict):
        response = await self._rag.search_verbose(row["query"], [])

        score_params = {
            "query": row["query"],
            "correct_answer": row["correct_answer"],
            "response": response.rag_response.model_dump_json(),
        }

        retrieval_scores_tasks = []

        async def f(chunk_local):
            retrieval_params = {
                "chunk": chunk_local,
                "correct_answer": row["correct_answer"],
            }
            return chunk_local, await self._retrieval_evaluator.eval_row(
                retrieval_params
            )

        async with asyncio.TaskGroup() as tg:
            scores = tg.create_task(self._evaluator.eval_row(score_params))

            for _, chunk in response.chunks_retrieved:

                retrieval_scores_tasks.append(tg.create_task(f(chunk)))

        scores = scores.result()

        retrieval_scores_tasks = [i.result() for i in retrieval_scores_tasks]
        retrieval_chunks = [chunk for _, chunk in response.chunks_retrieved]
        retrieval_scores_by_chunk = {
            chunk: scores for chunk, scores in retrieval_scores_tasks
        }

        retrieval_scores = defaultdict(list)
        for chunk in retrieval_chunks:
            for metric in retrieval_scores_by_chunk[chunk]:
                retrieval_scores[metric.metric_name].append(metric.parsed_verdict)

        self._printer.add_row(scores)
        self._printer.add_usages(
            response.prompt_tokens, response.completion_tokens, response.total_tokens
        )

        if retrieval_scores:
            self._printer.add_retrieval(**retrieval_scores)

        result = {
            "query": row["query"],
            "response": response.rag_response.response,
            "correct_answer": row["correct_answer"],
            "metrics": {**{i.metric_name: i.verdict.value for i in scores}},
            "retrieval": {
                "chunks": [json.loads(i.model_dump_json()) for i in retrieval_chunks],
                "metrics": retrieval_scores,
            },
            "usage": {
                "prompt_tokens": response.prompt_tokens,
                "completion_tokens": response.completion_tokens,
                "total_tokens": response.total_tokens,
            },
        }
        return result

    def _commit(self):
        repo = git.Repo(__file__, search_parent_directories=True)

        repo.index.add(self._output_path)
        repo.index.commit("[AUTO] Adding experimental report")
        repo.git.push()

    async def run(self) -> None:
        await super().run()

        logger.info(f"Coroutime for adding documents finished")

        queue = asyncio.Queue(self._n_of_parallel_requests)
        output_queue = asyncio.Queue()

        async def worker():
            request = await queue.get()
            while request is not None:
                output = None
                try:
                    output = await self.score_row(request)
                except Exception as ex:
                    logger.warning(f"Failed to evaluate row with error: {ex}")
                else:
                    await output_queue.put(output)
                request = await queue.get()
            await output_queue.put(None)

        async def reader():
            if self._not_compress:
                out_stream = open(self._output_path / FILENAMES["results"], mode="w")
            else:
                output_path = Path(
                    str(self._output_path / FILENAMES["results"]) + ".zst"
                )
                out_stream = zstd.open(output_path, mode="w")

            n_of_nones = 0

            while n_of_nones < self._n_of_parallel_requests:
                result = await output_queue.get()

                if result is None:
                    n_of_nones += 1
                else:
                    out_stream.write(json.dumps(result) + "\n")

            out_stream.flush()
            out_stream.close()

        async def read_from_file():
            for i in FileReader().read(self._dataset_file_path, self._input_format):
                await queue.put(i)

            for _ in range(self._n_of_parallel_requests):
                await queue.put(None)

        async with asyncio.TaskGroup() as tg:
            for _ in range(self._n_of_parallel_requests):
                tg.create_task(worker())

            tg.create_task(read_from_file())
            tg.create_task(reader())

        self._printer.print_percentages()

        open_func = zstd.open
        filename_modifier = ".zst"
        if self._not_compress:
            open_func = open
            filename_modifier = ""
        with open_func(
            str(self._output_path / FILENAMES["report_json"]) + filename_modifier,
            mode="w",
        ) as f:
            try:
                print(json.dumps(self._printer.export_stats_as_dict()), file=f)
            except Exception:
                logger.info(f"Got stats: {self._printer.export_stats_as_dict()}")
        logger.info(f"Evaluation completed. Commiting results.")
        self._commit()
