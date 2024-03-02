#!/bin/bash

/home/jack/ccgc/env/uwsgi --chdir=/home/jack/ccgc \
    --module=ccgc.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=ccgc.settings \
    --master --pidfile=/tmp/ccgc-master.pid \
    --socket=127.0.0.1:5000 \      # can also be a file
    --processes=5 \                 # number of worker processes
    --vacuum \                      # clear environment on exit
    --home=/home/jack/ccgc/env
