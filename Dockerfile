# Stage 1: Build the application
FROM python:3.9-slim AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user -r requirements.txt

COPY . .

# Stage 2: Create the final image
FROM python:3.9-slim AS final

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY . .

ENV PATH=/root/.local/bin:$PATH

EXPOSE 8000

CMD alembic upgrade head & uvicorn main:app --host 0.0.0.0 --port 8000
