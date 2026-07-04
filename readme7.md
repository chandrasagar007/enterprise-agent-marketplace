# Phase 7: 100% MCP Compliance & System Orchestration

## Overview
Phase 7 marks the transition of the Enterprise Agent Marketplace from a monolithic script into a production-grade, distributed microservice architecture. This phase resolved terminal chaos by introducing a unified build system and completely decoupled the agent's cognitive logic from the physical infrastructure using the Model Context Protocol (MCP).

## Key Achievements & Architectural Changes

### 1. The Unified Build System (`make start`)
We eliminated the "5-Terminal Chaos" (running Redis, Workers, FastAPI, Streamlit, and Ngrok manually) by implementing a robust `Makefile` and a bash orchestration script.

- **`make start`**: Silently boots Redis, spins up background RQ workers, launches the FastAPI backend, starts the Streamlit UI, and exposes the system via Ngrok—all in a single command.
- **`make logs`**: A unified command that utilizes `tail -f` to stream the logs of all 5 services into a single, beautifully consolidated terminal view for real-time debugging.
- **`make stop` & `make restart`**: Graceful teardown mechanisms to kill hanging ports and refresh system state cleanly.

### 2. The 100% MCP Decoupling (Tool Sandboxing)
We permanently deleted the monolithic `tools.py` file. All tools have been strictly sandboxed into three dedicated Model Context Protocol (MCP) servers. The LangGraph agents now operate purely as cognitive clients that request tools dynamically over secure `stdio` streams.

#### A. The Utility Server (`mcp_servers/utility_server.py`)
- **Role**: Handles all stateless, external interactions.
- **Tools**: `search_web` (Tavily API), `calculator`.

#### B. The Workspace Server (`mcp_servers/workspace_server.py`)
- **Role**: The physical OS sandbox. Prevents agents from roaming the host machine.
- **Tools**: `list_workspace_files`, `read_local_file`, `write_local_file`, `delete_local_file`, `read_telemetry_logs`.
- **Security**: Enforces strict path traversal blocks, ensuring tools can only operate within the exact `WORKSPACE_DIR`.

#### C. The Knowledge Server (`mcp_servers/knowledge_server.py`)
- **Role**: The heavy-data lifecycle manager. Owns the vector database footprint so worker nodes remain lightweight.
- **Tools**: `search_codebase`, `search_mental_models`, `search_career_history`, `read_master_career_profile`.
- **Infrastructure**: Manages the persistent ChromaDB connection and OpenAI embedding functions exclusively.

### 3. Overcoming "Context Bleed" (The `contextvars` Innovation)
Migrating to MCP introduced a severe architectural clash: LangGraph's supervisor relies on a synchronous SQLite Checkpointer (`SqliteSaver`), but MCP tools execute asynchronously.

- **The Problem**: Nesting the async MCP client inside the sync LangGraph node caused Python's execution context to bleed, crashing the worker with an async SQLite locking error.
- **The Solution**: We implemented a **Context Isolation Bubble** using Python's native `contextvars.Context()`.

```python
# The Context Isolation Pattern
ctx = contextvars.Context()
answer = ctx.run(asyncio.run, run_mcp_agent(enhanced_question))
```

This entirely isolates the inner async MCP execution loop from the outer LangGraph state, ensuring flawless bridging between the sync orchestrator and async tools.

### 4. Advanced Multi-Server Client Execution
The `mentor_agent` was upgraded to perform simultaneous, dual-server handshakes. It connects to both the `utility_server` (for live web data) and the `knowledge_server` (for internal frameworks) at the same time, fusing the toolsets dynamically before executing the ReAct loop.

## The New Execution Flow

1. User Input ➔ Streamlit UI
2. Task Queue ➔ Redis / RQ Worker
3. Orchestrator ➔ LangGraph Supervisor Node (Synchronous)
4. Security Check ➔ Guard Node & Tenant Registry (Blocks unauthorized access to destructive Admin nodes)
5. Agent Handoff ➔ Specialized Agent (e.g., `research_agent`)
6. Context Bubble ➔ Spins up `asyncio` inside `contextvars`
7. MCP Handshake ➔ Establishes `stdio` connection to the designated MCP Server(s).
8. Execution ➔ MCP Server runs the physical tool and returns data to the Agent.
9. Final Delivery ➔ UI renders the synthesized result.

## How to Run the System

### Start the entire ecosystem
```bash
make start
```

### Monitor all background processes
```bash
make logs
```

### Shut down cleanly
```bash
make stop
```

### Restart the system
```bash
make restart
```
