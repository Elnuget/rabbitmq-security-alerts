import json
import os
import time
from datetime import datetime, timezone

import pika

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "security_alerts")

TOPIC_EXCHANGE = "alerts.topic"
DIRECT_EXCHANGE = "alerts.direct"
FANOUT_EXCHANGE = "alerts.fanout"

SOC_QUEUE = "q.soc.critical"
NOTIFICATIONS_QUEUE = "q.notifications"
AUDIT_QUEUE = "q.audit"


def create_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials,
        connection_attempts=10,
        retry_delay=5,
    )
    return pika.BlockingConnection(parameters)


def declare_topology(channel):
    channel.exchange_declare(exchange=TOPIC_EXCHANGE, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange=DIRECT_EXCHANGE, exchange_type="direct", durable=True)
    channel.exchange_declare(exchange=FANOUT_EXCHANGE, exchange_type="fanout", durable=True)

    for queue in (SOC_QUEUE, NOTIFICATIONS_QUEUE, AUDIT_QUEUE):
        channel.queue_declare(queue=queue, durable=True)

    channel.queue_bind(exchange=TOPIC_EXCHANGE, queue=SOC_QUEUE, routing_key="*.critical")
    channel.queue_bind(exchange=TOPIC_EXCHANGE, queue=SOC_QUEUE, routing_key="auth.#")
    channel.queue_bind(exchange=TOPIC_EXCHANGE, queue=NOTIFICATIONS_QUEUE, routing_key="network.*")
    channel.queue_bind(exchange=DIRECT_EXCHANGE, queue=SOC_QUEUE, routing_key="alert.critical")
    channel.queue_bind(exchange=DIRECT_EXCHANGE, queue=NOTIFICATIONS_QUEUE, routing_key="alert.warning")
    channel.queue_bind(exchange=FANOUT_EXCHANGE, queue=NOTIFICATIONS_QUEUE)
    channel.queue_bind(exchange=FANOUT_EXCHANGE, queue=AUDIT_QUEUE)


def build_alert(alert_id, category, severity, source, message):
    return {
        "id": alert_id,
        "category": category,
        "severity": severity,
        "source": source,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def publish_alert(channel, exchange, routing_key, alert):
    body = json.dumps(alert).encode("utf-8")
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=body,
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=pika.DeliveryMode.Persistent,
        ),
    )
    print(f"[producer] {exchange} | {routing_key or 'broadcast'} | {alert['id']} | {alert['message']}")


def main():
    counter = 1

    while True:
        alerts = [
            (
                TOPIC_EXCHANGE,
                "auth.critical",
                build_alert(
                    f"ALERT-{counter:04d}",
                    "auth",
                    "critical",
                    "api-gateway",
                    "Multiple failed login attempts",
                ),
            ),
            (
                TOPIC_EXCHANGE,
                "network.scan",
                build_alert(
                    f"ALERT-{counter + 1:04d}",
                    "network",
                    "warning",
                    "ids-sensor",
                    "Port scan detected",
                ),
            ),
            (
                DIRECT_EXCHANGE,
                "alert.critical",
                build_alert(
                    f"ALERT-{counter + 2:04d}",
                    "malware",
                    "critical",
                    "endpoint-agent",
                    "Malware detected on workstation",
                ),
            ),
            (
                DIRECT_EXCHANGE,
                "alert.warning",
                build_alert(
                    f"ALERT-{counter + 3:04d}",
                    "compliance",
                    "warning",
                    "policy-engine",
                    "Outdated security policy found",
                ),
            ),
            (
                FANOUT_EXCHANGE,
                "",
                build_alert(
                    f"ALERT-{counter + 4:04d}",
                    "broadcast",
                    "info",
                    "security-center",
                    "Security maintenance window starts tonight",
                ),
            ),
        ]

        with create_connection() as connection:
            channel = connection.channel()
            declare_topology(channel)

            for exchange, routing_key, alert in alerts:
                publish_alert(channel, exchange, routing_key, alert)

        counter += 5
        print(f"[producer] batch published. Next batch in 15 seconds...")
        time.sleep(15)


if __name__ == "__main__":
    main()
