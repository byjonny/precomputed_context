#!/usr/bin/env python3
"""Plot paper-style bar charts for thinking-exemplar transfer results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DATASET_LABELS = {
    "arc_challenge": "ARC-Challenge",
    "openbookqa": "OpenBookQA",
    "gsm8k": "GSM8K",
    "mmlu_pro": "MMLU-Pro",
    "math": "MATH",
    "svamp": "SVAMP",
    "asdiv": "ASDiv",
    "aqua": "AQuA",
    "mawps": "MAWPS",
    "csqa": "CSQA",
    "strategyqa": "StrategyQA",
    "bbh_date": "Date Understanding",
    "bbh_sports": "Sports Understanding",
    "saycan": "SayCan",
    "last_letter": "Last Letter Concat.",
    "coin_flip": "Coin Flip",
}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def plot_grouped_correct_counts(rows: list[dict[str, str]], output_prefix: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    labels = [DATASET_LABELS.get(row["dataset"], row["dataset"]) for row in rows]
    none = np.array([int(row["none_correct"]) for row in rows])
    context = np.array([int(row["context_correct"]) for row in rows])
    totals = np.array([int(row["none_total"]) for row in rows])
    max_total = int(max(totals)) if len(totals) else 30
    delta = context - none
    total_values = sorted({int(total) for total in totals})
    if not total_values:
        sample_note = "No evaluation examples found."
    elif len(total_values) == 1:
        sample_note = f"Each dataset contains {total_values[0]} evaluation examples. Bar labels show correct / total."
    else:
        sample_note = (
            f"Dataset totals vary from {total_values[0]} to {total_values[-1]} examples. "
            "Bar labels show correct / total."
        )

    y = np.arange(len(rows))
    bar_h = 0.34

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.labelsize": 9,
            "axes.titlesize": 10,
            "legend.fontsize": 8.5,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    fig, ax = plt.subplots(figsize=(7.4, 5.8), constrained_layout=True)
    baseline_color = "#6b7280"
    context_color = "#2563eb"

    ax.barh(y - bar_h / 2, none, height=bar_h, color=baseline_color, label="No context")
    ax.barh(y + bar_h / 2, context, height=bar_h, color=context_color, label="Thinking exemplar")

    for i, (n, c, d, total) in enumerate(zip(none, context, delta, totals, strict=True)):
        ax.text(n + 0.35, i - bar_h / 2, f"{int(n)}/{int(total)}", va="center", ha="left", color=baseline_color, fontsize=7.5)
        ax.text(c + 0.35, i + bar_h / 2, f"{int(c)}/{int(total)}", va="center", ha="left", color=context_color, fontsize=7.5)
        ax.text(
            max_total + 1.0,
            i,
            f"{int(d):+d}",
            va="center",
            ha="left",
            fontsize=7.5,
            color="#166534" if d > 0 else "#991b1b" if d < 0 else "#374151",
        )

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, max_total + 4.4)
    ax.set_xlabel("Correct answers")
    ax.set_title("Effect of One Thinking Exemplar on Non-Thinking Qwen3.5-4B")
    ax.grid(axis="x", color="#e5e7eb", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.legend(loc="lower right", frameon=False)
    ax.text(max_total + 1.0, -0.85, "Δ", ha="left", va="bottom", fontsize=8, fontweight="bold")
    ax.text(
        0,
        len(rows) + 0.55,
        sample_note,
        ha="left",
        va="center",
        fontsize=8,
        color="#4b5563",
    )

    fig.savefig(output_prefix.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(output_prefix.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create paper-style bar chart from thinking-exemplar CSV.")
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("results/thinking_exemplar_multi/multi_native_30_v2.csv"),
    )
    parser.add_argument(
        "--output-prefix",
        type=Path,
        default=Path("results/thinking_exemplar_multi/multi_native_30_v2_paper_bar"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_rows(args.csv)
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    plot_grouped_correct_counts(rows, args.output_prefix)
    print(f"wrote {args.output_prefix.with_suffix('.pdf')}")
    print(f"wrote {args.output_prefix.with_suffix('.png')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
