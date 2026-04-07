## Запуск сервисов

Из корня, активировав `.venv`, в **отдельных терминалах**:

```bash
cd account_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

```bash
cd booking_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

```bash
cd tracking_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

```bash
cd media_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

```bash
cd payment_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8004 --reload
```

```bash
cd review_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

```bash
cd notification_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

```bash
cd gateway_service && ../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Проверка: `http://127.0.0.1:8000/health` … `http://127.0.0.1:8006/health`, шлюз: `http://127.0.0.1:8080/health`.

## Порты

| Сервис      | Порт |
|------------|------|
| account    | 8000 |
| booking    | 8001 |
| tracking   | 8002 |
| media      | 8003 |
| payment    | 8004 |
| review     | 8005 |
| notification | 8006 |
| gateway    | 8080 |

WebSocket трекинга подключать к **tracking** напрямую (не через gateway).

## После обновления (деплой / локально)

1. Применить миграции **`payment_service`** и **`booking_service`**: из корня с активным `.venv` выполнить `alembic upgrade head` в каждом из этих каталогов (или `./scripts/start-all.sh --migrate-only`).
2. В **`booking_service/.env`** задать URL платежного сервиса, например `PAYMENT_SERVICE_URL=http://127.0.0.1:8004` (в проде — реальный адрес **payment**).
3. Пользователям после выката **перелогиниться** (или обновить сессию через refresh): в access-токене должен быть claim **`role_key`** (`owner` / `walker`). Старые токены без `role_key` при операциях выгульщика (например вывод средств в **payment**) дадут ответ **`walker_only`**.
