
FROM python:3.10-slim

WORKDIR /app

COPY ./services/tgbot/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY ./services/tgbot .
COPY ./common ./common
COPY ./config/* ./config

CMD ["python", "-m", "main"]
