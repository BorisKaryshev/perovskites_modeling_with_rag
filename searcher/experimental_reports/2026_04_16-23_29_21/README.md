# Common information

Report was generated: 2026-04-17 01:56:53 +00:00

Comment: Basic RAG

Git branch name: bkaryshev/EXP-001_rag_or_plain_generation

Git commit: 3afc1ec81c7baf6797d3e26b6258ccb42cb46061

Is all files tracked by git: True

Eval dataset path: [docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl](../../docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl)

Path of config of experiment: [docs/EXP_001_is_retrieval_needed_eval/config.ini](../../docs/EXP_001_is_retrieval_needed_eval/config.ini)

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
| passed       |        91.43 |     256 |
| failed       |         7.14 |      20 |
| not found    |         1.43 |       4 |

## Shortness

| shortness   |   Percentage |   Count |
|-------------|--------------|---------|
| perfect     |        87.86 |     246 |
| good        |         7.14 |      20 |
| bad         |         5.00 |      14 |

## Spelling

| spelling   |   Percentage |   Count |
|------------|--------------|---------|
| perfect    |        59.64 |     167 |
| bad        |        36.79 |     103 |
| good       |         3.57 |      10 |

# Retrieval metrics

| Retrieval property          |   Value |
|-----------------------------|---------|
| avg n of chunks             |   10.00 |
| avg relevant position       |    3.89 |
| avg first relevant position |    1.71 |
| avg n of relevan chunks     |    2.17 |
| mrr@1                       |    0.59 |
| mrr@2                       |    0.68 |
| mrr@3                       |    0.71 |
| mrr@5                       |    0.72 |
| mrr@10                      |    0.73 |
| mrr@20                      |    0.73 |
| mrr@100                     |    0.73 |
| ndcg_at_k@1                 |    0.59 |
| ndcg_at_k@2                 |    0.62 |
| ndcg_at_k@3                 |    0.65 |
| ndcg_at_k@5                 |    0.68 |
| ndcg_at_k@10                |    0.75 |
| ndcg_at_k@20                |    0.75 |
| ndcg_at_k@100               |    0.75 |

# Usage metrics

| prompt_tokens   |      Value |
|-----------------|------------|
| n_of_records    |     280.00 |
| sum             | 1728339.00 |
| mean            |    6172.64 |
| min             |    4480.00 |
| p50             |    6138.00 |
| p90             |    6730.20 |
| p95             |    6943.80 |
| p99             |    7468.88 |
| max             |    7543.00 |

| completion_tokens   |     Value |
|---------------------|-----------|
| n_of_records        |    280.00 |
| sum                 | 143285.00 |
| mean                |    511.73 |
| min                 |    198.00 |
| p50                 |    411.00 |
| p90                 |    791.20 |
| p95                 |    985.80 |
| p99                 |   2740.00 |
| max                 |   4799.00 |

| total_tokens   |      Value |
|----------------|------------|
| n_of_records   |     280.00 |
| sum            | 1871624.00 |
| mean           |    6684.37 |
| min            |    4723.00 |
| p50            |    6636.50 |
| p90            |    7335.20 |
| p95            |    7727.40 |
| p99            |    9071.45 |
| max            |   11725.00 |
