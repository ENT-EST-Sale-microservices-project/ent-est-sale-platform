# MS-Notification

FastAPI service for consuming domain events and exposing user notifications.

## Endpoints

- `GET /notifications/health`
- `POST /notifications/test`
- `GET /notifications/{user_id}`

## Event consumption

- Connects to RabbitMQ topic exchange `ent.events.topic` by default.
- Binds queue `q.notification.user` to:
  - `user.*`
  - `course.*`

## Environment variables

- `RABBITMQ_URL` (default: `amqp://ent:ChangeMe_123!@rabbitmq:5672/`)
- `EVENTS_EXCHANGE` (default: `ent.events.topic`)
- `NOTIF_QUEUE` (default: `q.notification.user`)
- `NOTIFICATION_ENABLE_CONSUMER` (default: `true`)
