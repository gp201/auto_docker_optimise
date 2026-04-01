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

# OpenJDK version (required for NGS tools)
ARG openjdk_version="17"


# ----------------------------
#       OS dependencies + NGS TOOLS
# ----------------------------
USER root
ENV NGS_TOOLS_DIR="/tools"
WORKDIR /tmp
RUN apt-get update --yes \
    && apt-get install --yes --no-install-recommends \
        "openjdk-${openjdk_version}-jre-headless" \
        ca-certificates-java \
        libtool \
        libltdl-dev \
        automake \
        zlib1g-dev \
        libbz2-dev \
        pkg-config \
    #--- setup NGS dir ---
    && mkdir "${NGS_TOOLS_DIR}" \
    && chown "${NB_USER}" "${NGS_TOOLS_DIR}" \
    #--- bcl2fastq ---
    && cd "${NGS_TOOLS_DIR}" \
    && wget -q "https://burtonlab.s3.amazonaws.com/software/bcl2fastq2_0v2.20.0.422-2_amd64.deb" \
    && dpkg -i "bcl2fastq2_0v2.20.0.422-2_amd64.deb" \
    && rm "bcl2fastq2_0v2.20.0.422-2_amd64.deb" \
    #--- bases2fastq ---
    && wget -q "https://brineylab.s3.amazonaws.com/tools/bases2fastq-1.4.0.tar.gz" \
    && tar xzf "bases2fastq-1.4.0.tar.gz" \
    && rm "bases2fastq-1.4.0.tar.gz" \
    #--- FastQC ---
    && wget -q "http://burtonlab.s3.amazonaws.com/software/fastqc_v0.11.9.zip" \
    && unzip "fastqc_v0.11.9.zip" \
    && rm "fastqc_v0.11.9.zip" \
    && chmod +x "${NGS_TOOLS_DIR}/FastQC/fastqc" \
    && ln -s "${NGS_TOOLS_DIR}/FastQC/fastqc" "/usr/local/bin/fastqc" \
    #--- PANDAseq ---
    && git clone "https://github.com/neufeld/pandaseq" \
    && cd pandaseq \
    && ./autogen.sh \
    && ./configure \
    && make \
    && make install \
    && ldconfig \
    && cd "${NGS_TOOLS_DIR}" \
    #--- sickle (uses system zlib from zlib1g-dev) ---
    && git clone "https://github.com/najoshi/sickle" \
    && cd sickle \
    && make \
    && ln -s "${NGS_TOOLS_DIR}/sickle/sickle" "/usr/local/bin/sickle" \
    #--- CellRanger ---
    && cd "${NGS_TOOLS_DIR}" \
    && wget -q "https://brineylab.s3.amazonaws.com/tools/cellranger-8.0.1.tar" \
    && tar xf "cellranger-8.0.1.tar" \
    && rm "cellranger-8.0.1.tar" \
    && chmod -R 777 "${NGS_TOOLS_DIR}/cellranger-8.0.1" \
    && rm -rf "${NGS_TOOLS_DIR}/cellranger-8.0.1/external/cellranger_tiny_ref" \
    && rm -rf "${NGS_TOOLS_DIR}/cellranger-8.0.1/external/cellranger_tiny_fastq" \
    && find "${NGS_TOOLS_DIR}/cellranger-8.0.1" -name '*.a' -delete \
    && find "${NGS_TOOLS_DIR}/cellranger-8.0.1" -name '*.pyc' -delete \
    && find "${NGS_TOOLS_DIR}/cellranger-8.0.1" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true \
    && find "${NGS_TOOLS_DIR}/cellranger-8.0.1" -name '*.so' -exec strip --strip-unneeded {} + 2>/dev/null || true \
    && find "${NGS_TOOLS_DIR}/cellranger-8.0.1" -name '*.so.*' -exec strip --strip-unneeded {} + 2>/dev/null || true \
    #--- dorado ---
    && wget -q "https://brineylab.s3.amazonaws.com/tools/dorado-0.7.0-linux-x64.tar.gz" \
    && tar xzf "dorado-0.7.0-linux-x64.tar.gz" \
    && rm "dorado-0.7.0-linux-x64.tar.gz" \
    && chmod -R 777 "${NGS_TOOLS_DIR}/dorado-0.7.0-linux-x64" \
    && strip --strip-unneeded "${NGS_TOOLS_DIR}/dorado-0.7.0-linux-x64/lib/libdorado_torch_lib.so" 2>/dev/null || true \
    && strip --strip-unneeded "${NGS_TOOLS_DIR}/dorado-0.7.0-linux-x64/bin/dorado" 2>/dev/null || true \
    #--- cleanup build deps and caches ---
    && rm -rf "${NGS_TOOLS_DIR}/pandaseq" \
    && rm -rf "${NGS_TOOLS_DIR}/sickle/.git" \
    && apt-get purge -y libtool automake pkg-config \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf "/home/${NB_USER}/.cache/" \
    && fix-permissions "${NGS_TOOLS_DIR}" \
    && fix-permissions "/home/${NB_USER}"

WORKDIR "${NGS_TOOLS_DIR}"

# cutadapt + IgDiscover (conda-owned, must run as NB_UID)
USER ${NB_UID}
RUN python3 -m pip install --no-cache-dir "cutadapt" \
    && git clone "https://gitlab.com/gkhlab/igdiscover22.git" \
    && cd igdiscover22 \
    && sed '/- defaults/d' environment.yml > environment_no-default.yml \
    && mamba create -f environment_no-default.yml -n igdiscover \
    && mamba run -n igdiscover python3 -m pip install --no-cache-dir --no-deps -e . \
    && mamba run -n igdiscover python3 -m pip install --no-cache-dir "networkx==2.1" \
    && mamba clean --all -f -y \
    && find "${CONDA_DIR}" -name '*.a' -delete \
    && find "${CONDA_DIR}" -name '*.pyc' -delete \
    && find "${CONDA_DIR}" -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true \
    && rm -rf "${CONDA_DIR}/pkgs" \
    && find "${CONDA_DIR}" -name '*.so' -exec strip --strip-unneeded {} + 2>/dev/null || true \
    && fix-permissions "${CONDA_DIR}" \
    && fix-permissions "/home/${NB_USER}"

# update path with all tools
ENV PATH="${NGS_TOOLS_DIR}:${NGS_TOOLS_DIR}/cellranger-8.0.1/bin:${NGS_TOOLS_DIR}/dorado-0.7.0-linux-x64/bin:$PATH"


# ----------------------------
#         Final Setup
# ----------------------------
USER ${NB_UID}
WORKDIR "${HOME}"
