from .interface import EntryPoint
from src.evaluation import ReportGenerator, RawMetric

from argparse import ArgumentParser, Namespace
from pathlib import Path
import logging
import json

import zstandard as zstd

logger = logging.getLogger(__name__)


class EvalStatsEntryPoint(EntryPoint):
    def __init__(self, args: Namespace):
        super().__init__(args)

        self._printer = ReportGenerator()
        self._eval_result_file = args.eval_result_file

    @classmethod
    def add_subparser(cls, parser: ArgumentParser) -> None:
        parser.add_argument("eval_result_file", type=Path)

    async def run(self) -> None:
        open_func = open
        if Path(self._eval_result_file).suffix == ".zst":
            open_func = zstd.open

        with open_func(self._eval_result_file, mode="r") as f:
            for i in f:
                d = json.loads(i)

                for k, v in d["metrics"].items():
                    raw_metric = RawMetric(metric_name=k, verdict=v)
                    self._printer.add_raw_metrics([raw_metric])

                self._printer.add_usages(**d["usage"])
                self._printer.add_retrieval(**d["retrieval"]["metrics"])
        self._printer.print_percentages()
