FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    TZ=UTC

# Base utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Install Chromium + all its system dependencies via playwright
RUN playwright install chromium && \
    playwright install-deps chromium

COPY server.py /server.py

EXPOSE 3478

CMD ["python3", "/server.py"]
