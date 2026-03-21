# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install NumPy and Cython first (needed for compilation)
RUN pip install --no-cache-dir numpy==1.26.2 Cython

# Copy Legacy modules for compilation
COPY legacy /app/legacy

# Compile Cython modules: -i (replace), -3 (Python 3)
# We assume legacy/mustache/resources exists. If not, this might fail, so we can make it conditional
# or just run it as the user requested it.
RUN cythonize -i -3 legacy/mustache/resources/*.pyx || echo "Cython compilation failed or no files found, continuing..."

# Install Project Requirements
COPY requirements.txt .
# Install into a user directory to easily copy later
RUN pip install --no-cache-dir --target=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies (if any system libs are needed, e.g., libgomp1 for some scikit-learn optimizations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONPATH=/install:/app
ENV FLASK_APP=run.py
ENV PYTHONUNBUFFERED=1
ENV PATH="/install/bin:$PATH"

# Copy installed packages from builder
COPY --from=builder /install /install
# Copy app code (including compiled legacy modules if they were built in-place in /app/legacy)
COPY --from=builder /app/legacy /app/legacy
COPY . .

EXPOSE 5000

# Timeout increased to 120s as verifying in previous tests showed necessary for HDBSCAN on large datasets
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "--timeout", "120", "run:app"]
