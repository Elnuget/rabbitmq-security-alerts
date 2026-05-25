# Plan Deber RabbitMQ

Materia: ISWZ2202 - Diseno y Arquitectura de Software

Caso: Gestor de Alertas de Seguridad

## Checklist

- [x] Paso 1: Crear repositorio publico y estructura base.
- [x] Paso 2: Levantar RabbitMQ con Docker.
- [x] Paso 3: Crear vhost, exchanges, colas y bindings.
- [x] Paso 4: Implementar productor de alertas.
- [x] Paso 5: Implementar dos consumidores.
- [x] Paso 6: Ejecutar pruebas del flujo completo.
- [x] Paso 7: Tomar capturas de RabbitMQ Management.
- [x] Paso 8: Completar documento final con evidencias.
- [ ] Paso 9: Preparar demo en clase.

## Arquitectura Objetivo

- Productor: envia alertas de seguridad con categoria, severidad, origen y mensaje.
- Consumidor SOC: recibe eventos criticos y eventos de autenticacion.
- Consumidor Notificaciones: recibe eventos de advertencia y difusion general.
- RabbitMQ: broker central con exchanges `topic`, `direct` y `fanout`.

## Exchanges

| Exchange | Tipo | Uso |
| --- | --- | --- |
| `alerts.topic` | `topic` | Enrutamiento por patrones como `auth.login.critical` o `network.scan.warning`. |
| `alerts.direct` | `direct` | Enrutamiento exacto por claves como `alert.critical` y `alert.warning`. |
| `alerts.fanout` | `fanout` | Difusion general a todas las colas enlazadas. |

## Colas

| Cola | Consumidor | Proposito |
| --- | --- | --- |
| `q.soc.critical` | `consumer_soc` | Alertas criticas y de autenticacion. |
| `q.notifications` | `consumer_notifications` | Alertas para notificaciones. |
| `q.audit` | Opcional | Evidencia de broadcast y auditoria. |

## Bindings Planeados

| Exchange | Cola | Routing key / patron |
| --- | --- | --- |
| `alerts.topic` | `q.soc.critical` | `*.critical` |
| `alerts.topic` | `q.soc.critical` | `auth.#` |
| `alerts.topic` | `q.notifications` | `network.*` |
| `alerts.direct` | `q.soc.critical` | `alert.critical` |
| `alerts.direct` | `q.notifications` | `alert.warning` |
| `alerts.fanout` | `q.notifications` | vacio |
| `alerts.fanout` | `q.audit` | vacio |

## Configuracion RabbitMQ Creada

- Vhost: `security_alerts`
- Usuario: `guest`
- Permisos: configurar, escribir y leer en `.*`
- Exchanges durables: `alerts.topic`, `alerts.direct`, `alerts.fanout`
- Colas durables: `q.soc.critical`, `q.notifications`, `q.audit`

## Capturas Necesarias

- Contenedor RabbitMQ ejecutandose.
- Login en RabbitMQ Management.
- Vhost creado.
- Lista de exchanges.
- Detalle de `alerts.topic`.
- Detalle de `alerts.direct`.
- Detalle de `alerts.fanout`.
- Lista de colas.
- Bindings de cada cola.
- Productor enviando mensajes.
- Dos consumidores recibiendo mensajes.

## Comandos Demo

```bash
docker compose up -d
python src/consumer_soc.py
python src/consumer_notifications.py
python src/producer.py
```

Para prueba rapida sin dejar procesos abiertos:

```bash
python src/producer.py
python src/consumer_soc.py --limit 2
python src/consumer_notifications.py --limit 3
```

## Evidencia Paso 6

Prueba end-to-end ejecutada contra RabbitMQ local en vhost `security_alerts`.

Antes de publicar se purgaron las colas `q.soc.critical`, `q.notifications` y `q.audit`.

Despues de ejecutar `python src/producer.py`:

```text
q.soc.critical      2 ready, 0 unacked
q.notifications     3 ready, 0 unacked
q.audit             1 ready, 0 unacked
```

Despues de ejecutar consumidores:

```text
python src/consumer_soc.py --limit 2
python src/consumer_notifications.py --limit 3
```

Resultado:

```text
q.soc.critical      0 ready, 0 unacked
q.notifications     0 ready, 0 unacked
q.audit             1 ready, 0 unacked
```

`q.audit` conserva 1 mensaje porque no tiene consumidor en esta practica; evidencia que `alerts.fanout` difundio el broadcast tambien a auditoria.
