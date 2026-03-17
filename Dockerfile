# -- Build stage --
FROM python:3.13-slim AS builder

WORKDIR /build

COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir .

# -- Runtime stage --
FROM python:3.13-slim

RUN groupadd --system ploidy && useradd --system --gid ploidy ploidy

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ /app/src/

WORKDIR /app

RUN mkdir /data && chown ploidy:ploidy /data

ENV PLOIDY_PORT=8765
ENV PLOIDY_DB_PATH=/data/ploidy.db
ENV PLOIDY_LOG_LEVEL=INFO

EXPOSE 8765

VOLUME /data

USER ploidy

CMD ["python", "-m", "ploidy"]
