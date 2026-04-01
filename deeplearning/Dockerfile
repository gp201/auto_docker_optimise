ARG OWNER=brineylab
ARG BASE_IMG=$OWNER/base
FROM $BASE_IMG

# This image was initially created by the Jupyter Development Team:
# https://github.com/jupyter/docker-stacks
# and was subsequently modified and maintained by the Briney Lab.
LABEL maintainer='Briney Lab @ Scripps Research <briney@scripps.edu>'

# In alignment with the licensing of the orignal image created
# by the Jupyter Development Team, this image is distributed
# under the terms of the Modified BSD License.
# https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license


# ----------------------------
#         CUDA Setup
# ----------------------------
USER root

# NVIDIA configs
ENV NVIDIA_VISIBLE_DEVICES='all'
ENV NVIDIA_DRIVER_CAPABILITIES='compute,utility'
ENV PATH="${PATH}:/usr/local/nvidia/bin" \
    LD_LIBRARY_PATH='/usr/local/nvidia/lib:/usr/local/nvidia/lib64'

# CUDA toolkit + AI/ML Packages
USER ${NB_UID}
COPY --chown=${NB_UID}:${NB_GID} ./requirements/ai-ml_pip.txt ${REQUIREMENTS_DIR}/ai-ml_pip.txt
RUN rm -rf "/home/${NB_USER}/.cache/" \
    && mamba install --yes -c nvidia \
        "cuda-runtime~=12.4" \
        "cuda-nvcc~=12.4" \
        "cuda-cudart-dev~=12.4" \
        "cuda-libraries~=12.4" \
    && mamba clean --all -f -y \
    && sudo mkdir -p /usr/local/cuda \
    && sudo ln -s /opt/conda/* /usr/local/cuda/ \
    && python3 -m pip install --no-cache-dir -r "${REQUIREMENTS_DIR}/ai-ml_pip.txt" \
    && find "${CONDA_DIR}" -name '*.a' -delete \
    && find "${CONDA_DIR}" -name '*.pyc' -delete \
    && find "${CONDA_DIR}" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true \
    && find "${CONDA_DIR}/lib/python3.12/site-packages" -type d \( -name 'tests' -o -name 'test' \) -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf "${CONDA_DIR}/lib/python3.12/site-packages/torch/include" \
    && rm -rf "${CONDA_DIR}/pkgs" \
    && sudo apt-get update -qq && sudo apt-get install -y -qq --no-install-recommends binutils \
    && find "${CONDA_DIR}" -name '*.so' -exec strip --strip-unneeded {} + 2>/dev/null || true \
    && find "${CONDA_DIR}" -name '*.so.*' -exec strip --strip-unneeded {} + 2>/dev/null || true \
    && sudo apt-get purge -y binutils && sudo apt-get autoremove -y && sudo rm -rf /var/lib/apt/lists/* \
    && rm -rf "${CONDA_DIR}/share/doc" "${CONDA_DIR}/share/man" "${CONDA_DIR}/share/gtk-doc" \
    && rm -rf "${CONDA_DIR}/targets/x86_64-linux/lib/stubs" \
    && rm -rf "${CONDA_DIR}/targets/x86_64-linux/include" \
    && rm -rf "${CONDA_DIR}/include/cuda" "${CONDA_DIR}/include/cub" \
    && find "${CONDA_DIR}" -name 'libnvrtc.alt*' -delete \
    && find "${CONDA_DIR}" -name 'libnvrtc-builtins.alt*' -delete \
    && find "${CONDA_DIR}" -name 'libnppi*.so*' -delete \
    && find "${CONDA_DIR}" -name 'libnppc*.so*' -delete \
    && find "${CONDA_DIR}" -name 'libnpps*.so*' -delete \
    && find "${CONDA_DIR}" -name 'libcusolverMg*.so*' -delete


# ----------------------------
#         Final Setup
# ----------------------------
USER ${NB_UID}
WORKDIR "${HOME}"
