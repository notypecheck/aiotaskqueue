ARG PYTHON_IMAGE=python:3.12.9-slim-bookworm


FROM $PYTHON_IMAGE AS build
ARG PYTHON_UV_VERSION=>=0.5.29

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

RUN pip install uv${PYTHON_UV_VERSION}
RUN uv venv /app/.venv
COPY ./pyproject.toml ./uv.lock ./
RUN uv sync --frozen --no-install-project --all-extras --all-groups

FROM $PYTHON_IMAGE

RUN addgroup --gid 2000 app && adduser --gid 2000 --uid 1000 app
RUN chown -R app:app /home/app
USER app

WORKDIR /app
COPY --from=build --chown=app:app /app/.venv /app/.venv
ENV PYTHONPATH=$PYTHONPATH:/app/src \
    PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1

COPY aiotaskqueue ./aiotaskqueue
COPY ./example ./example
