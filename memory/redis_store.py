import json
import os
import redis

# ✅ DYNAMIC FIX: Leverages Docker network path if present, falls back to local machine defaults
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.Redis.from_url(
    redis_url,
    decode_responses=True
)

def get_history(session_id: str, tenant_id: str):
    # LEVEL 8: Prefix the key to physically isolate tenant data in Redis
    redis_key = f"{tenant_id}:{session_id}"
    data = redis_client.get(redis_key)

    if data:
        return json.loads(data)

    return []

def save_message(
    session_id: str,
    tenant_id: str,
    role: str,
    content: str
):
    redis_key = f"{tenant_id}:{session_id}"
    history = get_history(session_id, tenant_id)

    history.append(
        {
            "role": role,
            "content": content
        }
    )

    redis_client.setex(
        redis_key,
        86400,
        json.dumps(history)
    )