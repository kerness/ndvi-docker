FROM python:slim-buster

COPY . /opt/app
WORKDIR /opt/app

RUN ls -ltr
RUN pip install -r requirements.txt

ENTRYPOINT ["python", "landsat.py", ".", "krakow_krakowskie.shp"]