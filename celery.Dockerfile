FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1

RUN mkdir /app
WORKDIR /app

RUN pip install 'pip<24.1'
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY src /app/src
ENV PYTHONPATH "/app"

COPY ./start_celery_cmd/start_celery_beat /start_celery_beat
RUN sed -i 's/\r$//g' /start_celery_beat
RUN chmod +x /start_celery_beat

COPY ./start_celery_cmd/start_celery_worker /start_celery_worker
RUN sed -i 's/\r$//g' /start_celery_worker
RUN chmod +x /start_celery_worker