
FROM python:3.10-slim

WORKDIR /app

COPY ./services/dummy/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./services/dummy/ .
COPY ./common ./common
COPY ./config/* ./config


ENTRYPOINT ["tail", "-f", "/dev/null"]
