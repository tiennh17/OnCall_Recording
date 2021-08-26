FROM python:3

RUN mkdir -p ~/recording

WORKDIR /recording

COPY . /recording 

RUN pip --proxy http://proxy.hcm.fpt.vn:80 install -r requirements.txt

CMD [ "python3" , " ./recording.py" ]
