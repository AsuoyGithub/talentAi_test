FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    TALENT_AI_DB=/data/talent_ai.db \
    TALENT_AI_HOST=0.0.0.0 \
    TALENT_AI_PORT=8080

WORKDIR /app

COPY src ./src
COPY pyproject.toml README.md LICENSE ./

RUN mkdir -p /data

EXPOSE 8080

CMD ["python", "-m", "talent_ai", "serve"]
