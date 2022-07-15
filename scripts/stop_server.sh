#!/bin/bash

supervisorctl -u user -p 123 shutdown

if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi

sudo pkill -P1 gunicorn
