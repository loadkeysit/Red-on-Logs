FROM python:3.11-slim

WORKDIR /app

COPY ./logproducer.py .

RUN pip install kafka-python

CMD ["python", "logproducer.py"]
