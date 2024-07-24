FROM python:3.10-alpine
LABEL Author="Florian Dambrine <android.florian@gmail.com>"

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/opt/drone

RUN mkdir -p /opt/drone
WORKDIR /opt/drone

COPY requirements.txt /opt/drone/
RUN pip3 install -r requirements.txt

COPY plugin /opt/drone/plugin

ENTRYPOINT ["python3", "/opt/drone/plugin/main.py"]
