#!/bin/bash

if [ -e  /tmp/supervisord.pid ]; then sudo supervisorctl -u user -p 123 shutdown; fi


if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi

sudo pkill -P1 gunicorn
