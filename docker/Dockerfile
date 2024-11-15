ARG PYTHON_VERSION=3.10.14
FROM python:${PYTHON_VERSION} AS builder

LABEL maintainer="Wei Lee <mai@mai0313.com>" \
    org.label-schema.name="llm_discord_bot" \
    org.label-schema.vendor="Wei Lee" \
    org.label-schema.schema-version="1.0" \
    com.centurylinklabs.watchtower.stop-signal="SIGINT"

# Install git
RUN apt-get -y update && apt-get install -y git make
RUN git config --global http.sslVerify false

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install python packages
COPY ./docker/mirror/pip.conf /root/.pip/pip.conf
RUN python -m pip install --upgrade pip

########################################################################################

FROM builder AS base
WORKDIR /base_env
COPY ./requirements.lock ./requirements.lock
RUN pip install -r ./requirements.lock && pip cache purge

FROM builder AS dev
WORKDIR /base_env
COPY ./requirements-dev.lock ./requirements-dev.lock
RUN pip install -r ./requirements-dev.lock && pip cache purge

########################################################################################

FROM base AS bot
WORKDIR /app
COPY . .
