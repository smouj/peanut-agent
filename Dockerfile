FROM python:3.11-slim

LABEL maintainer="Smouj + Peanut Agent"
LABEL description="🥜 PEANUT-AGENT PRO v0.1 — Gateway + Agent (local-first)"

# Dependencias base (ligeras)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    sqlite3 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1
ENV OLLAMA_URL=http://ollama:11434

EXPOSE 18789

CMD ["python", "web_ui.py"]
