# GaugeGap Foundry - Production Docker Image
# Supports all three tracks: GaugeGap, FlowGap, CurveRank

FROM python:3.11-slim

LABEL maintainer="GaugeGap Foundry Team"
LABEL description="Verification-first AI-for-science infrastructure for Millennium Prize-adjacent problems"
LABEL version="0.1.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md LICENSE AGENTS.md ./
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY hypotheses/ ./hypotheses/
COPY docs/ ./docs/

# Install Python dependencies
# Start with minimal install, then add optional dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e ".[spectral,flow,dev]"

# Create results directory
RUN mkdir -p /app/results

# Run tests to verify installation
RUN python -m pytest tests/ -v

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Default command: reproduce the Berry-Keating impossibility proof
CMD ["python", "scripts/run_curverank_screen.py", \
     "--family", "xp", \
     "--n-basis", "10,15,20", \
     "--k-zeros", "20", \
     "--output-dir", "results/docker-run"]

# Alternative commands (override with docker run):
# 
# GaugeGap Z2 plaquette benchmark:
#   docker run gaugegap-foundry python scripts/run_z2_plaquette.py
#
# FlowGap Burgers benchmark:
#   docker run gaugegap-foundry python scripts/run_flowgap_burgers.py
#
# CurveRank extended screening:
#   docker run gaugegap-foundry python scripts/run_curverank_screen.py \
#       --family xp --n-basis 10,15,20,25,30 --k-zeros 50
#
# Interactive shell:
#   docker run -it gaugegap-foundry /bin/bash

# Made with Bob
