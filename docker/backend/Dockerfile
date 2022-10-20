FROM python:3.10

# не записывать .pyc-файлы
ENV PYTHONDONTWRITEBYTECODE 1
# отключение буферизации потоков stdout и stderr
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/back/

RUN apt update \
    && apt upgrade -y \
    && apt install netcat postgresql gcc python3-dev musl-dev -y \
    && pip install --upgrade pip

COPY ./req.txt .

RUN pip install -r req.txt

COPY docker/backend/entrypoint.sh .

COPY . .

ENTRYPOINT ["/usr/src/back/entrypoint.sh"]
