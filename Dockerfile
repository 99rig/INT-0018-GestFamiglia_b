# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

EXPOSE 8000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install system dependencies for uWSGI compilation
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libc6-dev \
    python3-dev \
    zstd \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install pip requirements
# COPY requirements/ requirements/
COPY requirements.txt .
RUN python -m pip install --upgrade pip
RUN python -m pip install -r requirements.txt

COPY . /code/
WORKDIR /code/

# Copia configurazione uWSGI
COPY uwsgi.ini /etc/uwsgi.ini

# Crea directory per log uWSGI
RUN mkdir -p /var/log/uwsgi

# Esegui collectstatic durante il build (usando --noinput per evitare prompt)
RUN python manage.py collectstatic --noinput
# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /code && chown -R appuser /var/log/uwsgi
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["uwsgi", "--ini=/etc/uwsgi.ini", "--show-config"]
