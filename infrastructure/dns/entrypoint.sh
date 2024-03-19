#!/bin/sh

# Start crond in background
crond -l 8


LOGFILE='/app/dns.log'
# ensure logfile exists
touch "$LOGFILE"

# Tail logfile
tail -F "$LOGFILE"
