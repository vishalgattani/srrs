FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    && ln -sf /usr/bin/python3.11 /usr/bin/python \
    && ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install package + dev deps
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e ".[dev]"

# Copy rest of project (tests etc.)
COPY . .

# Default: run full test suite
CMD ["pytest", "tests/", "-v", "--tb=short"]
