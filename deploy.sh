#!/usr/bin/env bash
ssh pi@pi << HERE
cd /home/pi/Projects/home-api
git pull origin master
docker build -t home-api .
docker stop home-api-web
docker rm home-api-web
docker run -d --name=home-api-web --restart=unless-stopped -p 8001:8000 -v /home/pi/Projects/home-api/media:/usr/src/app/media --add-host=pi:192.168.0.133 home-api
docker build -f Dockerfile_telebot -t home-api-telebot .
docker stop home-api-telebot
docker rm home-api-telebot
docker run -d --name=home-api-telebot --restart=unless-stopped -v /tmp/homeapi:/tmp/homeapi -v /home/pi/Projects/home-api/media:/usr/src/app/media --add-host=pi:192.168.0.133 home-api-telebot
HERE