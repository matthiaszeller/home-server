FROM python:3.13-alpine


WORKDIR /app

# install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Setup 10min cron job
RUN echo "*/10 * * * * python /app/main.py > /app/logs/cron.log 2>&1" >> /etc/crontabs/root

# copy scripts
COPY main.py .
COPY health.py .
COPY providers providers

# health probe
HEALTHCHECK --interval=60s --timeout=3s --start-period=600s --retries=2 \
  CMD python /app/health.py  || exit 1

# startup command
CMD [ "crond", "-l", "8", "-f" ]
