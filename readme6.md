# 🚀 Enterprise Multi-Agent Platform: Architecture & Evolution

## 📖 Overview
This project is a highly scalable, multi-tenant AI orchestration platform. It is designed to route user queries to a dynamic "Marketplace" of specialized AI agents while strictly enforcing tier-based paywalls, token limits, and data isolation.

We engineered this platform using an **11-Level Maturity Model**, systematically solving production bottlenecks at every stage, culminating in a fully distributed, asynchronous architecture with a streamlined Developer Experience (DX).

---

## 🧗 The 11 Levels of Architecture Implementation

### Level 1: The Foundation (LLM Call)
- **What we built:** A basic LangChain script connecting to OpenAI.
- **The Problem Solved:** Establishing basic intelligence (text-in, text-out generator).

### Level 2: Conversational Memory
- **What we built:** Implemented `MemorySaver` and message arrays.
- **The Problem Solved:** Allowed the AI to remember the context of the conversation.

### Level 3: Tool Use & ReAct Framework
- **What we built:** Transitioned to `create_react_agent` with physical Python tools.
- **The Problem Solved:** Gave the AI "hands" to read local files, scrape the web, and execute code.

### Level 4: LangGraph Orchestration (The Supervisor)
- **What we built:** Introduced `StateGraph` to split the monolithic agent into specialized workers managed by a central Supervisor LLM.
- **The Problem Solved:** Drastically increased accuracy and enabled cross-domain collaboration by routing tasks to domain experts.

### Level 5: Governance Firewalls
- **What we built:** Added `guard_node` (Input) and `output_guard_node` (Egress).
- **The Problem Solved:** Protected against prompt injections, illegal requests, and scrubbed API keys from final responses.

### Level 6: API Framework (FastAPI)
- **What we built:** Wrapped the LangGraph execution inside a FastAPI application.
- **The Problem Solved:** Turned a terminal script into a consumable web service with API Key authentication.

### Level 7: Human-In-The-Loop (HITL)
- **What we built:** Configured LangGraph to `interrupt_before` destructive nodes and built a `/chat/approve` endpoint.
- **The Problem Solved:** Froze execution before dangerous actions (like writing/deleting code) to await human manager approval.

### Level 8: Multi-Tenant SaaS & Telemetry
- **What we built:** Introduced `tenant_id`, SlowAPI rate limiting, and isolated LangGraph thread memory using a composite key (`tenant_id:session_id`).
- **The Problem Solved:** Mathematically isolated data between different companies (tenants) and tracked token usage.

### Level 9: The Agent Marketplace & Paywalls
- **What we built:** Created `database/registry.py` and a dynamic Python paywall block.
- **The Problem Solved:** Established `basic`, `pro`, and `enterprise` tiers, physically blocking users from accessing agents they haven't paid for.

### Level 10: Asynchronous Enterprise Workers (Decoupling)
- **What we built:** Integrated **Redis Queue (RQ)** and a `SqliteSaver` checkpointer.
- **The Problem Solved:** Decoupled the slow AI execution from the fast HTTP API. FastAPI now returns a `task_id` in 0.1 seconds, preventing `504 Gateway Timeouts` while the worker processes the AI request in the background.

### Level 11: Developer Experience (DX)
- **What we built:** A unified `Makefile` and a suite of bash scripts (`start.sh`, `stop.sh`, `status.sh`).
- **The Problem Solved:** Eliminated the "5-terminal chaos." Developers can now spin up, monitor, and tear down the entire distributed architecture with a single command.

---

## 🏗️ System Architecture

Our distributed system operates via **4 Micro-Components**:

1. **FastAPI (`app.py`):** The lightning-fast front door. Drops payloads into Redis and instantly returns `HTTP 202` with a `task_id`.
2. **Redis Server:** The message broker routing tasks between the API and the Worker.
3. **RQ Worker (`tasks.py`):** The background brain. Pulls tasks from Redis, opens a Just-In-Time (JIT) SQLite connection, and runs the AI agents safely.
4. **SQLite Checkpointer:** The shared memory drive passing LangGraph thread states between the API and Worker processes.

Optional components: Streamlit for frontend visualization and Ngrok for public webhook exposure.

---

## 🚀 How to Run the Platform (Developer Workflow)

### Start All Services
```bash
make start
```
Starts Redis, RQ Worker, FastAPI, Streamlit, and Ngrok in the background.

### Check System Health
```bash
make status
```

### View Live Logs
```bash
make logs
```
Press `Ctrl+C` to stop viewing logs.

### Shut Down
```bash
make stop
```

## ⚠️ Troubleshooting: Hard Reset

```bash
# Force kill services on common ports
lsof -ti:8000 | xargs kill -9
lsof -ti:8501 | xargs kill -9
lsof -ti:6379 | xargs kill -9

# Kill worker and ngrok
pkill -f rq
pkill -f ngrok

# Clean PID files and logs
make clean
```
####
🛠️ How to Add a New Agent
Our architecture is entirely modular. You never have to touch the API to add a new worker.

Create a new Python file in agents/ (e.g., financial_agent.py) and wrap it in create_react_agent.

Add its "job description" and pricing tier to database/registry.py.

Add a wrapper node function in agents/supervisor.py and wire it into the workflow map.