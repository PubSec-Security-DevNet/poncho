FROM ubuntu:22.04

# Copyright (c) 2024 Cisco and/or its affiliates.
#
# This software is licensed to you under the terms of the Cisco Sample
# Code License, Version 1.1 (the "License"). You may obtain a copy of the
# License at
#
#			    https://developer.cisco.com/docs/licenses
#
# All use of the material herein must be in accordance with the terms of
# the License. All rights not expressly granted by the License are
# reserved. Unless required by applicable law or agreed to separately in
# writing, software distributed under the License is distributed on an "AS
# IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
# or implied.
#

LABEL version="0.9.0"
LABEL description="Poncho: Uncategorized Website Management Tool For Cisco Umbrella"
LABEL maintainer="nciesins@cisco.com"


# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get upgrade \
    && apt-get install --no-install-recommends -y \
        python3 \
        pip \
        nginx \
    && apt-get clean \
    && apt-get purge \
    && rm -rf /var/lib/apt/lists/* 

# Set the working directory in the container
WORKDIR /app

# Copy the rest of the application code to the working directory
COPY requirements.txt .
COPY static ./static
COPY templates ./templates
COPY docker ./docker
COPY *.py .
COPY *.yaml .

RUN pip install --no-cache-dir -r requirements.txt && \
    mkdir data && \
    touch init.sh && \
    chmod 744 init.sh && \
    echo "#!/bin/sh" >> init.sh && \
    echo "if [ -f \"/app/docker/nginx/poncho.conf\" ]; then" >> init.sh && \
    echo "  if [ -f \"/app/docker/nginx/cert-bundle.crt\" ] && [ -f \"/app/docker/nginx/cert.key\" ]; then" >> init.sh && \
    echo "      mkdir /etc/nginx/ssl" >> init.sh && \
    echo "      cp /app/docker/nginx/cert-bundle.crt /etc/nginx/ssl/cert-bundle.crt" >> init.sh && \
    echo "      cp /app/docker/nginx/cert.key /etc/nginx/ssl/cert.key" >> init.sh && \
    echo "      chmod 600 /etc/nginx/ssl/cert.key" >> init.sh && \
    echo "      chmod 700 /etc/nginx/ssl" >> init.sh && \
    echo "      chown -R root:root /etc/nginx/ssl" >> init.sh && \
    echo "  fi" >> init.sh && \
    echo "  cp /app/docker/nginx/poncho.conf /etc/nginx/sites-available/poncho.conf" >> init.sh && \
    echo "  rm /etc/nginx/sites-enabled/default" >> init.sh && \
    echo "  ln -s /etc/nginx/sites-available/poncho.conf /etc/nginx/sites-enabled/poncho.conf" >> init.sh && \
    echo "  ln -sf /dev/stdout /var/log/nginx/access.log" >> init.sh && \
    echo "  ln -sf /dev/stderr /var/log/nginx/error.log" >> init.sh && \
    echo "fi" >> init.sh && \
    touch run.sh && \
    chmod 744 run.sh && \
    echo "#!/bin/sh" >> run.sh && \
    echo "./init.sh" >> run.sh && \
    echo "sed -i '/.\/init.sh/{N;d;}' ./run.sh" >> run.sh && \
    echo "if [ -f \"/etc/nginx/sites-enabled/poncho.conf\" ]; then nginx -g 'daemon off;' & fi" >> run.sh && \
    echo "gunicorn --preload --workers=4 --bind 0.0.0.0:8000 poncho:app" >> run.sh
    
# Expose the Flask app port
EXPOSE 8000 80 443

# Run Gunicorn to serve the Flask app
CMD ["./run.sh"]