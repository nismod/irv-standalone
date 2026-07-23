FROM python:3.12-slim

WORKDIR /code
RUN apt-get update && apt-get install -y libgdal-dev g++

COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

EXPOSE 8000

# Production server; docker-compose.dev.yml overrides this with
# `manage.py runserver` for development
CMD ["gunicorn", "irvapp.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]
