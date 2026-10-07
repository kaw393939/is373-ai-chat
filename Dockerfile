FROM node:24-alpine@sha256:ebfe2f90462722a7a4de65e91990e97fe0d401c70e0e762c5b53302f905ec1c1 AS frontend
WORKDIR /ui
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm test && npm run format:check && npm run build

FROM python:3.14.7-slim-trixie@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d AS dependencies
WORKDIR /app
RUN pip install --no-cache-dir uv==0.12.15
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --python /usr/local/bin/python

FROM python:3.14.7-slim-trixie@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d AS runtime
RUN python -m pip uninstall -y pip \
    && groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin appuser
WORKDIR /app
COPY --from=dependencies /app/.venv /app/.venv
COPY --from=frontend /ui/dist /app/frontend/dist
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY deploy ./deploy
COPY VERSION ./VERSION
ENV PATH="/app/.venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 STATIC_DIR=/app/frontend/dist
ARG COMMIT_SHA=development
ARG APP_VERSION=unreleased
RUN test "$APP_VERSION" = unreleased || test "$(cat VERSION)" = "$APP_VERSION"
ENV COMMIT_SHA=$COMMIT_SHA
LABEL org.opencontainers.image.source="https://github.com/kaw393939/is373-ai-chat" org.opencontainers.image.revision=$COMMIT_SHA org.opencontainers.image.version=$APP_VERSION
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3)"
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "172.18.0.0/16", "--limit-concurrency", "32", "--no-access-log"]
