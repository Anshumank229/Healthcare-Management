import time
import threading
import logging
from app.core.redis_client import redis_client
from app.services.whatsapp_service import whatsapp_service

logger = logging.getLogger(__name__)


def process_retry_queue():
    """Background worker to process failed WhatsApp messages"""
    while True:
        try:
            # Process delayed messages
            processed = redis_client.process_delayed_messages()
            if processed:
                logger.info(f"Processed {processed} delayed messages")

            # Get next message to retry
            message = redis_client.get_next_retry()
            if message:
                to_number = message.get("to_number")
                message_text = message.get("message")
                retry_count = message.get("retry_count", 0)

                logger.info(f"Retrying message to {to_number} (attempt {retry_count + 1})")

                try:
                    result = whatsapp_service.send_text_message(to_number, message_text)
                    if "error" not in result:
                        logger.info(f"Successfully sent retry message to {to_number}")
                    else:
                        redis_client.requeue_with_delay(message)
                except Exception as e:
                    logger.error(f"Retry failed: {e}")
                    redis_client.requeue_with_delay(message)

            time.sleep(5)  # Check every 5 seconds

        except Exception as e:
            logger.error(f"Retry worker error: {e}")
            time.sleep(10)


def start_retry_worker():
    """Start the background retry worker thread"""
    worker_thread = threading.Thread(target=process_retry_queue, daemon=True)
    worker_thread.start()
    logger.info("✅ WhatsApp retry worker started")