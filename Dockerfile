# Build stage 
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --prefix=/install --no-cache-dir -r requirements.txt

# Runtime stage 
FROM python:3.12-slim AS runtime

WORKDIR /app

# Copy installed packages from builder & app source 
COPY --from=builder /install /usr/local
COPY . .

# Make start script executable
RUN chmod +x scripts/start.sh

EXPOSE 8000

CMD ["/bin/sh", "scripts/start.sh"]

