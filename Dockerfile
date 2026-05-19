# =============================================================
# Stage 1 — Builder
# Install dependencies in an isolated layer.
# This layer is DISCARDED in the final image; only the
# installed packages (in /install) are copied across.
# =============================================================
FROM python:3.11-slim AS builder

WORKDIR /install

# Copy only the dependency manifest first — this lets Docker
# cache the pip-install layer until requirements.txt changes.
COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


# =============================================================
# Stage 2 — Runtime
# Lean final image; no build tools, no cache, no .venv.
# =============================================================
FROM python:3.11-slim AS runtime

# Keeps Python from writing .pyc files and enables unbuffered
# stdout/stderr so logs appear immediately in the container.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY app/ ./app/
COPY main.py .

# Non-root user for security best practice
RUN addgroup --system appgroup \
 && adduser  --system --ingroup appgroup appuser
USER appuser

EXPOSE 8000

# Health-check: Docker will poll /health every 30 s
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Use exec form so signals (SIGTERM) reach uvicorn directly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
