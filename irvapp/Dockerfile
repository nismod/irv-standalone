FROM python:3.12-slim

WORKDIR /code
RUN apt-get update && apt-get install -y libgdal-dev g++

COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code

CMD ["python", "manage.py", "runserver"]
