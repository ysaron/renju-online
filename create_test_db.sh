#!/bin/bash

set -e

test_db="${POSTGRES_DB}_tests";

echo "Creating test database..."

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	CREATE DATABASE $test_db;
	GRANT ALL PRIVILEGES ON DATABASE $test_db TO "$POSTGRES_USER";
EOSQL

echo "Test database ${test_db} created."
