#!/bin/bash

if [ -e  /tmp/supervisord.pid ]; then sudo pkill -F /tmp/supervisord.pid; fi

if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi

sudo pkill -P1 gunicorn
