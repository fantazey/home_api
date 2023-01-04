FROM python:3.9.13-slim-buster
WORKDIR /usr/src/app
COPY req.txt ./
RUN apt-get install python3-lxml
RUN pip install --no-cache-dir -r req.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
