🚀 Enterprise Multi-Agent Architecture — Level 10
A highly scalable, multi-tenant AI orchestration platform featuring dynamic agent routing,
tier-based paywalls, asynchronous execution, and enterprise-grade data isolation.

📖 Overview
This system routes user queries to a dynamic "Marketplace" of specialized AI agents — Coders, Researchers, Mentors, and Performance Auditors — while strictly enforcing:

✅ Tier-based paywalls (basic / pro / enterprise)
✅ Per-tenant token limits
✅ Complete multi-tenant data isolation
To prevent HTTP timeouts during heavy AI processing (30–60s), the system uses a Distributed Asynchronous Polling Architecture via Redis and background workers.

🧠 The "Why" — Evolution to Level 10
The Problem
Initially, the API processed LangGraph agents synchronously. AI tasks (web scraping, file analysis) regularly take 30–60 seconds. Standard HTTP servers (Vercel, AWS API Gateway, Nginx) forcefully drop connections after 10–15 seconds → 504 Gateway Timeout.

The Solution: Asynchronous Decoupling
Instead of making the user wait for the AI to finish, the API instantly returns a Task ID receipt. A background worker handles the heavy LangGraph execution while the client polls a status endpoint to retrieve the final answer.

Before (Synchronous):          After (Async Level 10):
  POST /chat                     POST /chat
  [user waits 60s...]            ← returns task_id in 0.1s
  ← final answer                 [worker processes in background]
  ← 504 Timeout ❌               GET /chat/status/{task_id}
                                  ← final answer ✅
✨ Core Features
1 — Agent Marketplace & Dynamic Paywalls
A dynamic registry (database/registry.py) acts as the agent storefront:

Agents are registered with specific job descriptions and assigned to pricing tiers (basic, pro, enterprise)
The Supervisor LLM dynamically reads the catalog and routes tasks to the appropriate worker
A Python Bouncer intercepts routing decisions — if a basic user attempts to invoke an enterprise agent, execution is physically blocked and a paywall message is returned
2 — Asynchronous Execution (Zero Timeouts)
Endpoint	Behaviour
POST /chat	Instantly accepts request, drops it in Redis Queue, returns task_id in ~0.1s
Background Worker	Silently executes heavy LangGraph task in an isolated process
GET /chat/status/{task_id}	Client polls this endpoint to retrieve the final answer
3 — Human-In-The-Loop (HITL)
Destructive actions (e.g., admin_coding_node attempting to write or delete local files) are automatically frozen by LangGraph
The graph pauses and saves its state to an SQLite database
Execution resumes only after a human manager hits the POST /chat/approve endpoint
4 — Performance Telemetry Auditing
A dedicated performance_agent has tools to physically read logs/api.log
Premium users can ask the system to audit its own performance — latency, token usage, and per-node execution times
5 — Multi-Tenant Data Isolation
Every state execution and chat memory is tagged with a composite key:

tenant_id:session_id
"Company A" mathematically cannot access the conversation history, codebase, or context window of "Company B." ✅

🏗️ System Architecture
The system is broken into 4 decoupled micro-components:

┌─────────────────────────────────────────────────────────────┐
│                      CLIENT REQUEST                         │
└──────────────────────────┬──────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  FastAPI  (app.py)                                           │
│  • Authentication (x-api-key)                               │
│  • Rate Limiting (SlowAPI)                                   │
│  • Token Counting (tiktoken)                                 │
│  • Enqueues task → Redis                                     │
│  • Returns HTTP 202 + task_id instantly                      │
└──────────────────────────┬───────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  Redis Server  (Message Broker / Post Office)                │
│  • Holds task queue between API and Worker                   │
└──────────────────────────┬───────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  RQ Worker  (tasks.py)  — The Heavy Lifter                   │
│  • Pulls tasks from Redis                                    │
│  • Compiles LangGraph dynamically (JIT — see note below)     │
│  • Loads .env API keys                                       │
│  • Runs AI agents                                            │
└──────────────────────────┬───────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  SQLite Checkpointer  (langgraph_checkpoints.sqlite)         │
│  • Shared memory between API process and Worker process      │
│  • Stores LangGraph thread states for HITL pausing           │
└──────────────────────────────────────────────────────────────┘


