# syntax=docker/dockerfile:1.3

ARG ERPNEXT_VERSION
FROM frappe/frappe-worker:latest

USER root

ARG APP_NAME
COPY . ../apps/

RUN apt update && apt install vim -y

RUN apt-get install python3-dev -y
RUN apt-get install build-essential -y



RUN --mount=type=cache,target=/root/.cache/pip \
    install-app erpnext


RUN --mount=type=cache,target=/root/.cache/pip \
    install-app payments

USER frappe
