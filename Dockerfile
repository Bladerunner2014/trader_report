FROM python:3.8-slim-buster
RUN apt-get update && apt-get install
RUN apt-get install -y libpq-dev python-dev
RUN apt-get -y install gcc mono-mcs
RUN pip install --upgrade pip
WORKDIR /make_trade
COPY ./requirements.txt  requirements.txt
RUN pip install -r ./requirements.txt
COPY . . 
EXPOSE 5002/TCP
CMD ["python3","app.py"]

