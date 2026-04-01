# Docker Image Size Reduction - Autoresearch Program

## Session Tracking

This project uses [entire.io](https://entire.io/) to capture AI agent sessions alongside every commit. Each optimization commit is automatically paired with the full agent conversation that produced it, creating a searchable record of decisions and reasoning.

Entire integrates with Claude Code automatically — no extra steps needed per session.

## Goal

Iteratively reduce the size of Docker images using automated optimization techniques. The primary metric is **total image size in MB** (lower is better).

## Repository Structure

```
auto_docker_optimise/
├── base/                         # Base image (Ubuntu 24.04 + micromamba + R + scipy + abx)
│   ├── Dockerfile
│   ├── fix-permissions           # Permission setup script
│   └── initial-condarc           # Conda channel configuration
├── datascience/
│   └── Dockerfile                # base + NGS tools (bcl2fastq2, CellRanger, dorado, etc.)
├── deeplearning/
│   └── Dockerfile                # base + CUDA 12.4 + AI/ML packages
├── jupyterhub/
│   ├── datascience/
│   │   └── Dockerfile            # datascience + JupyterLab/Hub
│   ├── deeplearning/
│   │   └── Dockerfile            # deeplearning + JupyterLab/Hub
│   └── runtime/                  # Shared JupyterHub startup scripts and config
│       ├── docker_healthcheck.py
│       ├── jupyter_server_config.py
│       ├── Rprofile.site
│       ├── start-notebook.py
│       └── start-singleuser.py
├── requirements/                  # Package specification files
│   ├── scipy_mamba.txt           # Scientific computing (pandas, scipy, numba, etc.)
│   ├── abx_pip.txt               # Bioinformatics (anndata, scanpy, scvelo, etc.)
│   ├── ai-ml_pip.txt             # AI/ML (torch, jax, transformers, diffusers, etc.)
│   ├── jupyter_mamba.txt         # JupyterHub/Lab core packages
│   ├── jupyter-extensions_pip.txt # JupyterLab extensions + AI integrations
│   ├── r_mamba.txt               # R packages via conda
│   └── r_cran.txt                # R packages from CRAN
└── scripts/                       # Measurement and optimization tooling
    ├── measure.py                 # Builds images with podman, records sizes to results.json
    ├── optimize.py                # Ratchet loop: edit → build → keep/revert
    ├── plot.py                    # Plots optimization progress to progress.png
    └── results.json               # Created on first run; tracks all measurements
```

## Image Hierarchy

```
reduce-docker/base  (Ubuntu 24.04 + micromamba + Python 3.12 + R + scipy + abx)
├── reduce-docker/datascience  (base + NGS tools + IgDiscover)
│   └── reduce-docker/jupyterhub-datascience  (datascience + JupyterLab/Hub)
└── reduce-docker/deeplearning  (base + CUDA 12.4 + AI/ML packages)
    └── reduce-docker/jupyterhub-deeplearning  (deeplearning + JupyterLab/Hub)
```

## Build Context

The scripts in `scripts/` expect the container files to be accessible at `scripts/containers/`. Ensure a symlink exists:

```bash
ln -s .. scripts/containers   # run from repo root if not already present
```

Build and measurement commands should be run from the `scripts/` directory:

```bash
cd scripts
python measure.py --label "baseline"
python optimize.py --status
python plot.py
```

## Rules

1. **Only edit Dockerfiles and requirements files** in the repo (under `base/`, `datascience/`, `deeplearning/`, `jupyterhub/`, `requirements/`). Do not modify `scripts/measure.py`, `scripts/optimize.py`, `scripts/plot.py`, or `program.md`.
2. **Preserve all functionality.** Every package, tool, and capability must remain available. Do not remove packages or tools.
3. **Images must build successfully** with `podman build`.
4. **Measure before and after.** Use `scripts/measure.py` to record image sizes after each change. Results are appended to `scripts/results.json`.
5. **One optimization per iteration.** Make a single, focused change per round so we can attribute size savings.
6. **Revert if size increases or build fails.** Run `git checkout -- .` from the repo root to revert uncommitted changes, or let `optimize.py` handle it automatically.
7. **Commit improvements.** If size decreases, commit the change with a descriptive message. Entire.io will automatically capture the agent session alongside the commit.

## Optimization Strategies (ordered by typical impact)

### High Impact
- **Multi-stage builds**: Use builder stages to compile, then copy only artifacts to a slim final stage.
- **Combine RUN layers**: Merge sequential `RUN` commands to reduce intermediate layers.
- **Clean up in the same layer**: Remove caches, temp files, and package manager artifacts in the same `RUN` command that creates them.
- **Use smaller base images**: Consider `ubuntu:24.04` minimal variants or Alpine where compatible.

### Medium Impact
- **Minimize apt packages**: Remove unnecessary apt packages; use `--no-install-recommends` everywhere.
- **Conda/mamba cleanup**: Ensure `mamba clean --all -f -y` runs after every install.
- **Pip no-cache**: Ensure `--no-cache-dir` is used for all pip installs.
- **Remove build dependencies**: Uninstall build-time-only packages after compilation.
- **Optimize COPY order**: Place frequently changing files later to maximize cache hits.

### Lower Impact
- **Use .dockerignore**: Exclude unnecessary files from build context.
- **Compress downloaded archives**: Use pigz for parallel decompression.
- **Pin exact versions**: Prevents pulling newer, potentially larger packages.

## Metric

The single metric is **total combined image size** across all successfully built images, measured in MB. `scripts/measure.py` records this to `scripts/results.json` after each build.

## Workflow (Ratchet Loop)

```
1. measure baseline sizes:
     cd scripts && python measure.py --label "baseline"

2. pick an optimization strategy and edit Dockerfile(s) / requirements file(s)

3. build and measure:
     python measure.py --label "description-of-change"

4. if total_size < best_total_size:
     git add <changed files>
     git commit -m "optimize: description (saved X MB)"
   else:
     git checkout -- .   # revert

5. check progress:
     python optimize.py --status
     python plot.py

6. repeat from step 2
```

## Script Reference

| Script | Purpose | Key flags |
|---|---|---|
| `scripts/measure.py` | Build images and record sizes | `--label`, `--images`, `--no-build`, `--base-only` |
| `scripts/optimize.py` | Run ratchet loop automatically | `--baseline`, `--status`, `--iterations N`, `--base-only`, `--files` |
| `scripts/plot.py` | Plot optimization progress to `progress.png` | — |