🔄 Full Data Flow
1.  User           →  POST /chat  (prompt + session_id + tenant_id)
2.  FastAPI        →  Drops payload into Redis Queue
                   →  Returns HTTP 202 + { "task_id": "abc123" }  ← instant
3.  RQ Worker      →  Picks up task abc123
                   →  Opens SQLite connection (JIT)
                   →  Loads OPENAI_API_KEY from .env
                   →  Starts guard_node
4.  Supervisor     →  Checks tenant_id + pricing tier
                   →  Reads Agent Marketplace catalog
                   →  Routes to research_agent
5.  Research Agent →  Executes Tavily web search
                   →  Writes final answer to SQLite
                   →  Exits cleanly
6.  User           →  GET /chat/status/abc123
7.  FastAPI        →  Checks Redis → job complete
                   →  Returns final answer ✅



⚠️ Architectural Decision: The JIT Fix
Why is LangGraph compiled dynamically in tasks.py instead of globally in supervisor.py?
The Problem (macOS fork-safety crash):

When a parent process (Redis Queue) opens a global database connection (SQLite) or a global socket (OpenAI httpx client), and then uses os.fork() to create a background worker — macOS deliberately crashes the program to prevent memory thread-leaks:

objc[12345]: +[NSCFConstantString initialize] may have been in progress in
another thread when fork() was called — crash ❌
The Fix — Just-In-Time (JIT) Compilation:

python
Copy
# ❌ WRONG — global connection (crashes on macOS fork)
checkpointer = SqliteSaver.from_conn_string("langgraph_checkpoints.sqlite")
graph = workflow.compile(checkpointer=checkpointer)

# ✅ CORRECT — JIT connection inside the worker task
def run_agent_task(payload):
    with sqlite3.connect("langgraph_checkpoints.sqlite") as conn:
        checkpointer = SqliteSaver(conn)
        graph = workflow.compile(checkpointer=checkpointer)
        result = graph.invoke(payload)
    # connection closed cleanly after block ✅
supervisor.py ships the graph completely uncompiled. The RQ Worker opens the DB connection, compiles, executes, and closes — all within a Python context manager.


📂 Project Structure
Sample_Project/
│
├── app.py                        # FastAPI: auth, rate limiting, enqueue, polling
├── tasks.py                      # RQ Worker: JIT graph compilation + LangGraph execution
│
├── agents/
│   ├── supervisor.py             # LLM Traffic Router (reads marketplace + routes)
│   ├── coding_agent.py           # Software engineering worker (Codebase RAG)
│   ├── research_agent.py         # Market intelligence worker (Tavily Search)
│   ├── mentor_agent.py           # Strategic advisor worker (Mental Models RAG)
│   ├── support_agent.py          # General troubleshooting worker
│   └── performance_agent.py      # Telemetry auditor (reads logs/api.log)
│
├── database/
│   └── registry.py               # Agent Marketplace: job descriptions + tier assignments
│
├── memory/
│   ├── chroma_store.py           # Long-term domain-isolated vector storage
│   └── redis_store.py            # Short-term ephemeral conversation state
│
├── rag/
│   ├── data/                     # Source PDFs and text files for Mentor Agent
│   └── scripts/
│       ├── ingest_code.py        # Pipeline: chunk + embed local codebase
│       └── ingest_books.py       # Pipeline: chunk + embed strategic frameworks
│
├── middleware/                   # Auth + validation rules
├── utils/                        # Token counters + loggers
├── logs/
│   └── api.log                   # Structured request logs (read by performance_agent)
├── langgraph_checkpoints.sqlite  # Shared HITL state store (API ↔ Worker)
└── .env                          # API Keys (OpenAI, Tavily)


🧰 Tech Stack
Layer	Technology
API Server	FastAPI + Uvicorn
Orchestration	LangGraph + LangChain
LLM	OpenAI gpt-3.5-turbo
Embeddings	OpenAI text-embedding-3-small
Vector DB (Long-term Memory + RAG)	ChromaDB
Task Queue / Message Broker	Redis + RQ (Redis Queue)
Short-term Session Cache	Redis
HITL State Persistence	SQLite (langgraph_checkpoints.sqlite)
Web Search	Tavily API
Rate Limiting	slowapi
Token Counting	tiktoken
Environment Management	uv + python-dotenv
Public Tunnel	Ngrok


