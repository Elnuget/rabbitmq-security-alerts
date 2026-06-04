#!/bin/bash
echo "Waiting for RabbitMQ..."
until rabbitmqctl -n rabbit@rabbitmq ping > /dev/null 2>&1; do
  sleep 2
done
echo "RabbitMQ ready. Creating vhost..."
rabbitmqctl -n rabbit@rabbitmq add_vhost security_alerts 2>/dev/null || true
rabbitmqctl -n rabbit@rabbitmq set_permissions -p security_alerts guest ".*" ".*" ".*"
echo "Vhost security_alerts created."
