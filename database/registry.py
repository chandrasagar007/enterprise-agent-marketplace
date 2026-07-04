# database/registry.py

# ==========================================
# 1. THE GLOBAL AGENT CATALOG (Marketplace)
# ==========================================
AGENT_CATALOG = {
    "research_agent": {
        "name": "research_agent",
        "description": "Call this agent for live web lookups, competitor research, and market trend analyses.",
        "tier": "basic"
    },
    "mentor_agent": {
        "name": "mentor_agent",
        "description": "Call this agent for strategic frameworks, consulting advice, mental models, or business planning.",
        "tier": "basic"
    },
    "coding_agent": {
        "name": "coding_agent",
        "description": "Call this agent to LIST files, inspect the local workspace, or READ code. STRICTLY READ-ONLY operations.",
        "tier": "pro"
    },
    "admin_coding_node": {
        "name": "admin_coding_node",
        "description": "Call this agent ONLY if the user explicitly asks to CREATE, WRITE, OVERWRITE, DELETE, or MODIFY files. Do NOT use this for reading or listing files.",
        "tier": "enterprise",
        "requires_hitl": True
    },
    "performance_agent": {
        "name": "performance_agent",
        "description": "Call this agent to audit execution times, break down system latency, check token usage, and analyze telemetry logs.",
        "tier": "enterprise"
    },
    # 🚀 NEW: Interview Copilot
    "interview_agent": {
        "name": "interview_agent",
        "description": "FAANG-Level AI PM Interview Copilot. Routes here ONLY when the user provides a Job Description (JD), asks to practice mock interviews, or wants to map their resume to a role.",
        "tier": "enterprise"
    }
}

# ==========================================
# 2. TENANT SUBSCRIPTIONS (The Paywall)
# ==========================================
TENANT_SUBSCRIPTIONS = {
    # Basic Tier: Can only do research and strategy. No coding allowed.
    "basic": [
        "research_agent", 
        "mentor_agent"
    ], 
    
    # Pro Tier: Unlocks safe codebase reading.
    "pro": [
        "research_agent", 
        "mentor_agent", 
        "coding_agent"
    ],
    
    # Enterprise Tier: Unlocks destructive file writing (HITL), telemetry, and Interview Copilot.
    "enterprise": [
        "research_agent", 
        "mentor_agent", 
        "coding_agent", 
        "admin_coding_node",
        "performance_agent",
        "interview_agent"  # 🚀 Unlocked for premium tenants
    ]
}

# ==========================================
# 3. MOCK DATABASE QUERY FUNCTIONS
# ==========================================
def get_active_agents_for_tenant(tenant_id: str) -> list[dict]:
    """
    Simulates a database JOIN operation.
    """
    active_agent_names = TENANT_SUBSCRIPTIONS.get(tenant_id, [])
    
    active_agents_metadata = []
    for name in active_agent_names:
        if name in AGENT_CATALOG:
            active_agents_metadata.append(AGENT_CATALOG[name])
            
    return active_agents_metadata

def format_agent_descriptions(active_agents: list[dict]) -> str:
    """
    Dynamically formats the "resume" text for the Supervisor's system prompt.
    """
    lines = []
    for agent in active_agents:
        lines.append(f"- '{agent['name']}': {agent['description']}")
    
    return "\n".join(lines)