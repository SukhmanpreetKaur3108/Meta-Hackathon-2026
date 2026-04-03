# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Runtime stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy source
COPY lpg_crisis_env/ ./lpg_crisis_env/
COPY inference.py .
COPY openenv.yaml .
COPY tests/ ./tests/

# Environment variable defaults (override at runtime)
ENV API_BASE_URL=https://router.huggingface.co/v1
ENV MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct
# HF_TOKEN must be provided at runtime: -e HF_TOKEN=hf_...

# Smoke test: import succeeds
RUN python -c "from lpg_crisis_env import LPGCrisisEnv; env = LPGCrisisEnv(); env.reset(); print('Environment loaded OK')"

# Default command: run baseline inference
CMD ["python", "inference.py"]
