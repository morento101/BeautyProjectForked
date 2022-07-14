#!/bin/bash

if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi

supervisorctl -u user -p 123 shutdown

sudo pkill -P1 gunicorn

