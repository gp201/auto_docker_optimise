# auto_docker_optimise

This is an experiment to have the LLM autonomously reduce Docker image sizes.

## Session Tracking

This project uses [entire.io](https://entire.io/) to capture AI agent sessions alongside every commit. Each optimization commit is automatically paired with the full agent conversation that produced it. Entire integrates with Claude Code automatically — no extra steps needed per session.

## Setup

To set up a new optimization run, work with the user to:

1. **Agree on a run tag**: propose a tag based on today's date (e.g. `apr1`). The branch `optimize/<tag>` must not already exist — this is a fresh run.
2. **Create the branch**: `git checkout -b optimize/<tag>` from current main.
3. **Read the in-scope files**: Read these files for full context:
   - `program.md` — this file, the experiment protocol.
   - `base/Dockerfile` — base image (Ubuntu 24.04 + micromamba + R + scipy + abx).
   - `datascience/Dockerfile` — base + NGS tools (bcl2fastq2, CellRanger, dorado, etc.).
   - `deeplearning/Dockerfile` — base + CUDA 12.4 + AI/ML packages.
   - `jupyterhub/datascience/Dockerfile` — datascience + JupyterLab/Hub.
   - `jupyterhub/deeplearning/Dockerfile` — deeplearning + JupyterLab/Hub.
   - `requirements/*.txt` — all package specification files.
   - `scripts/measure.py` — fixed build/measurement script. Do not modify.
   - `scripts/optimize.py` — fixed ratchet loop script. Do not modify.
4. **Verify symlink exists**: Check that `scripts/containers` symlink points to `..`. If not: `ln -s .. scripts/containers` from repo root.
5. **Establish baseline**: Run `cd scripts && python measure.py --label "baseline"` to build all images and record initial sizes.
6. **Confirm and go**: Confirm setup looks good.

Once you get confirmation, kick off the experimentation.

## Experimentation

Each experiment builds all 5 Docker images using `podman build`. You launch measurement simply as: `cd scripts && python measure.py --label "description"`.

**What you CAN do:**
- Modify Dockerfiles — `base/Dockerfile`, `datascience/Dockerfile`, `deeplearning/Dockerfile`, `jupyterhub/datascience/Dockerfile`, `jupyterhub/deeplearning/Dockerfile`.
- Modify requirements files — everything under `requirements/`.
- Add `.dockerignore` files, helper scripts used during build, or multi-stage build patterns.

**What you CANNOT do:**
- Modify `scripts/measure.py`, `scripts/optimize.py`, `scripts/plot.py`, or `program.md`. They are read-only.
- Remove packages or tools. Every package, tool, and capability must remain available.
- Install new system-level dependencies on the host.

**The goal is simple: get the lowest total combined image size in MB.** Everything is fair game: multi-stage builds, layer combining, cache cleanup, smaller base images, build-time dependency removal. The only constraint is that all 5 images build successfully and all packages remain available.

**Simplicity criterion**: All else being equal, simpler is better. A small size reduction that adds ugly complexity is not worth it. Conversely, removing unnecessary layers and getting equal or better results is a great outcome — that's a simplification win. When evaluating whether to keep a change, weigh the complexity cost against the size savings.

**The first run**: Your very first run should always be to establish the baseline, so you will run `python measure.py --label "baseline"` as is.

## Image Hierarchy

```
reduce-docker/base  (Ubuntu 24.04 + micromamba + Python 3.12 + R + scipy + abx)
├── reduce-docker/datascience  (base + NGS tools + IgDiscover)
│   └── reduce-docker/jupyterhub-datascience  (datascience + JupyterLab/Hub)
└── reduce-docker/deeplearning  (base + CUDA 12.4 + AI/ML packages)
    └── reduce-docker/jupyterhub-deeplearning  (deeplearning + JupyterLab/Hub)
```

Images are built in dependency order automatically by `measure.py`.

## Output format

Once `measure.py` finishes it prints a summary like this:

```
============================================================
MEASUREMENT SUMMARY (iteration 0)
Label: baseline
============================================================
  reduce-docker/base                            1234.56 MB  [success]
  reduce-docker/datascience                     2345.67 MB  [success]
  reduce-docker/deeplearning                    3456.78 MB  [success]
  reduce-docker/jupyterhub-datascience          2567.89 MB  [success]
  reduce-docker/jupyterhub-deeplearning         3678.90 MB  [success]
  TOTAL                                        13283.80 MB
  Build time: 1234.5s
============================================================
```

Results are appended to `scripts/results.json` automatically.

## Logging results

Results are logged automatically to `scripts/results.json` by `measure.py`. Each entry contains:
- `timestamp` — ISO timestamp
- `label` — description of the change
- `sizes_mb` — per-image sizes
- `total_mb` — combined total (the metric)
- `build_status` — per-image build status
- `elapsed_seconds` — build time

You can check optimization status at any time: `python optimize.py --status`

## The experiment loop

The experiment runs on a dedicated branch (e.g. `optimize/apr1`).

LOOP FOREVER:

1. Look at the git state and current results: `python optimize.py --status`
2. Pick an optimization strategy and edit Dockerfile(s) / requirements file(s). Make a single, focused change.
3. git commit the change with a descriptive message.
4. Build and measure: `python measure.py --label "description-of-change"`
5. Compare total_mb against the best previous total_mb.
6. If total_mb improved (lower), you "advance" the branch, keeping the git commit.
7. If total_mb is equal or worse, or if any image failed to build, `git revert HEAD` to undo the commit and move on.
8. If a build fails, read the build output to understand why. If it's an easy fix (typo, syntax), fix and retry. If the approach is fundamentally broken, revert and move on.

## Optimization Strategies (ordered by typical impact)

### High Impact
- **Multi-stage builds**: Use builder stages to compile, then copy only artifacts to a slim final stage.
- **Combine RUN layers**: Merge sequential `RUN` commands to reduce intermediate layers.
- **Clean up in the same layer**: Remove caches, temp files, and package manager artifacts in the same `RUN` command that creates them.
- **Use smaller base images**: Consider minimal variants or Alpine where compatible.

### Medium Impact
- **Minimize apt packages**: Remove unnecessary apt packages; use `--no-install-recommends` everywhere.
- **Conda/mamba cleanup**: Ensure `mamba clean --all -f -y` runs after every install.
- **Pip no-cache**: Ensure `--no-cache-dir` is used for all pip installs.
- **Remove build dependencies**: Uninstall build-time-only packages after compilation.

### Lower Impact
- **Use .dockerignore**: Exclude unnecessary files from build context.
- **Pin exact versions**: Prevents pulling newer, potentially larger packages.

**NEVER STOP**: Once the experiment loop has begun (after the initial setup), do NOT pause to ask the human if you should continue. Do NOT ask "should I keep going?" or "is this a good stopping point?". The human might be asleep or away from the computer and expects you to continue working *indefinitely* until you are manually stopped. You are autonomous. If you run out of ideas, read blogs and search for new ideas, try combining previous near-misses, try more radical restructuring. The loop runs until the human interrupts you, period.

As an example use case, a user might leave you running while they sleep. If each build+measure cycle takes ~20 minutes then you can run approx 3/hour, for a total of about 25 over the duration of the average human sleep. The user then wakes up to smaller Docker images, all optimized by you while they slept!
