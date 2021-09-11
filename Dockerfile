FROM python:3.8.3-slim-buster as base

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
COPY main.py .

# FROM base as test

# RUN python3 pytest

FROM base as prod

COPY entrypoint.sh .

ENTRYPOINT ["/app/entrypoint.sh"]