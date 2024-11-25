FROM python:3.11-slim-buster

ENV PYTHONUNBUFFERED=1

RUN mkdir /app
WORKDIR /app

RUN pip install 'pip<24.1'
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY src /app/src

ENV PYTHONPATH /app/src

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
