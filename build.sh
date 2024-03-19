# build base image for rpi3 model b
docker buildx build -f Dockerfile_base --load --platform linux/arm/v7 -t home-api-base .
# build web image for rpi3 model b
docker buildx build -f Dockerfile_web --load --platform linux/arm/v7 -t home-api .
# build telebot image for rpi3 model b
docker buildx build -f Dockerfile_telebot --load --platform linux/arm/v7 -t home-api-telebot .
