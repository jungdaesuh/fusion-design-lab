FROM python:3.12-slim

WORKDIR /app/env

RUN apt-get update && \
    apt-get install -y --no-install-recommends git curl libgomp1 && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    constellaration \
    "fastapi>=0.115.0" \
    "numpy>=2.0.0" \
    "openenv-core[core]>=0.2.1" \
    "pydantic>=2.10.0" \
    "uvicorn>=0.34.0"

COPY . /app/env

ENV PYTHONPATH="/app/env:$PYTHONPATH"
ENV ENABLE_WEB_INTERFACE=true

EXPOSE 8000

HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
