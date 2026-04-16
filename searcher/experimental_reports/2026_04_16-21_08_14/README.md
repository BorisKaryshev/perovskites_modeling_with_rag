# Common information

Report was generated: 2026-04-16 21:17:13 +00:00

Git branch name: bkaryshev/EXP-001_rag_or_plain_generation

Git commit: 851d788dfcdd8480baa71a88d568dfdb6d6783f4

Is all files tracked by git: False

Eval dataset path: [docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl](../../docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl)

Path of config of experiment: [docs/EXP_001_is_retrieval_needed_eval/config.ini](../../docs/EXP_001_is_retrieval_needed_eval/config.ini)

## Knowladge base content

- [docs/EXP_001_is_retrieval_needed_eval/pdfs/all-inorganic-perovskite-solar-cells.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/all-inorganic-perovskite-solar-cells.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/general-working-principles-of-ch3nh3pbx3-perovskite-solar-cells.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/general-working-principles-of-ch3nh3pbx3-perovskite-solar-cells.pdf)

# Generation metrics

## Correctnes

| correctnes   |   Percentage |   Count |
|--------------|--------------|---------|
| passed       |       100.00 |      20 |

## Shortness

| shortness   |   Percentage |   Count |
|-------------|--------------|---------|
| perfect     |        90.00 |      18 |
| good        |         5.00 |       1 |
| bad         |         5.00 |       1 |

## Spelling

| spelling   |   Percentage |   Count |
|------------|--------------|---------|
| bad        |        26.32 |       5 |
| perfect    |        68.42 |      13 |
| good       |         5.26 |       1 |

# Retrieval metrics

| Retrieval property          |   Value |
|-----------------------------|---------|
| avg n of chunks             |   10.00 |
| avg relevant position       |    3.98 |
| avg first relevant position |    1.41 |
| mrr@1                       |    0.68 |
| mrr@2                       |    0.76 |
| mrr@3                       |    0.76 |
| mrr@5                       |    0.77 |
| mrr@10                      |    0.77 |
| mrr@20                      |    0.77 |
| mrr@100                     |    0.77 |
| ndcg_at_k@1                 |    0.68 |
| ndcg_at_k@2                 |    0.67 |
| ndcg_at_k@3                 |    0.64 |
| ndcg_at_k@5                 |    0.68 |
| ndcg_at_k@10                |    0.75 |
| ndcg_at_k@20                |    0.75 |
| ndcg_at_k@100               |    0.75 |

# Usage metrics

| prompt_tokens   |     Value |
|-----------------|-----------|
| n_of_records    |     19.00 |
| sum             | 119967.00 |
| mean            |   6314.05 |
| min             |   5861.00 |
| p50             |   6453.00 |
| p90             |   6491.20 |
| p95             |   6493.00 |
| p99             |   6500.20 |
| max             |   6502.00 |

| completion_tokens   |   Value |
|---------------------|---------|
| n_of_records        |   19.00 |
| sum                 | 9612.00 |
| mean                |  505.89 |
| min                 |  285.00 |
| p50                 |  458.00 |
| p90                 |  734.00 |
| p95                 |  784.90 |
| p99                 |  805.78 |
| max                 |  811.00 |

| total_tokens   |     Value |
|----------------|-----------|
| n_of_records   |     19.00 |
| sum            | 129579.00 |
| mean           |   6819.95 |
| min            |   6242.00 |
| p50            |   6826.00 |
| p90            |   7143.20 |
| p95            |   7206.30 |
| p99            |   7280.46 |
| max            |   7299.00 |

