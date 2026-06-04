# RabbitMQ Security Alerts - Microservices

Microservicios de alertas de seguridad con RabbitMQ.

## Arquitectura

```
producer-service ──> RabbitMQ ──> consumer-soc-service (API REST + SQLite)
                          │
                          └──> consumer-notifications-service (SQLite)
```

Cada servicio se despliega en su propio contenedor Docker con almacenamiento independiente.

## Microservicios

| Servicio | Puerto | Almacenamiento | API |
|---|---|---|---|
| producer-service | - | - | No |
| consumer-soc-service | 8000 | SQLite (`/data/soc_alerts.db`) | Si |
| consumer-notifications-service | - | SQLite (`/data/notifications.db`) | No |

## Ejecucion

```bash
docker compose up --build
```

Todos los servicios se inician automaticamente. El producer publica alertas cada 15 segundos.

## API SOC

Una vez levantado:

```bash
curl http://localhost:8000/alerts
curl http://localhost:8000/alerts/count
curl http://localhost:8000/health
```

## RabbitMQ Management

```
http://localhost:15672
```

Usuario: `guest` / Password: `guest`

## Estructura

```
services/
├── producer-service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
├── consumer-soc-service/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
└── consumer-notifications-service/
    ├── app.py
    ├── Dockerfile
    └── requirements.txt
```

## Patron Arquitectonico

- **Comunicacion asincrona**: Los microservicios se comunican mediante RabbitMQ, no llamadas HTTP directas.
- **Desacoplamiento**: El productor no conoce a los consumidores.
- **Almacenamiento propio**: Cada consumidor tiene su base SQLite independiente.
- **Despliegue independiente**: Cada servicio en su contenedor con su Dockerfile.
- **API REST**: consumer-soc expone endpoints para consultar alertas consumidas.
