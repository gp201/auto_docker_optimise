# Docker Image Size Reduction - Autoresearch Program

## Session Tracking

This project uses [entire.io](https://entire.io/) to capture AI agent sessions alongside every commit. Each optimization commit is automatically paired with the full agent conversation that produced it, creating a searchable record of decisions and reasoning.

Entire integrates with Claude Code automatically — no extra steps needed per session.

## Goal

Iteratively reduce the size of Docker images in the `containers/` directory using automated optimization techniques. The primary metric is **total image size in MB** (lower is better).

## Image Hierarchy

```
base (Ubuntu 24.04 + conda/mamba + R + scipy + abx packages)
├── datascience (base + NGS tools + IgDiscover)
│   └── jupyterhub/datascience (datascience + JupyterLab/Hub)
└── deeplearning (base + CUDA 12.4 + AI/ML packages)
    └── jupyterhub/deeplearning (deeplearning + JupyterLab/Hub)
```

## Rules

1. **Only edit Dockerfiles and requirements files** in `containers/`. Do not modify `measure.py`, `optimize.py`, `plot.py`, or `program.md`. Note: `containers/` is a **git submodule** — changes must be committed and merged in that submodule's repository.
2. **Preserve all functionality.** Every package, tool, and capability must remain available. Do not remove packages or tools.
3. **Images must build successfully** with `podman build`.
4. **Measure before and after.** Use `measure.py` to record image sizes after each change.
5. **One optimization per iteration.** Make a single, focused change per round so we can attribute size savings.
6. **Revert if size increases or build fails.** Use `git reset --hard HEAD` to revert bad changes.
7. **Commit improvements.** If size decreases, commit the change with a message describing the optimization. Entire.io will automatically capture the agent session alongside the commit.

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

The single metric is **total combined image size** across all successfully built images, measured in MB.
The `measure.py` script records this to `results.json` after each build.

## Workflow (Ratchet Loop)

```
1. measure baseline sizes → record in results.json
2. pick an optimization strategy
3. edit Dockerfile(s) / requirements file(s)
4. build with podman
5. measure new sizes
6. if total_size < best_total_size:
     commit changes
     update best_total_size
   else:
     git reset --hard HEAD
7. repeat from step 2
```
