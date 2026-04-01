#!/usr/bin/env python3
"""
Build Docker images with podman and measure their sizes.
Records results to results.json.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RESULTS_FILE = Path(__file__).parent / "results.json"
BUILD_CONTEXT = Path(__file__).parent / "containers"

# Image build specs: (name, dockerfile_path relative to build context)
IMAGES = [
    ("reduce-docker/base", "base/Dockerfile"),
    ("reduce-docker/datascience", "datascience/Dockerfile"),
    ("reduce-docker/deeplearning", "deeplearning/Dockerfile"),
    ("reduce-docker/jupyterhub-datascience", "jupyterhub/datascience/Dockerfile"),
    ("reduce-docker/jupyterhub-deeplearning", "jupyterhub/deeplearning/Dockerfile"),
]

# Build dependency order: child images need parent tags
BUILD_DEPS = {
    "reduce-docker/datascience": "reduce-docker/base",
    "reduce-docker/deeplearning": "reduce-docker/base",
    "reduce-docker/jupyterhub-datascience": "reduce-docker/datascience",
    "reduce-docker/jupyterhub-deeplearning": "reduce-docker/deeplearning",
}


def run_cmd(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"  $ {' '.join(cmd)}")
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def build_image(name: str, dockerfile: str) -> bool:
    """Build a single image with podman. Returns True on success."""
    print(f"\n{'='*60}")
    print(f"Building: {name}")
    print(f"Dockerfile: {dockerfile}")
    print(f"{'='*60}")

    # Determine build args for parent image override
    build_args = []
    if name in BUILD_DEPS:
        parent = BUILD_DEPS[name]
        build_args = ["--build-arg", f"BASE_IMG={parent}"]

    cmd = [
        "podman", "build",
        "--format", "docker",
        "-t", name,
        "-f", str(BUILD_CONTEXT / dockerfile),
        *build_args,
        str(BUILD_CONTEXT),
    ]

    result = run_cmd(cmd, check=False)
    if result.returncode != 0:
        print(f"FAILED to build {name}:")
        print(result.stderr[-2000:] if len(result.stderr) > 2000 else result.stderr)
        return False

    print(f"Successfully built {name}")
    return True


def get_image_size(name: str) -> float | None:
    """Get image size in MB using podman inspect."""
    result = run_cmd(
        ["podman", "image", "inspect", name, "--format", "{{.Size}}"],
        check=False,
    )
    if result.returncode != 0:
        return None
    try:
        size_bytes = int(result.stdout.strip())
        return round(size_bytes / (1024 * 1024), 2)
    except (ValueError, IndexError):
        return None


def load_results() -> list[dict]:
    """Load existing results from JSON file."""
    if RESULTS_FILE.exists():
        return json.loads(RESULTS_FILE.read_text())
    return []


def save_results(results: list[dict]) -> None:
    """Save results to JSON file."""
    RESULTS_FILE.write_text(json.dumps(results, indent=2) + "\n")


def resolve_with_deps(images_to_build: list[str]) -> list[str]:
    """Expand a list of image names to include all transitive dependencies."""
    needed = set(images_to_build)
    changed = True
    while changed:
        changed = False
        for img in list(needed):
            parent = BUILD_DEPS.get(img)
            if parent and parent not in needed:
                needed.add(parent)
                changed = True
    # Return in IMAGES order so parents are built before children
    return [name for name, _ in IMAGES if name in needed]


def measure(
    images_to_build: list[str] | None = None,
    label: str = "",
    build: bool = True,
) -> dict:
    """
    Build and measure image sizes.

    Args:
        images_to_build: List of image names to build (None = all).
            Dependency images are always built first automatically.
        label: Label for this measurement (e.g., "baseline", optimization description).
        build: Whether to build images before measuring.

    Returns:
        Measurement record dict.
    """
    targets = IMAGES
    if images_to_build:
        resolved = resolve_with_deps(images_to_build)
        targets = [(n, d) for n, d in IMAGES if n in resolved]

    sizes = {}
    build_status = {}
    start_time = time.time()

    if build:
        for name, dockerfile in targets:
            success = build_image(name, dockerfile)
            build_status[name] = "success" if success else "failed"
    else:
        for name, _ in targets:
            build_status[name] = "skipped"

    # Measure all images (even if we only built some)
    for name, _ in IMAGES:
        size = get_image_size(name)
        if size is not None:
            sizes[name] = size

    elapsed = round(time.time() - start_time, 1)
    total_size = round(sum(sizes.values()), 2) if sizes else 0

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "label": label or "measurement",
        "sizes_mb": sizes,
        "total_mb": total_size,
        "build_status": build_status,
        "elapsed_seconds": elapsed,
    }

    # Append to results
    results = load_results()
    record["iteration"] = len(results)
    results.append(record)
    save_results(results)

    # Print summary
    print(f"\n{'='*60}")
    print(f"MEASUREMENT SUMMARY (iteration {record['iteration']})")
    print(f"Label: {record['label']}")
    print(f"{'='*60}")
    for name, size in sizes.items():
        status = build_status.get(name, "pre-existing")
        print(f"  {name:45s} {size:>10.2f} MB  [{status}]")
    print(f"  {'TOTAL':45s} {total_size:>10.2f} MB")
    print(f"  Build time: {elapsed}s")
    print(f"{'='*60}\n")

    return record


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build and measure Docker image sizes")
    parser.add_argument(
        "--label", "-l",
        default="",
        help="Label for this measurement",
    )
    parser.add_argument(
        "--images", "-i",
        nargs="*",
        default=None,
        help="Specific images to build (default: all)",
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="Skip building, just measure existing images",
    )
    parser.add_argument(
        "--base-only",
        action="store_true",
        help="Only build the base image",
    )
    args = parser.parse_args()

    images = args.images
    if args.base_only:
        images = ["reduce-docker/base"]

    measure(images_to_build=images, label=args.label, build=not args.no_build)


if __name__ == "__main__":
    main()
