#!/bin/bash

if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi

supervisorctl shutdown

sudo pkill -P1 gunicorn

