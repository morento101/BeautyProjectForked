#!/bin/bash

if [ -e /var/run/nginx.pid ]; then sudo nginx -s stop; fi


pid = `ps ax | grep gunicorn`

if [ -z "$pid" ]; then
  echo "no gunicorn deamon on port $Port"
else
  kill $pid
fi
