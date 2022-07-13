#!/bin/bash

if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi

if [ -e /tmp/supervisord.pid ]; then supervisorctl stop all; fi

if [ -e /tmp/supervisord.pid ]; then supervisorctl shutdown; fi

sudo pkill -P1 gunicorn

