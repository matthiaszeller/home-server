# Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir Flask

COPY main.py main.py

CMD ["flask", "--app", "main", "run", "--host=0.0.0.0", "--port=5000"]
