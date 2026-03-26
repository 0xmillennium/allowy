FROM python:3.14-slim AS builder

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir .


FROM python:3.14-slim

RUN groupadd --gid 1000 allowy \
    && useradd --uid 1000 --gid allowy --no-create-home allowy

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY src/ src/
COPY config/sources.yaml config/logging.yaml config/
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh \
    && mkdir -p config outputs logs \
    && chown -R allowy:allowy /app

ENV PATH="/opt/venv/bin:$PATH"

USER allowy

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
