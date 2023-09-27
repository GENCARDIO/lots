FROM python:3.10-slim

ENV TZ=Europe/Berlin

RUN pip3 install --upgrade pip

WORKDIR /lots

COPY . /lots

RUN pip3 --no-cache-dir install -r requirements.txt

VOLUME /lots/DB

CMD ["python3", "lots.py"]
