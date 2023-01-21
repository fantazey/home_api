FROM python:3.9.13-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add gcc python3-dev musl-dev
RUN apk add postgresql-dev

WORKDIR /usr/src/app

COPY req.txt ./
RUN pip install --upgrade pip && pip install --no-cache-dir -r req.txt

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000", "--insecure"]
