FROM python:2

WORKDIR /root/app/

RUN pip install --upgrade pip
RUN pip install setuptools gunicorn waitress watchdog flask pycrypto futures

COPY . .
COPY d-note-docker.ini /etc/dnote/d-note.ini

RUN python ./setup.py install

RUN generate_dnote_hashes

EXPOSE "8080"

ENTRYPOINT [ "/root/app/run" ]