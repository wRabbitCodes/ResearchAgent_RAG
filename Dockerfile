# -------- Stage 1: Build with all dev tools --------
FROM python:3.13.5-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------- Stage 2: Final runtime image --------
FROM python:3.13.5-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install libgomp1 required by llama_cpp native lib (OpenMP runtime)
RUN apt-get update && apt-get install -y libgomp1 curl && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local /usr/local

# Copy only the code (no build tools, no models) AS ROOT first
COPY . .

# Create non-root user and set ownership
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["python", "main.py"]
