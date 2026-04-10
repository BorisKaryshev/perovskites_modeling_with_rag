from .math_utils import ndcg_at_k, mrr_at_k_from_ordered_relevance

from copy import deepcopy
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
import numpy as np
from pathlib import Path
import sys
import logging

from git import Repo
from tabulate import tabulate

logger = logging.getLogger(__name__)


@dataclass
class RawMetric:
    metric_name: str
    verdict: str


def _format_datetime_with_offset(dt: datetime) -> str:
    """
    Format a timezone-aware datetime object as:
    YYYY-MM-DD HH:MM:SS+HH:MM (without milliseconds)
    """
    base = dt.strftime("%Y-%m-%d %H:%M:%S")
    offset = dt.strftime("%z")
    if offset:
        offset = offset[:3] + ":" + offset[3:]
    else:
        offset = "+00:00"
    return f"{base} {offset}"


class ReportGenerator:
    def __init__(
        self,
        eval_dataset_path: Optional[Path] = None,
        skip_check: bool = True,
        output_path: Optional[Path] = None,
        config_path: Optional[Path] = None,
        knowledge_base_files_paths: List[Path] = [],
    ):
        self._knowledge_base_files_paths = deepcopy(knowledge_base_files_paths)
        self._eval_dataset_path = eval_dataset_path
        self._config_path = config_path

        if not skip_check and not self.is_valid_for_generation():
            raise RuntimeError("Failed check for report generation")

        self._output_stream = sys.stderr
        if output_path:
            p = Path(output_path)
            p.parent.mkdir(exist_ok=True, parents=True)
            self._output_stream = open(p, mode="w")

        self._records = []

        self._metrics = defaultdict(int)
        self._usages = defaultdict(list)

        self._retrieval_is_relevant = []

    def is_valid_for_generation(self):
        repo = Repo(Path(__file__), search_parent_directories=True)

        is_valid = True

        if repo.is_dirty(untracked_files=True):
            logger.error(
                f"Evaluation cannot proceed. You have uncommited files. Commit before evaluation."
            )
            is_valid = False

        return is_valid

    def add_raw_metrics(self, raw_metrics: List[RawMetric]):
        for i in raw_metrics:
            self._metrics[i.metric_name] += 1

            self._records.append(i)

    def add_row(self, record: list):
        for i in record:
            self.add_raw_metrics(
                [RawMetric(metric_name=i.metric_name, verdict=i.verdict.name)]
            )

    def add_usages(
        self, prompt_tokens: int, completion_tokens: int, total_tokens: int, **_
    ):

        self._usages["prompt_tokens"].append(prompt_tokens)
        self._usages["completion_tokens"].append(completion_tokens)
        self._usages["total_tokens"].append(total_tokens)

    def add_retrieval(
        self,
        is_relevant: List[bool],
        **_,
    ):
        is_relevant_array = np.zeros(len(is_relevant))
        is_relevant_array[is_relevant] = 1

        self._retrieval_is_relevant.append(is_relevant_array)

    def export_stats_as_dict(self) -> dict:
        result = {}
        result["metrics"] = {}
        for metric in self._metrics.keys():
            result["metrics"][metric] = {}

            # Collect all values for this column
            values = [i.verdict for i in self._records if (i.metric_name == metric)]
            total = len(values)
            if total == 0:
                continue

            # Count frequencies
            counter = Counter(values)

            result["metrics"][metric]["columns"] = [metric, "Percentage", "Count"]
            result["metrics"][metric]["values"] = []
            # Sort values alphabetically for consistent output (optional)
            total_cnt = 0
            for val in counter.keys():
                cnt = counter[val]
                total_cnt += cnt
                percentage = (cnt / total) * 100
                result["metrics"][metric]["values"].append([val, percentage, cnt])

        repo = Repo(__file__, search_parent_directories=True)
        result["common"] = {
            "git_commit": repo.head.commit.hexsha,
            "git_branch": repo.active_branch.name,
            "is_all_files_commited": not repo.is_dirty(untracked_files=True),
            "knowledge_base_files_paths": [
                str(p) for p in self._knowledge_base_files_paths
            ],
        }

        result["common"]["eval_dataset_path"] = str(self._eval_dataset_path)
        result["common"]["config_path"] = str(self._config_path)
        result["common"]["timestamp"] = _format_datetime_with_offset(
            datetime.now().astimezone()
        )

        result["usages"] = {}
        for k, v in self._usages.items():
            result["usages"][k] = {
                "n_of_records": len(v),
                "sum": sum(v),
                "mean": float(np.mean(v)),
                "min": float(np.min(v)),
                "p50": float(np.percentile(v, 50)),
                "p90": float(np.percentile(v, 90)),
                "p95": float(np.percentile(v, 95)),
                "p99": float(np.percentile(v, 99)),
                "max": float(np.max(v)),
            }

        if self._retrieval_is_relevant:
            is_relevant_matrix = np.stack(self._retrieval_is_relevant)

            _, cols = np.where(is_relevant_matrix == 1)
            all_positions = cols + 1
            avg_relevant_all = (
                np.mean(all_positions) if len(all_positions) > 0 else None
            )

            first_indecies = np.argmax(is_relevant_matrix, axis=1)
            has_relevant = np.any(is_relevant_matrix == 1, axis=1)
            first_positions = first_indecies[has_relevant] + 1
            avg_relevant_first = (
                np.mean(first_positions) if len(first_positions) > 0 else None
            )

            result["retrieval"] = {
                "avg n of chunks": np.mean(
                    [len(i) for i in self._retrieval_is_relevant]
                ),
                "avg relevant position": avg_relevant_all,
                "avg first relevant position": avg_relevant_first,
                "mrr@1": mrr_at_k_from_ordered_relevance(is_relevant_matrix, 1),
                "mrr@2": mrr_at_k_from_ordered_relevance(is_relevant_matrix, 2),
                "mrr@3": mrr_at_k_from_ordered_relevance(is_relevant_matrix, 3),
                "mrr@5": mrr_at_k_from_ordered_relevance(is_relevant_matrix, 5),
                "mrr@10": mrr_at_k_from_ordered_relevance(is_relevant_matrix, 10),
                "mrr@20": mrr_at_k_from_ordered_relevance(is_relevant_matrix, 20),
                "mrr@100": mrr_at_k_from_ordered_relevance(is_relevant_matrix, 100),
                "ndcg_at_k@1": ndcg_at_k(is_relevant_matrix, 1),
                "ndcg_at_k@2": ndcg_at_k(is_relevant_matrix, 2),
                "ndcg_at_k@3": ndcg_at_k(is_relevant_matrix, 3),
                "ndcg_at_k@5": ndcg_at_k(is_relevant_matrix, 5),
                "ndcg_at_k@10": ndcg_at_k(is_relevant_matrix, 10),
                "ndcg_at_k@20": ndcg_at_k(is_relevant_matrix, 20),
                "ndcg_at_k@100": ndcg_at_k(is_relevant_matrix, 100),
            }

        return result

    def _print(self, *args, skip_space: bool = False, **kwargs):
        print(*args, **kwargs, file=self._output_stream)
        if not skip_space:
            print(**kwargs, file=self._output_stream)

    def print_percentages(self):
        stats_dict = self.export_stats_as_dict()

        self._print("# Common information")
        curr_datetime = stats_dict["common"]["timestamp"]
        self._print(f"Report was generated: {curr_datetime}")
        self._print(f"Git branch name: {stats_dict['common']['git_branch']}")
        self._print(f"Git commit: {stats_dict['common']['git_commit']}")
        self._print(
            f"Is all files tracked by git: {stats_dict['common']['is_all_files_commited']}"
        )

        if eval_dataset_path := stats_dict["common"]["eval_dataset_path"]:
            self._print(f"Eval dataset path: {eval_dataset_path}")

        if config_path := stats_dict["common"]["config_path"]:
            self._print(f"Path of config of experiment: {config_path}")

        self._print("## Knowladge base content")
        if not stats_dict["common"]["knowledge_base_files_paths"]:
            self._print("Have no tracked files")
        else:
            for p in stats_dict["common"]["knowledge_base_files_paths"]:
                self._print(f"- {p}", skip_space=True)
        self._print("", skip_space=True)

        self._print("# Generation metrics")
        for metric_name, data in stats_dict["metrics"].items():
            self._print(f"## {metric_name.capitalize()}")
            columns = data["columns"]
            rows = data["values"]

            self._print(
                tabulate(rows, headers=columns, floatfmt=".2f", tablefmt="github")
            )

        self._print("# Retrieval metrics")
        if stats_dict.get("retrieval"):
            columns = ["Retrieval property", "Value"]
            rows = []

            for k, v in stats_dict["retrieval"].items():
                rows.append([k, v])
            self._print(
                tabulate(rows, headers=columns, floatfmt=".2f", tablefmt="github")
            )
        else:
            self._print("No documents were retrieved during experiment")
        self._print("# Usage metrics")
        for usage_name, metrics in stats_dict["usages"].items():
            columns = [usage_name, "Value"]
            rows = []

            for k, v in metrics.items():
                rows.append([k, v])
            self._print(
                tabulate(rows, headers=columns, floatfmt=".2f", tablefmt="github")
            )
