#!/bin/sh
set -e

echo "Aguardando banco e aplicando migrations..."
alembic upgrade head

exec "$@"
