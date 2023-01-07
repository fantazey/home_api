#!/usr/bin/env bash
ssh pi@pi << HERE
cd /home/pi/Projects/home-api
git pull origin master
docker build -t home-api .
docker stop test-django
docker rm test-django
docker run -d --name=test-django -p 8001:8000 -v /home/pi/Projects/home-api/media:/usr/src/app/media --add-host=pi:192.168.0.133 home-api
docker build -f Dockerfile_telebot -t home-api-telebot .
docker stop test-home-api-telebot
docker rm test-home-api-telebot
docker run -d --name=test-home-api-telebot -v /home/pi/Projects/home-api/media:/usr/src/app/media --add-host=pi:192.168.0.133 home-api-telebot
HERE