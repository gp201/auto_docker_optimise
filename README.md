# auto_docker_optimise

This repository uses AI to optimize Dockerfiles. It takes a Dockerfile as input and generates an optimized version of it, which can lead to smaller image sizes and faster build times.

## Usage
1. Clone the repository:
   ```bash
   git clone
    ```

2. Install the required dependencies:
   ```bash
    pip install -r requirements.txt
    ```

## containers submodule

The `containers/` directory is a **git submodule**. Changes to Dockerfiles and related files should be made in and merged into that submodule's repository, not directly in this repo.

## Why did I create this project?
Well I wanted to explore tools that can research and optimise code. I have been using Docker for a while and I know that optimizing Dockerfiles can lead to significant improvements in build times and image sizes. I wanted to see if I could use AI to automate this process and make it easier for developers to create optimised Dockerfiles.

TBH, in this project I'm using `podman`.
