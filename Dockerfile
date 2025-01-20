FROM python:3.11.0-slim-buster
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /opt/app

#RUN apt-get update && apt-get install -y fontconfig libfontconfig1 libicu-dev

COPY requirements.txt /opt/app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt



#RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.31.0/geckodriver-v0.31.0-linux64.tar.gz && \
#    tar -xvzf geckodriver-v0.31.0-linux64.tar.gz && \
#    rm geckodriver-v0.31.0-linux64.tar.gz && \
#    mv geckodriver /usr/local/bin/

# Packages that require runtime download can be cached by running the python -c "CODE"
# Replace "CODE" with the lines that handle downloading
# RUN python -c "CODE"

WORKDIR /workspace