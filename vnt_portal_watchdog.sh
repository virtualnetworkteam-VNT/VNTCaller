#!/bin/bash
# VNT Portal Watchdog - runs every 1 min via crontab
if ! fuser 8888/tcp > /dev/null 2>&1; then
    echo "[$(date '+%H:%M:%S')] Portal down, restarting..." >> /tmp/portal_watchdog.log
    fuser -k 8888/tcp 2>/dev/null; sleep 1
    cd /home/k/vnt-web
    nohup /usr/bin/python3 /home/k/vnt-web/portal_server.py >> /tmp/portal.log 2>&1 &
    sleep 4
    if fuser 8888/tcp > /dev/null 2>&1; then
        echo "[$(date '+%H:%M:%S')] Portal RESTARTED OK" >> /tmp/portal_watchdog.log
    else
        echo "[$(date '+%H:%M:%S')] Portal restart FAILED" >> /tmp/portal_watchdog.log
    fi
fi
