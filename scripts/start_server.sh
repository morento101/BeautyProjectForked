#!/bin/bash

cd /home/ec2-user/Beauty

python3.9 -m venv venv

source venv/bin/activate

pip3.9 install -r requirements.txt

cd beauty

python3.9 manage.py makemigrations
python3.9 manage.py migrate
python3.9 manage.py collectstatic --noinput

sudo chmod -R 777 /home/ec2-user/Beauty

sudo cp /home/ec2-user/Beauty/nginx/flower.conf /etc/nginx/conf.d

gunicorn beauty.wsgi:application --bind 0.0.0.0:8000 --workers 4 --daemon

sudo nginx -c /etc/nginx/nginx.conf

supervisord -c /home/ec2-user/Beauty/supervisord.conf
