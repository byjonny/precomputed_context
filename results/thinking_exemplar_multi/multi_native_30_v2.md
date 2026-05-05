# Multi-Dataset Thinking-Exemplar Transfer

- Run id: `multi_native_30_v2`
- Model: `Qwen/Qwen3.5-4B`
- Exemplar generation: `enable_thinking=True`
- Evaluation generation: `enable_thinking=False`
- Eval examples per dataset: `30`
- Thinking max tokens: `4096`

## Results

| Dataset | None | Thinking exemplar | Delta | Recovered | Harmed |
|---|---:|---:|---:|---:|---:|
| `arc_challenge` | 28/30 (93.3%) | 26/30 (86.7%) | -2 (-6.7%) | 1 | 3 |
| `openbookqa` | 28/30 (93.3%) | 26/30 (86.7%) | -2 (-6.7%) | 0 | 2 |
| `gsm8k` | 6/30 (20.0%) | 6/30 (20.0%) | +0 (+0.0%) | 2 | 2 |
| `mmlu_pro` | 13/30 (43.3%) | 11/30 (36.7%) | -2 (-6.7%) | 2 | 4 |
| `math` | 5/30 (16.7%) | 3/30 (10.0%) | -2 (-6.7%) | 1 | 3 |
| `svamp` | 20/30 (66.7%) | 11/30 (36.7%) | -9 (-30.0%) | 0 | 9 |
| `asdiv` | 26/30 (86.7%) | 26/30 (86.7%) | +0 (+0.0%) | 1 | 1 |
| `aqua` | 13/30 (43.3%) | 6/30 (20.0%) | -7 (-23.3%) | 2 | 9 |
| `mawps` | 18/30 (60.0%) | 18/30 (60.0%) | +0 (+0.0%) | 1 | 1 |
| `csqa` | 19/30 (63.3%) | 18/30 (60.0%) | -1 (-3.3%) | 1 | 2 |
| `strategyqa` | 19/30 (63.3%) | 16/30 (53.3%) | -3 (-10.0%) | 3 | 6 |
| `bbh_date` | 19/30 (63.3%) | 17/30 (56.7%) | -2 (-6.7%) | 2 | 4 |
| `bbh_sports` | 17/30 (56.7%) | 16/30 (53.3%) | -1 (-3.3%) | 8 | 9 |
| `saycan` | 0/30 (0.0%) | 0/30 (0.0%) | +0 (+0.0%) | 0 | 0 |
| `last_letter` | 0/30 (0.0%) | 0/30 (0.0%) | +0 (+0.0%) | 0 | 0 |
| `coin_flip` | 19/30 (63.3%) | 13/30 (43.3%) | -6 (-20.0%) | 10 | 16 |
| **Total** | **250/480 (52.1%)** | **213/480 (44.4%)** | **-37 (-7.7%)** |  |  |

## Artifacts

- Exemplar JSONL: `results/thinking_exemplar_multi/multi_native_30_v2_exemplars.jsonl`
- Raw eval JSONL: `results/thinking_exemplar_multi/multi_native_30_v2.jsonl`
- CSV table: `results/thinking_exemplar_multi/multi_native_30_v2.csv`
- SVG chart: `results/thinking_exemplar_multi/multi_native_30_v2_chart.svg`
