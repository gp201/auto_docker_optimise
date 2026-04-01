# This image was initially created by the Jupyter Development Team:
# https://github.com/jupyter/docker-stacks/tree/main/images/docker-stacks-foundation
# and was subsequently modified by the Briney Lab.

# In alignment with the licensing of the orignal image created
# by the Jupyter Development Team, this image is distributed
# under the terms of the Modified BSD License.
# https://en.wikipedia.org/wiki/BSD_licenses#3-clause_license

# The default base image is Ubuntu 24.04 (noble)
# https://hub.docker.com/_/ubuntu/tags?page=1&name=noble

ARG BASE_IMG=ubuntu:24.04
FROM $BASE_IMG

ARG OWNER=brineylab
LABEL maintainer='Briney Lab @ Scripps Research <briney@scripps.edu>'

# NB user
ARG NB_USER="jovyan"
ARG NB_UID="1000"
ARG NB_GID="100"

# Python version
ARG PYTHON_VERSION=3.12

# Environmental variables
ENV DEBIAN_FRONTEND=noninteractive \
    CONDA_DIR=/opt/conda \
    SHELL=/bin/bash \
    NB_USER=${NB_USER} \
    NB_UID=${NB_UID} \
    NB_GID=${NB_GID} \
    LC_ALL=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8
ENV PATH="${CONDA_DIR}/bin:${PATH}"
ENV HOME="/home/${NB_USER}"
ENV REQUIREMENTS_DIR="${HOME}/.requirements"

# Fix: https://github.com/hadolint/hadolint/wiki/DL4006
# Fix: https://github.com/koalaman/shellcheck/wiki/SC3014
SHELL ["/bin/bash", "-o", "pipefail", "-c"]


# ----------------------------
#       OS dependencies
# ----------------------------
USER root
RUN apt-get update --yes \
    # - apt-get upgrade is run to patch known vulnerabilities in apt-get packages as
    #   the ubuntu base image is rebuilt too seldom sometimes (less than once a month)
    && apt-get upgrade --yes \
    && apt-get install --yes --no-install-recommends \
        # - bzip2 is necessary to extract the micromamba executable.
        bzip2 \
        ca-certificates \
        locales \
        # - `netbase` provides /etc/{protocols,rpc,services}, part of POSIX
        #   and required by various C functions like getservbyname and getprotobyname
        #   https://github.com/jupyter/docker-stacks/pull/2129
        netbase \
        sudo \
        # - tini is installed as a helpful container entrypoint that reaps zombie
        #   processes and such of the actual executable we want to start, see
        #   https://github.com/krallin/tini#why-tini for details.
        tini \
        wget \
        # - additional apt packages beyond those in the original Jupyter dockerfile
        bash \
        bashtop \
        btop \
        curl \
        htop \
        nano \
        nfs-common \
        openssh-server \
        pigz \
        screen \
        tmux \
        traceroute \
        unzip \
        vim \
        zip \
        gnupg \
        gnupg2 \
        # for cython: https://cython.readthedocs.io/en/latest/src/quickstart/install.html
        build-essential \
        # for latex labels (cm-super removed - uses Type1 fonts, very large)
        dvipng \
        # for matplotlib anim
        ffmpeg \
        fonts-liberation \
        git \
        # less is needed to run help in R
        # see: https://github.com/jupyter/docker-stacks/issues/1588
        less \
        openssh-client \
        # - pandoc is used to convert notebooks to html files
        #   it's not present in aarch64 ubuntu image, so we install it here
        pandoc \
        # - run-one - a wrapper script that runs no more
        #   than one unique  instance  of  some  command with a unique set of arguments,
        #   we use `run-one-constantly` to support `RESTARTABLE` option
        run-one \
        # nbconvert dependencies
        # https://nbconvert.readthedocs.io/en/latest/install.html#installing-tex
        texlive-xetex \
        texlive-fonts-recommended \
        texlive-plain-generic \
        tzdata \
        # Enable clipboard on Linux host systems
        xclip \
        # R pre-requisites
        fonts-dejavu \
        gfortran \
        gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /usr/share/doc /usr/share/info \
    && find /usr/share/man -type f -delete \
    && rm -rf /usr/share/texlive/texmf-dist/doc \
    && rm -rf /usr/share/texmf/doc \
    && echo "en_US.UTF-8 UTF-8" > /etc/locale.gen \
    && locale-gen


