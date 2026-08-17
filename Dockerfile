FROM python:3.12-slim

LABEL org.opencontainers.image.title="Multi-Coin Paper Daytrader" \
      org.opencontainers.image.version="0.2.0" \
      org.opencontainers.image.description="Paper-only crypto daytrading simulator for Unraid" \
      org.opencontainers.image.source="https://github.com/2CrAzYTV/multi-coin-paper-daytrader" \
      org.opencontainers.image.url="https://github.com/2CrAzYTV/multi-coin-paper-daytrader" \
      org.opencontainers.image.documentation="https://github.com/2CrAzYTV/multi-coin-paper-daytrader/blob/main/docs/UNRAID.md" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    XDG_CACHE_HOME=/data/.cache

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY unraid/multi-coin-paper-daytrader.png ./app/static/app-icon.png
RUN mkdir -p /data

EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/health', timeout=3)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8787", "--proxy-headers"]
