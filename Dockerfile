FROM python:3.8.1-slim

RUN mkdir -p /media/msd /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

WORKDIR /workshop
COPY app ./app
COPY start.sh ./start.sh
RUN chmod a+x start.sh

CMD [ "./start.sh" ]