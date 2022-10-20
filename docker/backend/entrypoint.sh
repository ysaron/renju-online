#!/bin/sh

alembic upgrade head
python create_superuser.py

exec "$@"