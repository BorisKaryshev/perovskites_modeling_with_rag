# Common information

Report was generated: 2026-04-17 19:41:33 +00:00

Comment: EXP-001 simple rag with embeddings search only

Git branch name: master

Git commit: b68c04b21d59f7980cc393568df69c1da815bc08

Is all files tracked by git: True

Eval dataset path: [docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl](../../docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl)

Path of config of experiment: [docs/EXP_001_is_retrieval_needed_eval/config_embeding_only_search.ini](../../docs/EXP_001_is_retrieval_needed_eval/config_embeding_only_search.ini)

## Knowladge base content

- [docs/EXP_001_is_retrieval_needed_eval/pdfs/all-inorganic-perovskite-solar-cells.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/all-inorganic-perovskite-solar-cells.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/general-working-principles-of-ch3nh3pbx3-perovskite-solar-cells.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/general-working-principles-of-ch3nh3pbx3-perovskite-solar-cells.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/liu2017.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/liu2017.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/nontemplate-synthesis-of-ch3nh3pbbr3-perovskite-nanoparticles.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/nontemplate-synthesis-of-ch3nh3pbbr3-perovskite-nanoparticles.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/Perovskite.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/Perovskite.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/Perovskite photonic sources.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/Perovskite photonic sources.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/progress-in-perovskite-photocatalysis.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/progress-in-perovskite-photocatalysis.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/s40820-021-00672-w.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/s40820-021-00672-w.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/s40820-023-01140-3.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/s40820-023-01140-3.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/s41377-024-01461-x.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/s41377-024-01461-x.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/s41467-018-05454-4.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/s41467-018-05454-4.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/s41467-018-07255-1.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/s41467-018-07255-1.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/semitransparent-perovskite-solar-cells.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/semitransparent-perovskite-solar-cells.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/understanding-degradation-mechanisms-and-improving-stability-of-perovskite-photovoltaics.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/understanding-degradation-mechanisms-and-improving-stability-of-perovskite-photovoltaics.pdf)
- [docs/EXP_001_is_retrieval_needed_eval/pdfs/What_Defines_a_Perovskite.pdf](../../docs/EXP_001_is_retrieval_needed_eval/pdfs/What_Defines_a_Perovskite.pdf)

# Generation metrics

## Correctnes

| correctnes   |   Percentage |   Count |
|--------------|--------------|---------|
| failed       |        26.92 |      77 |
| passed       |        70.98 |     203 |
| not found    |         2.10 |       6 |

## Shortness

| shortness   |   Percentage |   Count |
|-------------|--------------|---------|
| bad         |        17.83 |      51 |
| good        |         6.64 |      19 |
| perfect     |        75.52 |     216 |

## Spelling

| spelling   |   Percentage |   Count |
|------------|--------------|---------|
| bad        |        45.07 |     128 |
| perfect    |        50.35 |     143 |
| good       |         4.58 |      13 |

## Correctness

| correctness   |   Percentage |   Count |
|---------------|--------------|---------|
| bad           |       100.00 |       2 |

# Retrieval metrics

| Retrieval property          |   Value |
|-----------------------------|---------|
| avg n of chunks             |   10.00 |
| avg relevant position       |    4.51 |
| avg first relevant position |    2.92 |
| avg n of relevan chunks     |    1.63 |
| mrr@1                       |    0.34 |
| mrr@2                       |    0.40 |
| mrr@3                       |    0.43 |
| mrr@5                       |    0.45 |
| mrr@10                      |    0.47 |
| mrr@20                      |    0.47 |
| mrr@100                     |    0.47 |
| ndcg_at_k@1                 |    0.34 |
| ndcg_at_k@2                 |    0.36 |
| ndcg_at_k@3                 |    0.38 |
| ndcg_at_k@5                 |    0.44 |
| ndcg_at_k@10                |    0.52 |
| ndcg_at_k@20                |    0.52 |
| ndcg_at_k@100               |    0.52 |

# Usage metrics

| prompt_tokens   |      Value |
|-----------------|------------|
| n_of_records    |     286.00 |
| sum             | 1713896.00 |
| mean            |    5992.64 |
| min             |    4019.00 |
| p50             |    6006.50 |
| p90             |    6626.50 |
| p95             |    6798.50 |
| p99             |    7185.70 |
| max             |    8532.00 |

| completion_tokens   |     Value |
|---------------------|-----------|
| n_of_records        |    286.00 |
| sum                 | 196977.00 |
| mean                |    688.73 |
| min                 |    117.00 |
| p50                 |    445.50 |
| p90                 |   1166.00 |
| p95                 |   2163.00 |
| p99                 |   4731.00 |
| max                 |   9067.00 |

| total_tokens   |      Value |
|----------------|------------|
| n_of_records   |     286.00 |
| sum            | 1910873.00 |
| mean           |    6681.37 |
| min            |    4693.00 |
| p50            |    6481.00 |
| p90            |    7473.50 |
| p95            |    8227.00 |
| p99            |   11640.70 |
| max            |   17599.00 |
