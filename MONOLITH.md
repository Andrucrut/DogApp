# DogApp Monolith Mode

This repository now also supports a single-process backend mode that keeps the
existing service folders intact.

## What changes

- The existing folders stay as they are: `account_service`, `booking_service`,
  `tracking_service`, `media_service`, `payment_service`, `review_service`,
  `notification_service`.
- A single FastAPI app in `main.py` mounts them all under one process:
  - `/account`
  - `/booking`
  - `/tracking`
  - `/media`
  - `/payment`
  - `/review`
  - `/notification`
- Internal service-to-service HTTP calls point back to the same app using
  `MONOLITH_BASE_URL`.
- `gateway_service` is not needed in monolith mode.

## Setup

1. Copy env:

```bash
cp monolith.env.sample monolith.env
```

2. Create the target database, for example:

```bash
createdb dogapp_monolith
```

3. Initialize all tables into the single database:

```bash
set -a && source monolith.env && set +a
PYTHONPATH=. ./.venv/bin/python scripts/init-monolith-db.py
```

4. Start the single backend:

```bash
bash scripts/start-monolith.sh
```

## Health

```bash
curl http://127.0.0.1:9000/health
```

## API shape

The original `/api/v1` routes stay inside each mounted service.
Examples:

- `http://127.0.0.1:9000/account/api/v1/auth/register`
- `http://127.0.0.1:9000/booking/api/v1/bookings/`
- `http://127.0.0.1:9000/notification/api/v1/notifications/me`

