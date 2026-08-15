FROM python:3.12-slim

WORKDIR /app

# System deps needed for GitPython to shell out to the real git binary.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Example: docker run --env-file .env dailypulse python -m src.main --type quote
ENTRYPOINT ["python", "-m", "src.main"]
CMD ["--test", "--type", "quote"]
