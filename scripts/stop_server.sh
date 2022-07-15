#!/bin/bash

if [ -e  /tmp/supervisord.pid ]; then sudo kill -9 $(cat /tmp/supervisord.pid); fi

if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi

sudo pkill -P1 gunicorn