# ----------------------------
#       User Setup
# ----------------------------
# Copy script to fix permissions
COPY --chown=${NB_UID}:${NB_GID} ./base/fix-permissions /usr/local/bin/fix-permissions
RUN chmod a+rx /usr/local/bin/fix-permissions

# Enable prompt color in the skeleton .bashrc before creating the default NB_USER
RUN sed -i 's/^#force_color_prompt=yes/force_color_prompt=yes/' /etc/skel/.bashrc && \
    # More information in: https://github.com/jupyter/docker-stacks/pull/2047
    # and docs: https://docs.conda.io/projects/conda/en/latest/dev-guide/deep-dives/activation.html
    echo 'eval "$(conda shell.bash hook)"' >> /etc/skel/.bashrc

# Delete existing user with UID="${NB_UID}" if it exists
# hadolint ignore=SC2046
RUN if grep -q "${NB_UID}" /etc/passwd; then \
        userdel --remove $(id -un "${NB_UID}"); \
    fi

# Create NB_USER with name jovyan user with UID=1000 and in the 'users' group
# Make sure these dirs are writable by the `users` group
# Grant sudo and add password
RUN echo "auth requisite pam_deny.so" >> /etc/pam.d/su \
    && sed -i.bak -e 's/^%admin/#%admin/' /etc/sudoers \
    && sed -i.bak -e 's/^%sudo/#%sudo/' /etc/sudoers \
    && useradd -l -m -s /bin/bash -N -u "${NB_UID}" "${NB_USER}" \
    && mkdir -p "${CONDA_DIR}" \
    && chown "${NB_USER}:${NB_GID}" "${CONDA_DIR}" \
    && chmod g+w /etc/passwd \
    && fix-permissions "${HOME}" \
    && fix-permissions "${CONDA_DIR}" \
    && usermod -aG sudo ${NB_USER} \
    && echo "${NB_USER}  ALL=(ALL) NOPASSWD:ALL" | tee /etc/sudoers.d/${NB_USER} \
    && rm -rf "/home/${NB_USER}/.cache/"


# ----------------------------
#         Micromamba
# ----------------------------
# Download and install Micromamba, and initialize Conda prefix.
#   <https://github.com/mamba-org/mamba#micromamba>
#   Similar projects using Micromamba:
#     - Micromamba-Docker: <https://github.com/mamba-org/micromamba-docker>
#     - repo2docker: <https://github.com/jupyterhub/repo2docker>
USER ${NB_UID}
COPY --chown="${NB_UID}:${NB_GID}" ./base/initial-condarc "${CONDA_DIR}/.condarc"
WORKDIR /tmp
RUN set -x \
    && arch=$(uname -m) \
    && if [ "${arch}" = "x86_64" ]; then \
        # Should be simpler, see <https://github.com/mamba-org/mamba/issues/1437>
        arch="64"; \
    fi \
    # https://mamba.readthedocs.io/en/latest/installation/micromamba-installation.html#linux-and-macos
    && wget --progress=dot:giga -O - \
        "https://micro.mamba.pm/api/micromamba/linux-${arch}/latest" | tar -xvj bin/micromamba \
    && PYTHON_SPECIFIER="python=${PYTHON_VERSION}" \
    && if [[ "${PYTHON_VERSION}" == "default" ]]; then PYTHON_SPECIFIER="python"; fi \
    # Install the packages
    && ./bin/micromamba install \
        --root-prefix="${CONDA_DIR}" \
        --prefix="${CONDA_DIR}" \
        --yes \
        'jupyter_core' \
        'conda' \
        'mamba' \
        "${PYTHON_SPECIFIER}" \
    && rm -rf /tmp/bin/ \
    # Pin major.minor version of python
    # https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-pkgs.html#preventing-packages-from-updating-pinning
    && mamba list --full-name 'python' | awk 'END{sub("[^.]*$", "*", $2); print $1 " " $2}' >> "${CONDA_DIR}/conda-meta/pinned" \
    && mamba clean --all -f -y \
    && mkdir -p ${REQUIREMENTS_DIR} \
    && mkdir -p "/home/${NB_USER}/work" \
    && rm -rf "/home/${NB_USER}/.cache/" \
    && fix-permissions "${CONDA_DIR}" \
    && fix-permissions "${REQUIREMENTS_DIR}" \
    && fix-permissions "/home/${NB_USER}"


