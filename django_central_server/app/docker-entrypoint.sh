#!/bin/bash

# Wait for MySQL to be available
if [ "$DATABASE" = "mysql" ]; then
    echo "Waiting for MySQL..."
    until apk add --no-cache --virtual .build-deps mariadb-client && \
          mysqladmin ping -h "$SQL_HOST" -P "$SQL_PORT" --silent; do
        sleep 0.5
    done
    echo "MySQL started"
    apk del .build-deps
fi

# Execute the passed command
exec "$@"