FROM python:3.6
LABEL maintainer="Pawan Nandakishore <pawan.nandakishore@gmail.com>"
COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
RUN mkdir /app
COPY . /app
WORKDIR /app/app
EXPOSE 8080
CMD gunicorn -b :8080 index:server