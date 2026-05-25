import argparse
import json

import pika

from config import (
    NOTIFICATIONS_QUEUE,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_VHOST,
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


def print_alert(alert):
    print(
        "Notifications received "
        f"{alert['id']} | {alert['severity']} | {alert['category']} | "
        f"{alert['source']} | {alert['message']}"
    )


def handle_message(channel, method, properties, body):
    alert = json.loads(body.decode("utf-8"))
    print_alert(alert)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def consume_limited(channel, limit):
    consumed = 0

    for _ in range(limit):
        method, properties, body = channel.basic_get(queue=NOTIFICATIONS_QUEUE, auto_ack=False)
        if method is None:
            break

        handle_message(channel, method, properties, body)
        consumed += 1

    print(f"Notifications consumer finished. Messages consumed: {consumed}")


def main():
    parser = argparse.ArgumentParser(description="Consume notification security alerts")
    parser.add_argument("--limit", type=int, help="Consume N messages and exit")
    args = parser.parse_args()

    with create_connection() as connection:
        channel = connection.channel()
        channel.queue_declare(queue=NOTIFICATIONS_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)

        if args.limit:
            consume_limited(channel, args.limit)
            return

        channel.basic_consume(queue=NOTIFICATIONS_QUEUE, on_message_callback=handle_message)
        print(f"Notifications consumer waiting on {NOTIFICATIONS_QUEUE}. Press Ctrl+C to stop.")

        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()


if __name__ == "__main__":
    main()
