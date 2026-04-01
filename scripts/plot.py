#!/usr/bin/env python3
"""
Plot Docker image size optimization progress.

Reads results.json and generates:
1. Total size over iterations (line chart)
2. Per-image size comparison (grouped bar chart)
3. Size breakdown by image (stacked area chart)

Saves plots to progress.png
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

RESULTS_FILE = Path(__file__).parent / "results.json"
OUTPUT_FILE = Path(__file__).parent / "progress.png"

# Color palette
COLORS = {
    "reduce-docker/base": "#4C72B0",
    "reduce-docker/datascience": "#55A868",
    "reduce-docker/deeplearning": "#C44E52",
    "reduce-docker/jupyterhub-datascience": "#8172B3",
    "reduce-docker/jupyterhub-deeplearning": "#CCB974",
}

SHORT_NAMES = {
    "reduce-docker/base": "base",
    "reduce-docker/datascience": "datascience",
    "reduce-docker/deeplearning": "deeplearning",
    "reduce-docker/jupyterhub-datascience": "jh-datasci",
    "reduce-docker/jupyterhub-deeplearning": "jh-deeplearn",
}


def load_results() -> list[dict]:
    if not RESULTS_FILE.exists():
        print("No results.json found. Run measure.py first.")
        sys.exit(1)
    return json.loads(RESULTS_FILE.read_text())


def plot_total_over_iterations(ax, results: list[dict]):
    """Line chart: total image size over iterations."""
    iterations = [r["iteration"] for r in results]
    totals = [r["total_mb"] for r in results]

    ax.plot(iterations, totals, "o-", color="#4C72B0", linewidth=2, markersize=8)
    ax.fill_between(iterations, totals, alpha=0.15, color="#4C72B0")

    # Annotate baseline and best
    if totals:
        baseline = totals[0]
        best_val = min(totals)
        best_idx = totals.index(best_val)

        ax.axhline(y=baseline, color="gray", linestyle="--", alpha=0.5, label=f"Baseline: {baseline:.0f} MB")

        if best_idx > 0:
            saved = baseline - best_val
            pct = (saved / baseline) * 100
            ax.annotate(
                f"Best: {best_val:.0f} MB\n(-{pct:.1f}%)",
                xy=(iterations[best_idx], best_val),
                xytext=(15, 15),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
                color="#2ca02c",
                arrowprops=dict(arrowstyle="->", color="#2ca02c"),
            )

    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Total Size (MB)", fontsize=11)
    ax.set_title("Total Image Size Over Iterations", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(True, alpha=0.3)


def plot_per_image_comparison(ax, results: list[dict]):
    """Grouped bar chart: per-image size for baseline vs latest."""
    if len(results) < 1:
        return

    baseline = results[0]
    latest = results[-1]

    # Get all image names
    all_images = list(baseline.get("sizes_mb", {}).keys())
    if not all_images:
        return

    x = range(len(all_images))
    width = 0.35

    baseline_sizes = [baseline["sizes_mb"].get(img, 0) for img in all_images]
    latest_sizes = [latest["sizes_mb"].get(img, 0) for img in all_images]

    bars1 = ax.bar(
        [i - width / 2 for i in x], baseline_sizes, width,
        label=f"Baseline (iter {baseline['iteration']})",
        color="#C44E52", alpha=0.8,
    )
    bars2 = ax.bar(
        [i + width / 2 for i in x], latest_sizes, width,
        label=f"Latest (iter {latest['iteration']})",
        color="#4C72B0", alpha=0.8,
    )

    # Add size labels on bars
    for bar in bars1:
        h = bar.get_height()
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 20,
                f"{h:.0f}", ha="center", va="bottom", fontsize=7,
            )
    for bar in bars2:
        h = bar.get_height()
        if h > 0:
            ax.text(
                bar.get_x() + bar.get_width() / 2, h + 20,
                f"{h:.0f}", ha="center", va="bottom", fontsize=7,
            )

    short = [SHORT_NAMES.get(img, img.split("/")[-1]) for img in all_images]
    ax.set_xticks(list(x))
    ax.set_xticklabels(short, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("Size (MB)", fontsize=11)
    ax.set_title("Per-Image Size: Baseline vs Latest", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis="y")


def plot_size_breakdown(ax, results: list[dict]):
    """Stacked area chart: size breakdown by image over iterations."""
    if not results:
        return

    all_images = list(results[0].get("sizes_mb", {}).keys())
    if not all_images:
        return

    iterations = [r["iteration"] for r in results]

    for img in all_images:
        sizes = [r["sizes_mb"].get(img, 0) for r in results]
        color = COLORS.get(img, None)
        short = SHORT_NAMES.get(img, img.split("/")[-1])
        ax.plot(iterations, sizes, "o-", label=short, color=color, linewidth=1.5, markersize=5)

    ax.set_xlabel("Iteration", fontsize=11)
    ax.set_ylabel("Size (MB)", fontsize=11)
    ax.set_title("Individual Image Sizes Over Iterations", fontsize=13, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.grid(True, alpha=0.3)


def plot_savings_waterfall(ax, results: list[dict]):
    """Waterfall chart showing cumulative savings per iteration."""
    if len(results) < 2:
        ax.text(0.5, 0.5, "Need 2+ iterations\nfor savings chart",
                ha="center", va="center", fontsize=12, transform=ax.transAxes)
        ax.set_title("Savings Per Iteration", fontsize=13, fontweight="bold")
        return

    labels = []
    deltas = []
    for i in range(1, len(results)):
        delta = results[i]["total_mb"] - results[i - 1]["total_mb"]
        labels.append(results[i].get("label", f"iter-{i}"))
        deltas.append(delta)

    colors = ["#2ca02c" if d < 0 else "#d62728" for d in deltas]
    x = range(len(deltas))

    ax.bar(x, [-d for d in deltas], color=colors, alpha=0.8)

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=8)
    ax.set_ylabel("Savings (MB)", fontsize=11)
    ax.set_title("Size Change Per Iteration", fontsize=13, fontweight="bold")
    ax.axhline(y=0, color="black", linewidth=0.5)
    ax.grid(True, alpha=0.3, axis="y")


def main():
    results = load_results()

    if not results:
        print("No results to plot.")
        sys.exit(1)

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(
        "Docker Image Size Optimization Progress",
        fontsize=16, fontweight="bold", y=0.98,
    )

    plot_total_over_iterations(axes[0, 0], results)
    plot_per_image_comparison(axes[0, 1], results)
    plot_size_breakdown(axes[1, 0], results)
    plot_savings_waterfall(axes[1, 1], results)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(OUTPUT_FILE, dpi=150, bbox_inches="tight")
    print(f"Plot saved to {OUTPUT_FILE}")

    # Also print a text summary
    if len(results) >= 2:
        baseline = results[0]["total_mb"]
        best = min(r["total_mb"] for r in results if r["total_mb"] > 0)
        saved = baseline - best
        pct = (saved / baseline) * 100 if baseline > 0 else 0
        print(f"\nSummary: {baseline:.0f} MB -> {best:.0f} MB ({saved:.0f} MB saved, {pct:.1f}% reduction)")


if __name__ == "__main__":
    main()
