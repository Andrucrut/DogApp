#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	CREATE DATABASE booking_db;
	CREATE DATABASE tracking_db;
	CREATE DATABASE media_db;
	CREATE DATABASE payment_db;
	CREATE DATABASE review_db;
	CREATE DATABASE notification_db;
EOSQL
