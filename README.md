# Precomputed Context Experiments

This repository contains small-scale reasoning experiments for evaluating how
precomputed context, structured hints, and thinking exemplars affect
non-thinking LLM inference.

## Repository Layout

```text
.
├── data/                         # Hand-authored experiment inputs
│   └── hint_cases.json
├── docs/                         # Human-readable reports and notes
├── results/                      # Generated JSONL, Markdown, CSV, and figures
├── scripts/
│   ├── analysis/                 # Plotting and post-processing utilities
│   └── exploratory/              # One-off prompt probes
└── src/precomputed_context/      # Reusable loaders and experiment runners
```

## Main Entry Points

Run commands from the repository root with `PYTHONPATH=src`, or install the
package in editable mode.

```bash
PYTHONPATH=src python -m precomputed_context.run_context_eval
PYTHONPATH=src python -m precomputed_context.structured_transfer_eval
PYTHONPATH=src python -m precomputed_context.bbh_transfer_eval
PYTHONPATH=src python -m precomputed_context.hint_lab --cases-file data/hint_cases.json
PYTHONPATH=src python -m precomputed_context.thinking_exemplar_transfer
PYTHONPATH=src python -m precomputed_context.thinking_exemplar_multi_dataset
```

Dataset inspection and export:

```bash
PYTHONPATH=src python -m precomputed_context.eval_dataset_reader --list
PYTHONPATH=src python -m precomputed_context.eval_dataset_reader --datasets positive50 --offset 20 --limit 2 --preview 1
```

Plot generation:

```bash
python scripts/analysis/plot_thinking_exemplar_results.py
```

## Notes

- `results/` is intentionally kept in the repo because it contains the recorded
  experiment artifacts.
- The experiment runners fetch public datasets from Hugging Face and use
  `mlx_lm` for local model inference.
- Default output directories still point into `results/` to preserve the
  existing artifact organization.

