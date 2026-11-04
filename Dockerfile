FROM python:3.10-slim


ENV TZ=Europe/Madrid \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


RUN pip3 install --upgrade pip


RUN apt-get update \
    && apt-get install -y libreoffice --no-install-recommends \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /lots


COPY . /lots


RUN pip3 --default-timeout=180 --no-cache-dir install -r requirements.txt


VOLUME /lots/DB

EXPOSE 5017


CMD ["python3", "lots.py"]
