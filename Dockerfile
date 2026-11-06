# syntax=docker/dockerfile:1
# データを作る道具をまとめたイメージ。make build はこの中で動く

FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv

# tippecanoe は配布用のバイナリが無いので、実行するイメージと同じ OS でビルドする
FROM ghcr.io/osgeo/gdal:ubuntu-full-3.13.3@sha256:2dd0f81ef927ff4c3d4dbe4f73c029dc86d4073974c0564f8e196f6e1412e2e0 AS tippecanoe
ARG TIPPECANOE_VERSION=2.79.0
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential ca-certificates curl libsqlite3-dev zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*
RUN curl -fsSL "https://github.com/felt/tippecanoe/archive/refs/tags/${TIPPECANOE_VERSION}.tar.gz" | tar xz -C /tmp \
  && make -C "/tmp/tippecanoe-${TIPPECANOE_VERSION}" -j"$(nproc)" \
  && make -C "/tmp/tippecanoe-${TIPPECANOE_VERSION}" install PREFIX=/opt/tippecanoe

FROM ghcr.io/osgeo/gdal:ubuntu-full-3.13.3@sha256:2dd0f81ef927ff4c3d4dbe4f73c029dc86d4073974c0564f8e196f6e1412e2e0
ARG NODE_VERSION=24.22.2
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl git make xz-utils \
  && rm -rf /var/lib/apt/lists/*
RUN arch="$(dpkg --print-architecture)" \
  && case "$arch" in amd64) node_arch=x64 ;; arm64) node_arch=arm64 ;; *) exit 1 ;; esac \
  && curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-${node_arch}.tar.xz" | tar xJ -C /usr/local --strip-components=1
COPY --from=tippecanoe /opt/tippecanoe /usr/local
COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /opt/geojson
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund
COPY pyproject.toml uv.lock .python-version ./
ENV UV_PROJECT_ENVIRONMENT=/opt/geojson/.venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/bin/python3 \
    UV_LINK_MODE=copy
RUN uv sync --frozen --no-install-project
ENV PATH=/opt/geojson/.venv/bin:/opt/geojson/node_modules/.bin:$PATH \
    GEOJSON_IN_IMAGE=1

WORKDIR /work
