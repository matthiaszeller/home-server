
FROM python:3.10

WORKDIR /app

COPY ./services/dummy .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./common ./common
COPY ./config/* ./config


ENTRYPOINT ["tail", "-f", "/dev/null"]
