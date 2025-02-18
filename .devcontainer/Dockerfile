ARG PYTHON_VERSION=3.10.14
FROM python:${PYTHON_VERSION} AS builder

LABEL maintainer="Wei Lee <mai@mai0313.com>" \
    org.label-schema.name="repo-template" \
    org.label-schema.vendor="Wei Lee" \
    org.label-schema.schema-version="1.0" \
    com.centurylinklabs.watchtower.stop-signal="SIGINT"

# Install git, Node.js, and other dependencies
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends git make curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install python packages
RUN git config --global http.sslVerify false && \
    python -m pip install --upgrade pip

RUN curl -sSf https://rye.astral.sh/get | RYE_INSTALL_OPTION="--yes" bash && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    echo "export PATH='$HOME/.local/bin:$PATH'" >> ~/.bashrc && \
    echo "source '$HOME/.rye/env'" >> ~/.bashrc
