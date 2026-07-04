# 🤖 Enterprise Multi-Agent AI Platform (v11.0)

A production-grade, state-driven multi-agent AI orchestration platform. This project evolves from a simple single-agent chatbot into a fully governed, multi-tenant, asynchronous, Dockerized microservices backend equipped with **Model Context Protocol (MCP)** tool sandboxing and Human-in-the-Loop (HITL) execution controls.

---

## 🗺️ The 11-Level Architectural Journey

| Level | Milestone | Status |
| :--- | :--- | :--- |
| **0-3** | Basic Agent API, Logging, Auth, & Vector Memory | ✅ Done |
| **4** | LangGraph Orchestration & Domain-Isolated RAG | ✅ Done |
| **5** | Langfuse Observability & Cross-Domain Collaboration | ✅ Done |
| **6** | Agent Governance & Guardrails (Input/Output Gatekeepers) | ✅ Done |
| **7** | Human-in-the-Loop (HITL) Execution Freezes | ✅ Done |
| **8** | Multi-Tenant SaaS Data Isolation | ✅ Done |
| **9** | Agent Marketplace & Tier-Based Paywalls | ✅ Done |
| **10** | Asynchronous Decoupling (Redis Queue + SQLite Checkpointer)| ✅ Done |
| **11** | **Dockerized Microservices & 100% MCP Tool Sandboxing** | 🚀 **Live** |

---

## 🏗️ System Architecture

The platform operates via a completely decoupled, distributed microservice pattern:

```text
User
  ↓
Streamlit UI (Frontend)
  ↓
FastAPI (API Gateway + Auth + Tenant Routing)
  ↓
Redis Queue (Message Broker)
  ↓
RQ Worker (Background Asynchronous Execution)
  ↓
LangGraph Supervisor (LLM Traffic Router)
  ↓
┌──────────────┬──────────────┬──────────────┬──────────────┬──────────────┐
│ Coding Agent │Research Agent│ Mentor Agent │Support Agent │Interview Agt │
│ (MCP + RAG)  │(Tavily Search│(Mental Models│(Helpdesk)    │(Evaluations) │
└──────────────┴──────────────┴──────────────┴──────────────┴──────────────┘
  ↓
MCP Servers (Utility Server, Workspace Server, Knowledge Server)
  ↓
Domain-Isolated Memory (ChromaDB + Redis)
  ↓
Structured JSON Asynchronous Response



Key Enterprise Features:
100% MCP Decoupling: Tools are strictly sandboxed into dedicated Model Context Protocol servers (Utility, Workspace, Knowledge). Agents operate purely as cognitive clients requesting tools dynamically.

Asynchronous Execution (Zero Timeouts): Solves the standard 15s HTTP timeout problem. The API instantly returns a task_id while background RQ workers handle 30–60 second AI tasks.

Multi-Tenant Data Isolation: Every state execution, long-term vector memory, and chat history is mathematically siloed using a tenant_id:session_id composite key.

Human-In-The-Loop (HITL): Destructive actions (like writing/deleting code) automatically freeze execution. The graph state is serialized to SQLite until a human manager approves via the /chat/approve endpoint.

Agent Marketplace & Paywalls: A dynamic registry physically blocks basic-tier users from accessing enterprise-tier agents.


Project Structure:

Sample_Project/
├── app.py                      # FastAPI API Gateway
├── app_ui.py                   # Streamlit Frontend UI
├── tasks.py                    # RQ Worker: JIT graph compilation & execution
├── docker-compose.yml          # Container orchestration
├── Makefile                    # Unified build commands
│
├── agents/                     # LangGraph Cognitive Clients
│   ├── supervisor.py           # LLM Traffic Router
│   ├── admin_coding_agent.py   # Engineering worker (Write/Delete - HITL protected)
│   ├── coding_agent.py         # Engineering worker (Read-only MCP client)
│   ├── interview_agent.py      # Interview prep and evaluation worker
│   ├── research_agent.py       # Market intelligence worker
│   ├── mentor_agent.py         # Strategic advisor worker
│   └── performance_agent.py    # Telemetry auditor
│
├── mcp_servers/                # Model Context Protocol Sandboxes
│   ├── knowledge_server.py     # ChromaDB & Vector lifecycles
│   ├── utility_server.py       # Web search & calculators
│   └── workspace_server.py     # Local file read/write access
│
├── memory/                     # State & Persistence
│   ├── chroma_store.py         # Domain-isolated vector storage
│   ├── memory_store.py         # Long-term state handling
│   └── redis_store.py          # Short-term ephemeral memory
│
├── rag/                        # Retrieval-Augmented Generation
│   ├── career_data/            # PDF and document knowledge base
│   ├── data/                   # Strategic mental models
│   └── scripts/                # Ingestion pipelines (books, code, career)
│
├── middleware/                 # API Auth & Rate Limiting
├── database/                   # Agent Marketplace registry
├── utils/                      # Telemetry, logging, and token tracking
└── logs/                       # System logs (API, Redis, Worker, UI)

⚙️ Setup & Deployment

1. Clone the Repository
git clone [https://github.com/chandrasagar007/enterprise-agent-marketplace.git](https://github.com/chandrasagar007/enterprise-agent-marketplace.git)
cd enterprise-agent-marketplace/Sample_Project

2. Configure Environment Variables
Create a .env file in the Sample_Project root. Never commit this file.

OPENAI_API_KEY=sk-your-openai-api-key
TAVILY_API_KEY=tvly-your-tavily-api-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_HOST=[https://cloud.langfuse.com](https://cloud.langfuse.com)
REDIS_URL=redis://redis-1:6379/0
API_URL=http://api-1:8000

3. Start the Microservices (Docker)
The easiest way to boot the entire multi-container architecture (Redis, API, UI, Worker) is using the unified Makefile:
> make start
(Alternatively, run: docker compose up -d --build)

another method also to use the same terminal for these, if failed earlier
> docker compose build api --no-cache
> docker compose up -d
> docker compose logs -f
> docker compose down
(or)
> docker compose down --remove-orphans 

> make restart

4. Monitor the System
To view the aggregated real-time logs across all services:
make logs


🛠️ Tech Stack
Gateway: FastAPI, Uvicorn, Streamlit

Orchestration: LangGraph, LangChain, MCP (Model Context Protocol)

Asynchronous Workers: Redis, Redis Queue (RQ)

AI/LLM: OpenAI GPT-4o / GPT-3.5-turbo, Text-Embedding-3-small

Memory: ChromaDB, SQLite (Checkpointer)

DevOps: Docker, Docker Compose, Make

Observability: Langfuse








