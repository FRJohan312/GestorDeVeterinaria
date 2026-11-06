FROM ubuntu:24.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 python3-tk && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/ ./src/

CMD ["python3", "src/main.py"]