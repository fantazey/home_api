#!/usr/bin/env bash
ssh pi@pi << HERE
cd /home/pi/Projects/home-api
git pull origin master
docker build -t home-api .
docker stop test-django
docker rm test-django
docker run -d --name=test-django -p 8001:8000 --add-host=pi:192.168.0.133 home-api
HERE