FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY . /myproject
WORKDIR /myproject

RUN pip install --no-cache-dir -r requirements.txt
RUN python manage.py migrate
RUN python manage.py createcachetable
RUN python manage.py collectstatic --noinput
