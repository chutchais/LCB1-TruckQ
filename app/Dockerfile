# Dockerfile - this is a comment. Delete me if you want.
FROM python:3.7.5-alpine

RUN apk add --update --no-cache \
    g++ gcc libxslt-dev musl-dev python3-dev \
    libffi-dev openssl-dev jpeg-dev zlib-dev

RUN apk add --no-cache tzdata
ENV TZ Asia/Bangkok

ENV LIBRARY_PATH=/lib:/usr/lib

WORKDIR /usr/src/app
COPY ./requirements.txt /usr/src/app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt


COPY . /usr/src/app


RUN chmod +x /usr/src/app/docker-entrypoint.sh
