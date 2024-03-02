#!/bin/bash

/home/jack/ccgc/env/bin/uwsgi --chdir=/home/jack/ccgc \
    --module=ccgc.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=ccgc.settings \
    --master --pidfile=/tmp/ccgc-master.pid \
    --socket=127.0.0.1:5000 \
    --processes=5 \
    --vacuum \
    --home=/home/jack/ccgc/env
