FROM python:3.13-alpine


WORKDIR /app

# install
RUN pip install --no-cache-dir requests

# Setup 5min cron job
RUN echo "*/5 * * * * python /app/main.py > /app/logs/cron.log 2>&1" >> /etc/crontabs/root

# copy scripts
COPY main.py .

# startup command
CMD [ "crond", "-l", "8", "-f" ]
