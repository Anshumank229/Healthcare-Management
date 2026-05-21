import redis
import json
import logging
from datetime import timedelta
from typing import Optional, Any
from dotenv import load_dotenv
import os

load_dotenv()
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Cache TTL constants (in seconds)
CACHE_TTL_AVAILABILITY = 300  # 5 minutes
CACHE_TTL_DOCTOR = 3600  # 1 hour
CACHE_TTL_SESSION = 1800  # 30 minutes
CACHE_TTL_OTP = 300  # 5 minutes

# Retry queue constants
RETRY_QUEUE_NAME = "whatsapp_retry_queue"
MAX_RETRIES = 3
RETRY_DELAYS = [60, 300, 900]  # 1 minute, 5 minutes, 15 minutes


class RedisClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Initialize Redis connection"""
        try:
            self.client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.warning(f"⚠️ Redis connection failed: {e}. Using fallback (no caching)")
            self.client = None

    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.client is not None

    # ========== CACHE METHODS ==========

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available():
            return None
        try:
            value = self.client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache"""
        if not self.is_available():
            return False
        try:
            serialized = json.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_available():
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.is_available():
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Redis clear pattern error: {e}")
            return 0

    # ========== DOCTOR AVAILABILITY CACHING ==========

    def get_doctor_availability(self, doctor_id: int, date: str) -> Optional[list]:
        """Get cached doctor availability"""
        key = f"doctor:availability:{doctor_id}:{date}"
        return self.get(key)

    def set_doctor_availability(self, doctor_id: int, date: str, slots: list,
                                ttl: int = CACHE_TTL_AVAILABILITY) -> bool:
        """Cache doctor availability"""
        key = f"doctor:availability:{doctor_id}:{date}"
        return self.set(key, slots, ttl)

    def invalidate_doctor_availability(self, doctor_id: int):
        """Invalidate all availability caches for a doctor"""
        return self.clear_pattern(f"doctor:availability:{doctor_id}:*")

    # ========== DOCTOR INFO CACHING ==========

    def get_doctor(self, doctor_id: int) -> Optional[dict]:
        """Get cached doctor info"""
        key = f"doctor:{doctor_id}"
        return self.get(key)

    def set_doctor(self, doctor_id: int, doctor_data: dict, ttl: int = CACHE_TTL_DOCTOR) -> bool:
        """Cache doctor info"""
        key = f"doctor:{doctor_id}"
        return self.set(key, doctor_data, ttl)

    # ========== SESSION CACHING ==========

    def cache_session(self, user_id: int, token: str, user_data: dict, ttl: int = CACHE_TTL_SESSION) -> bool:
        """Cache user session"""
        key = f"session:{user_id}:{token[:20]}"
        return self.set(key, user_data, ttl)

    def get_session(self, user_id: int, token: str) -> Optional[dict]:
        """Get cached session"""
        key = f"session:{user_id}:{token[:20]}"
        return self.get(key)

    def invalidate_session(self, user_id: int):
        """Invalidate all sessions for a user"""
        return self.clear_pattern(f"session:{user_id}:*")

    # ========== OTP CACHING ==========

    def store_otp(self, phone: str, otp: str, ttl: int = CACHE_TTL_OTP) -> bool:
        """Store OTP for verification"""
        key = f"otp:{phone}"
        return self.set(key, {"otp": otp, "attempts": 0}, ttl)

    def verify_otp(self, phone: str, otp: str) -> bool:
        """Verify OTP"""
        key = f"otp:{phone}"
        data = self.get(key)
        if not data or data.get("otp") != otp:
            return False
        self.delete(key)
        return True

    def increment_otp_attempts(self, phone: str) -> int:
        """Increment OTP verification attempts"""
        key = f"otp:{phone}"
        data = self.get(key)
        if data:
            attempts = data.get("attempts", 0) + 1
            data["attempts"] = attempts
            self.set(key, data)
            return attempts
        return 0

    # ========== WEBHOOK RETRY QUEUE ==========

    def add_to_retry_queue(self, message_data: dict) -> bool:
        """Add failed webhook message to retry queue"""
        if not self.is_available():
            return False
        try:
            import time
            message_data["queued_at"] = time.time()
            message_data["retry_count"] = 0
            self.client.lpush(RETRY_QUEUE_NAME, json.dumps(message_data))
            logger.info(f"Added message to retry queue: {message_data.get('to_number', 'unknown')}")
            return True
        except Exception as e:
            logger.error(f"Add to retry queue error: {e}")
            return False

    def get_next_retry(self) -> Optional[dict]:
        """Get next message to retry"""
        if not self.is_available():
            return None
        try:
            item = self.client.rpop(RETRY_QUEUE_NAME)
            return json.loads(item) if item else None
        except Exception as e:
            logger.error(f"Get next retry error: {e}")
            return None

    def requeue_with_delay(self, message_data: dict) -> bool:
        """Re-queue message with updated retry count"""
        if not self.is_available():
            return False
        try:
            import time
            retry_count = message_data.get("retry_count", 0) + 1

            if retry_count >= MAX_RETRIES:
                logger.error(f"Message failed after {MAX_RETRIES} retries: {message_data.get('to_number', 'unknown')}")
                return False

            message_data["retry_count"] = retry_count
            delay = RETRY_DELAYS[retry_count - 1] if retry_count <= len(RETRY_DELAYS) else 300
            message_data["retry_at"] = time.time() + delay

            # Add to delayed queue (using sorted set for delayed processing)
            self.client.zadd("whatsapp_delayed_queue", {json.dumps(message_data): message_data["retry_at"]})
            logger.info(f"Re-queued message for retry {retry_count} in {delay}s")
            return True
        except Exception as e:
            logger.error(f"Requeue error: {e}")
            return False

    def process_delayed_messages(self) -> int:
        """Process messages whose retry time has come"""
        if not self.is_available():
            return 0
        try:
            import time
            now = time.time()
            # Get all messages ready for retry
            items = self.client.zrangebyscore("whatsapp_delayed_queue", 0, now)
            processed = 0
            for item in items:
                # Move back to main queue
                self.client.lpush(RETRY_QUEUE_NAME, item)
                self.client.zrem("whatsapp_delayed_queue", item)
                processed += 1
            return processed
        except Exception as e:
            logger.error(f"Process delayed messages error: {e}")
            return 0

    # ========== RATE LIMITING (Distributed) ==========

    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Check if rate limit exceeded (distributed)"""
        if not self.is_available():
            return True  # Allow if Redis unavailable
        try:
            current = self.client.incr(key)
            if current == 1:
                self.client.expire(key, window)
            return current <= limit
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True


# Singleton instance
redis_client = RedisClient()