# ==============================================================================
# Container: Zero-LLM Support Triage & Intent Routing Engine
# Base: Python 3.12 Slim (Minimal attack surface & memory footprint)
# ==============================================================================
FROM python:3.12-slim

# System dependencies for high-performance math and SQLite
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY pyproject.toml .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir . && \
    python -c "import nltk; nltk.download('vader_lexicon')"

# Copy application source code
COPY . .

# Initialize SQLite database and train baseline classifier
RUN python database/init_db.py && \
    python models/train_model.py

# Healthcheck to verify local engine availability
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, 'windmill/f/econ_support_triage'); import delighted_script; res = delighted_script.main('HEALTH', 'Order ping', 'Standard'); sys.exit(0 if res['department'] else 1)"

EXPOSE 8080

CMD ["python", "scripts/deploy_and_test.py"]
