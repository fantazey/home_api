#!/usr/bin/env bash
# build base image for rpi3 model b
#docker buildx build -f Dockerfile_base --load --platform linux/arm/v7 -t fantazey/home-api-base:slim .
# build web image for rpi3 model b
#docker buildx build -f Dockerfile_web --load --platform linux/arm/v7 -t home-api .
# build telebot image for rpi3 model b
#docker buildx build -f Dockerfile_telebot --load --platform linux/arm/v7 -t home-api-telebot .
docker save -o /tmp/docker-image-home-api.tar home-api:slim
docker save -o /tmp/docker-image-home-api-telebot.tar home-api-telebot:slim
scp /tmp/docker-image-home-api.tar pi@pi:/tmp/docker-image-home-api.tar
scp /tmp/docker-image-home-api-telebot.tar pi@pi:/tmp/docker-image-home-api-telebot.tar
rm /tmp/docker-image-home-api.tar
rm /tmp/docker-image-home-api-telebot.tar
ssh pi@pi << HERE
cd /home/pi/Projects/home-api
docker load -i /tmp/docker-image-home-api.tar
rm /tmp/docker-image-home-api.tar
docker load -i /tmp/docker-image-home-api-telebot.tar
rm /tmp/docker-image-home-api-telebot.tar
docker stop home-api-web
docker rm home-api-web
docker run -d --name=home-api-web \
  --restart=unless-stopped \
  -p 8001:8000 \
  -v /home/pi/Projects/home-api/media:/usr/src/app/media \
  -v /home/pi/Projects/home-api/home_api/private_settings.py:/usr/src/app/home_api/private_settings.py:ro \
  --add-host=pi:192.168.0.133 \
  home-api:slim
docker stop home-api-telebot
docker rm home-api-telebot
docker run -d --name=home-api-telebot \
  --restart=unless-stopped \
  -v /home/pi/Projects/home-api/home_api/private_settings.py:/usr/src/app/home_api/private_settings.py:ro \
  -v /tmp/homeapi:/tmp/homeapi \
  -v /home/pi/Projects/home-api/media:/usr/src/app/media \
  --add-host=pi:192.168.0.133 \
  home-api-telebot:slim
HERE