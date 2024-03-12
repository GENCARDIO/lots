FROM python:3.10-slim


ENV TZ=Europe/Berlin


RUN pip3 install --upgrade pip


RUN apt-get update \
    && apt-get install -y libreoffice --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /lots


COPY . /lots


RUN pip3 --no-cache-dir install -r requirements.txt


VOLUME /lots/DB


CMD ["python3", "lots.py"]
