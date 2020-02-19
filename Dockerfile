FROM python:3.8
CMD ["python", "/app/script.py"]
RUN adduser --system --home /app app
USER app
COPY script.py /app