#-----------------
#      SciPy
#-----------------
COPY --chown=${NB_UID}:${NB_GID} ./requirements/scipy_mamba.txt ${REQUIREMENTS_DIR}/scipy_mamba.txt
COPY --chown=${NB_UID}:${NB_GID} ./requirements/abx_pip.txt ${REQUIREMENTS_DIR}/abx_pip.txt
COPY --chown=${NB_UID}:${NB_GID} ./requirements/r_mamba.txt ${REQUIREMENTS_DIR}/r_mamba.txt
COPY --chown=${NB_UID}:${NB_GID} ./requirements/r_cran.txt ${REQUIREMENTS_DIR}/r_cran.txt
RUN mamba install --yes --file "${REQUIREMENTS_DIR}/scipy_mamba.txt" \
    && mamba install --yes --file ${REQUIREMENTS_DIR}/r_mamba.txt \
    && mamba clean --all -f -y \
    #--- install CPU-only torch first (harmonypy depends on torch, avoid pulling CUDA libs) ---
    && python3 -m pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    #--- ab[x] and dependencies ---
    && python3 -m pip install --no-cache-dir -r ${REQUIREMENTS_DIR}/abx_pip.txt \
    && python3 -m pip install --no-cache-dir \
        "scab>=0.2.4" \
        abstar \
        abutils \
    #--- R: Bioconductor packages ---
    && Rscript -e "BiocManager::install(c('biomaRt', 'DESeq2'), ask = FALSE, update = FALSE)" \
    #--- R: CRAN packages ---
    && MAKEFLAGS="-j$(nproc)" Rscript -e "\
        pkgs <- scan('${REQUIREMENTS_DIR}/r_cran.txt', what = '', quiet = TRUE); \
        install.packages( \
            pkgs, \
            dependencies = TRUE, \
            repos = 'https://cran.rstudio.com' \
        )" \
    #--- cleanup ---
    && rm -rf "/home/${NB_USER}/.cache/" \
    && find "${CONDA_DIR}" -name '*.a' -delete \
    && find "${CONDA_DIR}" -name '*.pyc' -delete \
    && find "${CONDA_DIR}" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true \
    && find "${CONDA_DIR}/lib/python3.12/site-packages" -type d \( -name 'tests' -o -name 'test' \) -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf "${CONDA_DIR}/lib/python3.12/site-packages/torch/include" \
    && find "${CONDA_DIR}/lib/python3.12/site-packages/abutils/binaries" -name '*darwin*' -delete \
    && rm -rf "${CONDA_DIR}/pkgs" \
    && rm -rf "${CONDA_DIR}/share/doc" \
    && rm -rf "${CONDA_DIR}/share/man" \
    && rm -rf "${CONDA_DIR}/share/gtk-doc" \
    && rm -rf "${CONDA_DIR}/man" \
    && rm -rf "${CONDA_DIR}/share/info" \
    && rm -rf "${CONDA_DIR}/share/locale" \
    && rm -rf "${CONDA_DIR}/lib/R/doc" \
    && find "${CONDA_DIR}/lib/R/library" -type d -name "help" -exec rm -rf {} + 2>/dev/null || true \
    && find "${CONDA_DIR}/lib/R/library" -type d -name "html" -exec rm -rf {} + 2>/dev/null || true \
    && find "${CONDA_DIR}/lib/R/library" -type d -name "demo" -exec rm -rf {} + 2>/dev/null || true \
    && find "${CONDA_DIR}" -name '*.so' -exec strip --strip-unneeded {} + 2>/dev/null || true \
    && rm -rf "${CONDA_DIR}/targets" \
    && rm -rf /opt/conda/libexec/gcc \
    && rm -rf /opt/conda/include \
    && rm -rf /opt/conda/x86_64-conda-linux-gnu/sysroot/lib64/locale \
    && rm -rf /opt/conda/x86_64-conda-linux-gnu/sysroot/lib64/gconv \
    && rm -f /opt/conda/bin/x86_64-conda-linux-gnu-* \
    && rm -rf /opt/conda/x86_64-conda-linux-gnu/sysroot/usr \
    && fix-permissions "${CONDA_DIR}" \
    && fix-permissions "/home/${NB_USER}"

# Remove build-time-only system packages after all compilation is done
USER root
RUN apt-get purge -y --auto-remove \
        build-essential \
        gfortran \
        gcc \
        g++ \
        cpp \
        make \
        dpkg-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# ----------------------------
#         Final Setup
# ----------------------------
USER ${NB_UID}
WORKDIR "${HOME}"

ENTRYPOINT ["tini", "--"]
CMD ["/bin/bash"]
