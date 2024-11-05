# pull official base image
FROM python:3.12-alpine

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install MySQL dependencies
RUN apk add --no-cache \
    mariadb-dev \
    build-base \
    pkgconfig

# install dependencies
COPY ./requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

# copy project
COPY . .

# # Copy the entrypoint script
# COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh

# # Make entrypoint script executable
# RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# # Entrypoint
# ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

RUN python manage.py makemigrations
RUN python manage.py migrate

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "myproject.wsgi:application"] 