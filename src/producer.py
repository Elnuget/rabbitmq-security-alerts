import json
from datetime import datetime, timezone

import pika

from config import (
    AUDIT_QUEUE,
    DIRECT_EXCHANGE,
    FANOUT_EXCHANGE,
    NOTIFICATIONS_QUEUE,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_VHOST,
    SOC_QUEUE,
    TOPIC_EXCHANGE,
)


def create_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        virtual_host=RABBITMQ_VHOST,
        credentials=credentials,
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
    print(f"Sent {exchange} | {routing_key or 'broadcast'} | {alert['id']} | {alert['message']}")


def main():
    alerts = [
        (
            TOPIC_EXCHANGE,
            "auth.critical",
            build_alert(
                "ALERT-001",
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
                "ALERT-002",
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
                "ALERT-003",
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
                "ALERT-004",
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
                "ALERT-005",
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

    print("Producer finished.")


if __name__ == "__main__":
    main()
