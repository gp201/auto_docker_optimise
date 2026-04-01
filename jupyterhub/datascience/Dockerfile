ARG OWNER=brineylab
ARG BASE_IMG=$OWNER/datascience
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
#       Mamba + Extensions
# ----------------------------
USER ${NB_UID}
WORKDIR /tmp
COPY --chown=${NB_UID}:${NB_GID} ./requirements/jupyter_mamba.txt ${REQUIREMENTS_DIR}/jupyter_mamba.txt
COPY --chown=${NB_UID}:${NB_GID} ./requirements/jupyter-extensions_pip.txt ${REQUIREMENTS_DIR}/jupyter-extensions_pip.txt
ENV JUPYTER_PORT=8888
EXPOSE $JUPYTER_PORT
RUN mamba install --yes --file "${REQUIREMENTS_DIR}/jupyter_mamba.txt" \
    && mamba clean --all -f -y \
    && python3 -m pip install --no-cache-dir -r "${REQUIREMENTS_DIR}/jupyter-extensions_pip.txt" \
    && jupyter server --generate-config \
    && jupyter server extension disable mercury_app \
    && jupyter lab clean \
    && npm cache clean --force \
    && rm -rf "/home/${NB_USER}/.cache/yarn" \
    && fix-permissions "${CONDA_DIR}" \
    && fix-permissions "/home/${NB_USER}"


# ----------------------------
#    Container Startup
# ----------------------------
# Copy local files as late as possible to avoid cache busting
USER ${NB_UID}
COPY ./jupyterhub/runtime/start-notebook.py ./jupyterhub/runtime/start-singleuser.py /usr/local/bin/
COPY ./jupyterhub/runtime/jupyter_server_config.py ./jupyterhub/runtime/docker_healthcheck.py /etc/jupyter/

# Fix permissions on /etc/jupyter as root
USER root
RUN fix-permissions /etc/jupyter/ \
    && rm -rf "/home/${NB_USER}/.cache/"

HEALTHCHECK --interval=3s --timeout=1s --start-period=3s --retries=3 \
    CMD /etc/jupyter/docker_healthcheck.py || exit 1

# Add R mimetype option to specify how the plot returns from R to the browser
USER ${NB_UID}
COPY --chown=${NB_UID}:${NB_GID} ./jupyterhub/runtime/Rprofile.site /opt/conda/lib/R/etc/


# ----------------------------
#         Final Setup
# ----------------------------
USER ${NB_UID}
WORKDIR "${HOME}"

# Configure container startup
ENTRYPOINT ["tini", "--"]
CMD ["start-notebook.py"]
