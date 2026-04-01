#!/usr/bin/env python3
"""
Ratchet loop for Docker image size optimization.

Inspired by Karpathy's autoresearch: iteratively optimize Dockerfiles,
keep changes that reduce total image size, revert changes that don't.

Usage:
    python optimize.py                    # run optimization loop
    python optimize.py --iterations 10    # run 10 iterations
    python optimize.py --baseline         # just build and measure baseline
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from measure import IMAGES, BUILD_CONTEXT, measure, load_results

CONTAINERS_DIR = BUILD_CONTEXT
EDITABLE_FILES = []

# Collect all editable Dockerfiles and requirements files
for name, dockerfile in IMAGES:
    EDITABLE_FILES.append(CONTAINERS_DIR / dockerfile)
for req_file in (CONTAINERS_DIR / "requirements").glob("*.txt"):
    EDITABLE_FILES.append(req_file)


def git_commit(message: str) -> bool:
    """Commit all changes in containers/ with the given message."""
    result = subprocess.run(
        ["git", "add", "-A"],
        cwd=str(CONTAINERS_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=str(CONTAINERS_DIR),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def git_revert() -> bool:
    """Revert all uncommitted changes in containers/."""
    result = subprocess.run(
        ["git", "checkout", "--", "."],
        cwd=str(CONTAINERS_DIR),
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def git_diff() -> str:
    """Get the current diff in containers/."""
    result = subprocess.run(
        ["git", "diff", "--stat"],
        cwd=str(CONTAINERS_DIR),
        capture_output=True,
        text=True,
    )
    return result.stdout


def get_best_total() -> float | None:
    """Get the best (lowest) total size from results history."""
    results = load_results()
    if not results:
        return None
    totals = [r["total_mb"] for r in results if r["total_mb"] > 0]
    return min(totals) if totals else None


def print_status():
    """Print current optimization status."""
    results = load_results()
    if not results:
        print("No measurements yet. Run with --baseline first.")
        return

    baseline = results[0]
    latest = results[-1]
    best = min(results, key=lambda r: r["total_mb"] if r["total_mb"] > 0 else float("inf"))

    print(f"\n{'='*60}")
    print("OPTIMIZATION STATUS")
    print(f"{'='*60}")
    print(f"  Iterations:     {len(results)}")
    print(f"  Baseline total: {baseline['total_mb']:.2f} MB")
    print(f"  Current total:  {latest['total_mb']:.2f} MB")
    print(f"  Best total:     {best['total_mb']:.2f} MB (iteration {best['iteration']})")
    if baseline["total_mb"] > 0:
        reduction = baseline["total_mb"] - best["total_mb"]
        pct = (reduction / baseline["total_mb"]) * 100
        print(f"  Total saved:    {reduction:.2f} MB ({pct:.1f}%)")
    print(f"{'='*60}\n")

    # Per-image comparison
    if baseline.get("sizes_mb") and latest.get("sizes_mb"):
        print(f"  {'Image':<45s} {'Baseline':>10s} {'Current':>10s} {'Delta':>10s}")
        print(f"  {'-'*75}")
        for name in baseline["sizes_mb"]:
            base_size = baseline["sizes_mb"].get(name, 0)
            curr_size = latest["sizes_mb"].get(name, 0)
            delta = curr_size - base_size
            sign = "+" if delta > 0 else ""
            print(f"  {name:<45s} {base_size:>9.2f}M {curr_size:>9.2f}M {sign}{delta:>9.2f}M")
        print()


def print_editable_files():
    """Print the list of files that can be edited."""
    print("\nEditable files:")
    for f in EDITABLE_FILES:
        if f.exists():
            print(f"  {f.relative_to(CONTAINERS_DIR.parent)}")


def run_baseline(images: list[str] | None = None):
    """Build all images and record baseline measurements."""
    print("\n" + "=" * 60)
    print("BUILDING BASELINE")
    print("=" * 60)
    record = measure(images_to_build=images, label="baseline", build=True)
    git_commit(f"baseline: total {record['total_mb']:.2f} MB")
    print_status()


def run_iteration(iteration: int, images: list[str] | None = None) -> dict:
    """
    Run a single optimization iteration.

    This function:
    1. Records current best
    2. Builds and measures
    3. Keeps or reverts based on size comparison

    The actual Dockerfile edits should be made BEFORE calling this
    (either manually or by an AI agent).
    """
    best_before = get_best_total()
    diff = git_diff()

    if not diff.strip():
        print(f"\nIteration {iteration}: No changes detected, skipping.")
        return {}

    print(f"\n{'='*60}")
    print(f"ITERATION {iteration}")
    print(f"{'='*60}")
    print(f"Changes:\n{diff}")

    # Build and measure
    record = measure(
        images_to_build=images,
        label=f"iteration-{iteration}",
        build=True,
    )

    new_total = record["total_mb"]

    # Check for build failures
    failures = [k for k, v in record["build_status"].items() if v == "failed"]
    if failures:
        print(f"\nBuild FAILED for: {', '.join(failures)}")
        print("Reverting changes...")
        git_revert()
        return record

    # Compare with best
    if best_before is not None and new_total < best_before:
        saved = best_before - new_total
        pct = (saved / best_before) * 100
        print(f"\nIMPROVEMENT: {saved:.2f} MB saved ({pct:.1f}%)")
        print(f"  {best_before:.2f} MB -> {new_total:.2f} MB")
        git_commit(
            f"optimize: {record['label']} - {new_total:.2f} MB "
            f"(saved {saved:.2f} MB / {pct:.1f}%)"
        )
    elif best_before is not None:
        increase = new_total - best_before
        print(f"\nNO IMPROVEMENT: size increased by {increase:.2f} MB")
        print("Reverting changes...")
        git_revert()
    else:
        # First measurement, just commit
        git_commit(f"measure: {new_total:.2f} MB total")

    return record


def main():
    parser = argparse.ArgumentParser(
        description="Docker image size optimization ratchet loop"
    )
    parser.add_argument(
        "--baseline",
        action="store_true",
        help="Build and measure baseline only",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Print current optimization status",
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=1,
        help="Number of optimization iterations to run (default: 1)",
    )
    parser.add_argument(
        "--images", "-i",
        nargs="*",
        default=None,
        help="Specific images to build",
    )
    parser.add_argument(
        "--base-only",
        action="store_true",
        help="Only build the base image",
    )
    parser.add_argument(
        "--files",
        action="store_true",
        help="List editable files",
    )
    args = parser.parse_args()

    images = args.images
    if args.base_only:
        images = ["reduce-docker/base"]

    if args.files:
        print_editable_files()
        return

    if args.status:
        print_status()
        return

    if args.baseline:
        run_baseline(images)
        return

    # Run optimization iterations
    for i in range(1, args.iterations + 1):
        run_iteration(i, images)
        print_status()


if __name__ == "__main__":
    main()
