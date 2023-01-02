FROM python:3-alpine
WORKDIR /usr/src/app
COPY req.txt ./
RUN pip install --no-cache-dir -r req.txt
COPY . .
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
