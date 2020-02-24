FROM python:3.8-alpine
CMD ["python", "/app/script.py"]

RUN adduser --system --home /app app \
  && apk add -U --no-cache git

USER app
COPY script.py /app

