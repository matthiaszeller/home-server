FROM alpine:latest


WORKDIR /app

# install curl
RUN apk add --no-cache curl

# Setup 5min cron job
RUN echo "*/5 * * * * sh /app/dns.sh > /app/logs/cron.log 2>&1" >> /etc/crontabs/root

# copy scripts
COPY dns.sh .
COPY entrypoint.sh .
RUN chmod +x dns.sh && chmod +x entrypoint.sh

# startup command
CMD [ "/app/entrypoint.sh" ]
