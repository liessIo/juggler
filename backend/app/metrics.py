# backend/app/metrics.py

from prometheus_client import Counter, Histogram, Gauge
import time

# Authentication metrics
login_attempts = Counter('login_attempts_total', 'Total login attempts', ['status'])
active_sessions = Gauge('active_sessions', 'Number of active sessions')
token_refreshes = Counter('token_refreshes_total', 'Total token refreshes')

# Security metrics
blocked_requests = Counter('blocked_requests_total', 'Total blocked requests', ['reason'])
suspicious_activities = Counter('suspicious_activities_total', 'Total suspicious activities', ['type'])

# Performance metrics
request_duration = Histogram('request_duration_seconds', 'Request duration', ['endpoint'])

def track_request_duration(endpoint: str):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            duration = time.time() - start
            request_duration.labels(endpoint=endpoint).observe(duration)
            return result
        return wrapper
    return decorator