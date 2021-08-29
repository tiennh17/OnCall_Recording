FROM python:3

RUN mkdir -p /usr/src/app

WORKDIR /usr/src/app

RUN chmod -R 777 /usr/src/app

RUN touch log_recording.txt

COPY . /usr/src/app

RUN chmod 777 recording.py

RUN pip install -r requirements.txt

CMD [ "python3" , "recording.py" ]

USER root
