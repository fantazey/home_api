#!/usr/bin/env bash

function build_base() {
# build base image for rpi3 model b
echo "Build base image"
docker buildx build -f Dockerfile_base --load --platform linux/arm/v7 -t fantazey/home-api-base:slim .
echo "Upload base image to hub.docker"
docker push fantazey/home-api-base:slim
}

function build_web() {
# build web image for rpi3 model b
echo "Build web image"
docker buildx build -f Dockerfile_web --load --platform linux/arm/v7 -t home-api:slim .
docker save -o /tmp/docker-image-home-api.tar home-api:slim
gzip /tmp/docker-image-home-api.tar
echo "Send web image to PI"
scp /tmp/docker-image-home-api.tar.gz pi@pi:/tmp/docker-image-home-api.tar.gz
echo "Remove web image archive"
rm /tmp/docker-image-home-api.tar.gz
}

function build_telebot() {
# build telebot image for rpi3 model b
echo "Build telebot image"
docker buildx build -f Dockerfile_telebot --load --platform linux/arm/v7 -t home-api-telebot .
docker save -o /tmp/docker-image-home-api-telebot.tar home-api-telebot:slim
gzip /tmp/docker-image-home-api-telebot.tar
echo "Send telebot image to PI"
scp /tmp/docker-image-home-api-telebot.tar.gz pi@pi:/tmp/docker-image-home-api-telebot.tar.gz
echo "Remove telebot image archive"
rm /tmp/docker-image-home-api-telebot.tar.gz
}

function deploy_web() {
ssh pi@pi << HERE
cd /tmp
echo "Unzip web image"
gunzip /tmp/docker-image-home-api.tar.gz
echo "Load web image into docker"
docker load -i /tmp/docker-image-home-api.tar
echo "Remove web image archive"
rm /tmp/docker-image-home-api.tar

cd /home/pi/Projects/home-api
echo "Stop home-api-web container"
docker stop home-api-web
echo "Remove home-api-web container"
docker rm home-api-web
echo "Start home-api-web container"
docker run -d --name=home-api-web \
  --restart=unless-stopped \
  -p 8001:8000 \
  -v /home/pi/Projects/home-api/media:/usr/src/app/media \
  -v /home/pi/Projects/home-api/home_api/private_settings.py:/usr/src/app/home_api/private_settings.py:ro \
  --add-host=pi:192.168.0.133 \
  home-api:slim
HERE
}

function deploy_telebot() {
ssh pi@pi << HERE
cd /tmp
echo "Unzip telebot image"
gunzip /tmp/docker-image-home-api-telebot.tar.gz
echo "Load telebot image into docker"
docker load -i /tmp/docker-image-home-api-telebot.tar
echo "Remove telebot image archive"
rm /tmp/docker-image-home-api-telebot.tar

echo "Stop home-api-telebot container"
docker stop home-api-telebot
echo "Remove home-api-telebot container"
docker rm home-api-telebot
echo "Start home-api-telebot container"
docker run -d --name=home-api-telebot \
  --restart=unless-stopped \
  -v /home/pi/Projects/home-api/home_api/private_settings.py:/usr/src/app/home_api/private_settings.py:ro \
  -v /tmp/homeapi:/tmp/homeapi \
  -v /home/pi/Projects/home-api/media:/usr/src/app/media \
  --add-host=pi:192.168.0.133 \
  home-api-telebot:slim
HERE
}

while [ -n "$1" ]
do
  case "$1" in
  -bb) build_base ;;
  -bw) build_web ;;
  -bt) build_telebot ;;
  -dw) deploy_web ;;
  -dt) deploy_telebot ;;
  *) echo "unknown option" ;;
  esac
  shift
done