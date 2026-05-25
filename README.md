# RabbitMQ Security Alerts

Proyecto para la práctica de Diseño y Arquitectura de Software sobre gestores de colas con RabbitMQ.

Caso real: Gestor de Alertas de Seguridad.

## Objetivo

Implementar un productor y dos consumidores usando RabbitMQ con exchanges `topic`, `direct` y `fanout`.

## Componentes

- `producer`: publica alertas de seguridad.
- `consumer_soc`: consume alertas críticas para el equipo SOC.
- `consumer_notifications`: consume alertas de notificación.
- RabbitMQ Management UI: permite evidenciar exchanges, colas y bindings.

## Estructura

```text
.
├── docs/
│   └── plan-tarea.md
├── src/
│   ├── config.py
│   ├── consumer_notifications.py
│   ├── consumer_soc.py
│   └── producer.py
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Inicio Rapido

```bash
docker compose up -d
python -m venv .venv
pip install -r requirements.txt
```

Luego se implementan productor y consumidores segun `docs/plan-tarea.md`.
