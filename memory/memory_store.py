# memory/memory_store.py

conversation_memory = {}

def get_history(session_id: str, tenant_id: str):
    key = f"{tenant_id}:{session_id}"
    return conversation_memory.get(key, [])

def save_message(
    session_id: str,
    tenant_id: str,
    role: str,
    content: str
):
    key = f"{tenant_id}:{session_id}"
    if key not in conversation_memory:
        conversation_memory[key] = []

    conversation_memory[key].append(
        {
            "role": role,
            "content": content
        }
    )