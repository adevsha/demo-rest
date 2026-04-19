import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from aiokafka import AIOKafkaProducer

from app.config import settings

logger = logging.getLogger(__name__)

_producer: AIOKafkaProducer | None = None

TOPIC_USERS = "demo.users"
TOPIC_PRODUCTS = "demo.products"
TOPIC_ORDERS = "demo.orders"


async def start_producer() -> None:
    global _producer
    producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP)
    try:
        await asyncio.wait_for(producer.start(), timeout=5.0)
        _producer = producer
        logger.info("Kafka producer started (bootstrap=%s)", settings.KAFKA_BOOTSTRAP)
    except (asyncio.TimeoutError, Exception) as exc:
        logger.warning("Kafka unreachable; events will be dropped: %s", exc)
        _producer = None
        try:
            await producer.stop()
        except Exception:
            pass


async def stop_producer() -> None:
    global _producer
    if _producer is not None:
        try:
            await _producer.stop()
        except Exception as exc:
            logger.warning("Error stopping Kafka producer: %s", exc)
    _producer = None


async def publish(topic: str, event_type: str, payload: dict[str, Any]) -> None:
    if _producer is None:
        return
    event = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    try:
        await _producer.send(topic, json.dumps(event, default=str).encode())
    except Exception as exc:
        logger.warning("Kafka publish failed (topic=%s, event=%s): %s", topic, event_type, exc)