######
🚀 Running the Platform (Local Dev)
This is a distributed system — you need 4 separate terminal windows running simultaneously.

Prerequisite: Ensure .env contains OPENAI_API_KEY=your_key_here and TAVILY_API_KEY=your_key_here



Terminal 1 — Start the Message Broker (Redis)
bash
Copy
> redis-server
Keeps the task queue alive to pass messages between the API and the Worker.

Terminal 2 — Start the AI Worker (RQ)
bash
Copy
> export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
> rq worker enterprise_tasks
Executes the heavy LangGraph logic.
The export command bypasses the macOS SecureTransport fork-safety crash during local dev.

Terminal 3 — Start the Web Server (FastAPI)
bash
Copy
> uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
Runs the lightning-fast API endpoints. Open Swagger UI at http://127.0.0.1:8000/docs

Terminal 4 — Expose to the Internet (Ngrok)
bash
Copy
> ngrok http 8000


Creates a public HTTPS URL for Webhooks, Postman, or Frontend UI testing.

🔌 API Reference
Method	Endpoint	Description	Auth
POST	/chat	Submit a task → returns task_id instantly	✅
GET	/chat/status/{task_id}	Poll for final answer	✅
POST	/chat/approve	Approve a HITL-frozen destructive action	✅
Example: Submit a Task
bash
Copy
curl -X POST "http://localhost:8000/chat" \
  -H "x-api-key: your_secure_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_001",
    "tenant_id": "company_a",
    "question": "Research the top 3 competitors of Notion in 2025."
  }'
Response (instant — ~0.1s):

json
Copy
{
  "status": "queued",
  "task_id": "abc123-xyz"
}
Example: Poll for Result
bash
Copy
curl "http://localhost:8000/chat/status/abc123-xyz" \
  -H "x-api-key: your_secure_api_key"
Response (when complete):

json
Copy
{
  "status": "complete",
  "answer": "The top 3 competitors of Notion in 2025 are...",
  "execution_time": "14.2s",
  "agent_used": "research_agent",
  "token_usage": 1842
}
🛠️ How to Add a New Agent
The architecture is fully modular — no changes to core routing logic required.

Step 1 — Create the Agent
Create a new file in agents/ (e.g., financial_agent.py):

python
Copy
from langchain.agents import create_react_agent

financial_agent = create_react_agent(llm, tools=[...], prompt=...)
Step 2 — Register in the Marketplace
Add its job description and tier in database/registry.py:

python
Copy
{
  "name": "financial_agent",
  "description": "Analyzes financial statements, revenue models, and investment frameworks.",
  "tier": "enterprise"
}
Step 3 — Wire into the Supervisor
Add a wrapper node in agents/supervisor.py and map it in workflow.add_edge():

python
Copy
workflow.add_node("financial_agent", run_financial_agent)
workflow.add_conditional_edges("supervisor", route_to_agent)
✅ The Supervisor LLM dynamically reads the new registry entry and immediately routes matching tasks to your new agent — no further changes needed.

🧠 Agent Marketplace
Agent	Domain	Tier	Tools
coding_agent	Software Engineering	basic+	search_codebase (RAG), Calculator
research_agent	Market Intelligence	pro+	Tavily Search
mentor_agent	Strategic Advisory	pro+	search_mental_models (RAG)
performance_agent	Telemetry Auditing	enterprise	Reads logs/api.log
support_agent	General Troubleshooting	basic+	LLM reasoning
🔧 Troubleshooting
Port 8000 already in use:

bash
Copy
lsof -i :8000
kill -9 <PID>
RQ Worker crashing on macOS (fork-safety error):

bash
Copy
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
rq worker enterprise_tasks
Redis not connecting:

bash
Copy
brew services start redis      # macOS
sudo systemctl start redis     # Linux
redis-cli ping                 # Expected: PONG
Tasks stuck in queue (never completing):

bash
Copy
# Check worker is running
rq info

# Flush the queue and retry
rq empty enterprise_tasks