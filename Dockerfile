# Stage 1: Build the application
FROM python:3.10-slim AS builder

# Set the working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies into a temporary directory
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Copy the application code
COPY . .

# Stage 2: Create a minimal runtime image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /install /usr/local

# Copy application code from the builder stage
COPY --from=builder /app /app

# Expose the application port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"]