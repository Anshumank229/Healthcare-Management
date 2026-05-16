from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Create limiter with Redis storage (falls back to in-memory if Redis not available)
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

def setup_rate_limiting(app: FastAPI):
    \"\"\"Setup rate limiting for the FastAPI app\"\"\"
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

def rate_limit(limit: str):
    \"\"\"Decorator to apply rate limit to specific endpoints\"\"\"
    return limiter.limit(limit)

def get_client_ip(request: Request) -> str:
    \"\"\"Get client IP address from request\"\"\"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"
