# Common information

Report was generated: 2026-04-16 23:29:11 +00:00

Comment: Plain model answering

Git branch name: bkaryshev/EXP-001_rag_or_plain_generation

Git commit: ad8a61eff5ee1057836219748b9c81bab0712080

Is all files tracked by git: True

Eval dataset path: [docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl](../../docs/EXP_001_is_retrieval_needed_eval/dataset.jsonl)

Path of config of experiment: [docs/EXP_001_is_retrieval_needed_eval/no_retrieval_config.ini](../../docs/EXP_001_is_retrieval_needed_eval/no_retrieval_config.ini)

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
| failed       |        65.74 |     190 |
| passed       |        33.91 |      98 |
| not found    |         0.35 |       1 |

## Shortness

| shortness   |   Percentage |   Count |
|-------------|--------------|---------|
| perfect     |        94.46 |     273 |
| bad         |         2.08 |       6 |
| good        |         3.46 |      10 |

## Spelling

| spelling   |   Percentage |   Count |
|------------|--------------|---------|
| perfect    |        73.36 |     212 |
| bad        |        25.26 |      73 |
| good       |         1.38 |       4 |

# Retrieval metrics

No documents were retrieved during experiment

# Usage metrics

| prompt_tokens   |     Value |
|-----------------|-----------|
| n_of_records    |    289.00 |
| sum             | 111472.00 |
| mean            |    385.72 |
| min             |    370.00 |
| p50             |    384.00 |
| p90             |    397.00 |
| p95             |    400.60 |
| p99             |    409.12 |
| max             |    428.00 |

| completion_tokens   |     Value |
|---------------------|-----------|
| n_of_records        |    289.00 |
| sum                 | 112926.00 |
| mean                |    390.75 |
| min                 |     96.00 |
| p50                 |    322.00 |
| p90                 |    668.80 |
| p95                 |    896.40 |
| p99                 |   1462.60 |
| max                 |   1587.00 |

| total_tokens   |     Value |
|----------------|-----------|
| n_of_records   |    289.00 |
| sum            | 224398.00 |
| mean           |    776.46 |
| min            |    477.00 |
| p50            |    708.00 |
| p90            |   1070.00 |
| p95            |   1284.00 |
| p99            |   1841.56 |
| max            |   1969.00 |

