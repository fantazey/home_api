#!/usr/bin/env bash
cd /home/pi/Projects/home-api
git pull origin master
docker stop test-django
docker rm test-django
docker build -t home-api .
docker run -d --name=test-django -p 8001:8000 --add-host=pi:192.168.0.133 home-api