import json
import os
import sqlite3
import threading

import pika
import uvicorn
from fastapi import FastAPI

RABBITMQ_HOST = os.environ.get("RABBITMQ_HOST", "rabbitmq")
RABBITMQ_PORT = int(os.environ.get("RABBITMQ_PORT", 5672))
RABBITMQ_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBITMQ_PASSWORD = os.environ.get("RABBITMQ_PASSWORD", "guest")
RABBITMQ_VHOST = os.environ.get("RABBITMQ_VHOST", "security_alerts")

SOC_QUEUE = "q.soc.critical"
DB_PATH = "/data/soc_alerts.db"

app = FastAPI(title="SOC Alerts API", version="1.0.0")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            source TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            consumed_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_alert(alert):
    from datetime import datetime, timezone

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO alerts (id, category, severity, source, message, timestamp, consumed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            alert["id"],
            alert["category"],
            alert["severity"],
            alert["source"],
            alert["message"],
            alert["timestamp"],
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    conn.close()


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


def handle_message(channel, method, properties, body):
    alert = json.loads(body.decode("utf-8"))
    save_alert(alert)
    print(f"[soc] consumed {alert['id']} | {alert['severity']} | {alert['category']} | {alert['message']}")
    channel.basic_ack(delivery_tag=method.delivery_tag)


def consume_loop():
    with create_connection() as connection:
        channel = connection.channel()
        channel.queue_declare(queue=SOC_QUEUE, durable=True)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=SOC_QUEUE, on_message_callback=handle_message)
        print("[soc] consumer waiting for messages...")
        channel.start_consuming()


@app.on_event("startup")
def startup():
    init_db()
    thread = threading.Thread(target=consume_loop, daemon=True)
    thread.start()


@app.get("/alerts")
def get_alerts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM alerts ORDER BY consumed_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/alerts/count")
def get_alerts_count():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    conn.close()
    return {"count": count}


@app.get("/health")
def health():
    return {"status": "ok", "service": "consumer-soc"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
