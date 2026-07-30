FROM python:3.13-alpine3.22

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN apk upgrade --no-cache \
    && addgroup -S app && adduser -S -G app -u 10001 app \
    && pip install --no-cache-dir -r requirements.txt

COPY app.py .

USER 10001:10001

EXPOSE 8080

CMD ["python", "app.py"]
