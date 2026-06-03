FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml README.md SKILL.md ./
COPY src ./src
COPY data ./data
COPY scripts ./scripts

RUN pip install --upgrade pip && pip install -e .

ENTRYPOINT ["file-search-agent"]
