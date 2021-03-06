FROM python:3.8

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

EXPOSE 80

COPY . .

ENV OSM_URL=https://overpass-api.de/api/interpreter
ENV MONGODB_DATABASE=roadtrip
ENV MONGODB_SERIES=user_search
ENV MONGODB_USER=mongodbuser
ENV MONGODB_PASSWORD=your_mongodb_root_password
ENV TELEGRAM_API_TOKEN=_
ENV MONGODB_HOST=mongodb

USER root
RUN chmod 755 ./start.sh
CMD ./start.sh
