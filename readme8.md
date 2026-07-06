# README 8: Enterprise Agent Marketplace

# Enterprise Agent Marketplace (Multi-Tenant Agentic Architecture)

An enterprise-grade, asynchronous AI agent orchestration platform built with FastAPI, LangGraph, Streamlit, Redis Queue (RQ), and Docker. The platform isolates tenant data, executes long-running AI workflows asynchronously, persists vector knowledge through ChromaDB, and scales through a decoupled microservice architecture.

## Highlights

- Multi-tenant architecture with tenant isolation
- Asynchronous AI execution using Redis Queue (RQ)
- LangGraph-based agent orchestration
- Streamlit web interface
- FastAPI orchestration gateway
- ChromaDB vector storage
- Docker Compose deployment
- MCP-ready worker architecture
- External tool integrations (OpenAI, Tavily)
- Optional Langfuse observability

## Architecture

```
User
  |
Streamlit UI
  |
FastAPI API Gateway
  |
Redis Queue (Broker)
  |
RQ Worker
  |
LangGraph Supervisor
  |
Specialized Agents
  |
MCP Servers / External APIs / ChromaDB
```

## Microservices

### UI (Streamlit)
- Chat interface
- Session management
- Background polling
- Displays asynchronous task status

### API (FastAPI)
- Authentication and request validation
- Tenant-aware routing
- Creates background jobs
- Returns task identifiers immediately

### Redis
- RQ message broker
- Session isolation using `tenant_id:session_id`
- Queue management

### Worker (RQ)
- Executes LangGraph workflows
- Performs tool execution
- Connects to MCP servers
- Handles web search and vector retrieval

## Technology Stack

- FastAPI
- Streamlit
- LangGraph
- Redis
- Redis Queue (RQ)
- ChromaDB
- Docker Compose
- OpenAI
- Tavily
- Langfuse (optional)

## Environment Configuration

Create a `.env` file.

```ini
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

REDIS_URL=redis://redis-1:6379/0
```

## Docker Deployment

The deployment consists of four primary containers:

- `redis-1`
- `api-1`
- `worker-1`
- `ui-1`

Persistent volumes:

- `redis_data`
- `chroma_data`

All services communicate through the `agent_network` bridge network.

## Deployment Workflow

### Stop existing environment

```bash
docker compose down --remove-orphans
```

### Build fresh images

```bash
docker compose build --no-cache
```

### Start all services

```bash
docker compose up -d
```

## Monitoring

### Worker and API logs

```bash
docker compose logs -f worker-1 api-1
```

### Logs for all services

```bash
docker compose logs -f
```

## Troubleshooting

### Long-running tasks

Symptoms:

- UI timeout while worker continues processing.
- Worker logs show repeated tool calls.

Typical cause:

Large prompts that require many sequential tool invocations and LLM requests can exceed the frontend polling timeout.

Recommended solution:

1. Increase the polling timeout in `app_ui.py` from 300 seconds to 600 or 900 seconds.
2. Rebuild the UI container.

```bash
docker compose build ui

docker compose up -d ui
```

### Reset stuck queues

```bash
docker compose down

docker volume rm sample_project_redis_data

docker compose up -d

docker compose logs -f  
```

## Operational Flow

1. User submits a prompt through Streamlit.
2. FastAPI validates the request.
3. A background task is pushed into Redis.
4. RQ Worker consumes the task.
5. LangGraph coordinates specialized agents.
6. Agents access MCP tools, ChromaDB, or external APIs.
7. Results are returned to the UI asynchronously.

## Production Benefits

- Horizontal worker scaling
- Tenant isolation
- Non-blocking API requests
- Persistent vector knowledge
- Containerized deployment
- Easy observability with Langfuse
- Clean separation between UI, API, queue, and execution engine


### git commands
git status
git add .
git commit -m "feat: Complete Phase 4 Enterprise Agent Marketplace with DSPy Macro-Learning, MCP Tools, and UI HITL Approval"
git push origin main