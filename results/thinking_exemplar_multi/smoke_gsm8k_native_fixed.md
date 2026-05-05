# Multi-Dataset Thinking-Exemplar Transfer

- Run id: `smoke_gsm8k_native_fixed`
- Model: `Qwen/Qwen3.5-4B`
- Exemplar generation: `enable_thinking=True`
- Evaluation generation: `enable_thinking=False`
- Eval examples per dataset: `2`
- Thinking max tokens: `2048`

## Results

| Dataset | None | Thinking exemplar | Delta | Recovered | Harmed |
|---|---:|---:|---:|---:|---:|
| `gsm8k` | 1/2 (50.0%) | 1/2 (50.0%) | +0 (+0.0%) | 0 | 0 |
| **Total** | **1/2 (50.0%)** | **1/2 (50.0%)** | **+0 (+0.0%)** |  |  |

## Artifacts

- Exemplar JSONL: `results/thinking_exemplar_multi/smoke_gsm8k_native_fixed_exemplars.jsonl`
- Raw eval JSONL: `results/thinking_exemplar_multi/smoke_gsm8k_native_fixed.jsonl`
- CSV table: `results/thinking_exemplar_multi/smoke_gsm8k_native_fixed.csv`
- SVG chart: `results/thinking_exemplar_multi/smoke_gsm8k_native_fixed_chart.svg`
