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
        "cuda-toolkit~=12.4" \
    && mamba clean --all -f -y \
    && sudo mkdir -p /usr/local/cuda \
    && sudo ln -s /opt/conda/* /usr/local/cuda/ \
    && python3 -m pip install --no-cache-dir -r "${REQUIREMENTS_DIR}/ai-ml_pip.txt"


# ----------------------------
#         Final Setup
# ----------------------------
USER ${NB_UID}
WORKDIR "${HOME}"
