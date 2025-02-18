ARG PYTHON_VERSION=3.10.14
FROM python:${PYTHON_VERSION} AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

LABEL maintainer="Wei Lee <mai@mai0313.com>" \
    org.label-schema.name="llm_discord_bot" \
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
COPY ./docker/mirror/pip.conf /root/.pip/pip.conf
RUN git config --global http.sslVerify false && \
    python -m pip install --upgrade pip

########################################################################################

FROM builder AS base
WORKDIR /base
COPY ./pyproject.toml ./pyproject.toml
# RUN uv sync --frozen --no-dev && uv cache clean
RUN uv export --no-dev --no-hashes --output-file ./requirements.lock && \
    pip install -r ./requirements.lock && \
    pip cache purge

FROM builder AS dev
WORKDIR /base
COPY ./pyproject.toml ./pyproject.toml
# RUN uv sync --frozen && uv cache clean
RUN uv export --no-hashes --group docs --output-file ./requirements-dev.lock && \
    pip install -r ./requirements-dev.lock && \
    pip cache purge

########################################################################################

FROM base AS prod
WORKDIR /app
COPY . .

FROM dev AS docs
WORKDIR /app
COPY . .
RUN make gen-docs
