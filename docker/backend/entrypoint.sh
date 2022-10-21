#!/bin/sh

alembic revision --autogenerate
alembic upgrade head
python create_superuser.py

exec "$@"