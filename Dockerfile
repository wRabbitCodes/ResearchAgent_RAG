# -------- Stage 1: Build with all dev tools --------
FROM python:3.13.5-slim as builder

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system deps required for building llama-cpp-python
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies including llama-cpp-python (built here)
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -------- Stage 2: Final runtime image --------
FROM python:3.13.5-slim

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local /usr/local

# Copy only the code (no build tools, no models)
COPY --chown=appuser:appuser . .

# Expose FastAPI port
EXPOSE 8000

# Run the app
CMD ["python", "src/main.py"]
