# Enterprise Multi-Agent Orchestration Platform (v8.0)

## Overview
This repository contains a production-grade, state-driven multi-agent AI platform built with FastAPI and LangGraph. It has evolved from a basic parallel-agent script into a secure, multi-tenant SaaS backend equipped with Human-in-the-Loop (HITL) execution controls, domain-isolated memory vaults, and strict input/output governance.

---

## 🏗️ Architecture Evolution & Execution Steps

### Step 1: Observability & Collaborative Orchestration (Level 5)
* **The Goal:** Move from parallel agent execution to a collaborative pipeline with full telemetry.
* **What was executed:**
    * Integrated **Langfuse v3** to trace LLM executions, token usage, and latency.
    * Refactored the `supervisor_node` to enforce **Cross-Domain Collaboration**, ensuring agents chain their work (e.g., Coding Agent reads files ➡️ Mentor Agent analyzes the code).
    * Implemented `build_collaborative_prompt` so worker agents share context natively through the `AgentState`.

### Step 2: Agent Governance & Guardrails (Level 6)
* **The Goal:** Protect the system from malicious users (prompt injection) and protect the users from the system (data leaks).
* **What was executed:**
    * **Input Gatekeeper (`guard_node`):** Added a pre-processing node to instantly reject prompt injections, dangerous requests, and off-topic domain breaches before waking up expensive worker agents.
    * **Output Gatekeeper (`output_guard_node`):** Added a post-processing egress filter right before the `END` node to format markdown, suppress raw Python crashes, and automatically redact exposed API keys (e.g., replacing `sk-...` with `[REDACTED_KEY]`).
    * **Meta-Query Balance:** Tuned the Supervisor to gracefully handle conversational chit-chat and session history requests without triggering security false alarms.

### Step 3: Production Tooling & Human-in-the-Loop (Level 7)
* **The Goal:** Give agents physical tools (web search, file system access) while preventing autonomous destructive actions.
* **What was executed:**
    * **Privilege Separation:** Split the coding capabilities into a safe `coding_agent` (Read-Only) and an `admin_coding_agent` (Write/Delete).
    * **Path Traversal Security:** Locked all local file operations strictly to the `WORKSPACE_DIR`.
    * **Live Web Access:** Integrated the `TavilySearchResults` tool into the Research Agent with fallback mock-tools.
    * **HITL Execution Freeze:** Utilized LangGraph's `interrupt_before=["admin_coding_node"]` compiler flag. If an agent attempts to write/delete code, the graph serializes to memory and returns an `HTTP 202 Accepted` status.
    * **Thaw Endpoint:** Created `POST /chat/approve` to let a human manager authorize the pending destructive action and resume the graph.

### Step 4: Multi-Tenant SaaS Isolation (Level 8)
* **The Goal:** Ensure absolute data isolation between different corporate clients sharing the same backend.
* **What was executed:**
    * **API Layer:** Mandated the `x-tenant-id` HTTP header on all FastAPI endpoints.
    * **Graph Configuration:** Passed the `tenant_id` into LangGraph's `RunnableConfig` so every node and agent operates inside a tenant-aware context.
    * **Redis Isolation:** Prefixed all short-term memory keys (`tenant_id:session_id`) to mathematically prevent cross-tenant session bleeding.
    * **ChromaDB Vaults:** Injected `tenant_id` into the vector metadata and enforced strict `$and` queries during retrieval to ensure long-term research and strategic memories are fully siloed.

---

## 🛠️ Current System Capabilities

1.  **Dynamic Routing:** The Supervisor autonomously evaluates user intent and routes tasks to the Coding, Research, or Mentor agents.
2.  **State-Driven Memory:** Maintains both short-term Redis state and domain-isolated long-term ChromaDB vector storage.
3.  **Absolute Data Isolation:** 100% secure multi-tenancy. Company A cannot prompt-inject their way into Company B's data vault.
4.  **Asynchronous Approvals:** The platform safely pauses high-risk operations and waits for human API confirmation.

---

## 🔌 API Endpoints

### 1. Execute Chat / Agent Routing
* **Endpoint:** `POST /chat`
* **Headers:** `x-api-key`, `x-tenant-id`
* **Body:** `{"session_id": "string", "question": "string"}`
* **Returns:** `200 OK` (Standard execution) OR `202 Accepted` (Requires HITL approval).

### 2. Approve Pending Action (HITL)
* **Endpoint:** `POST /chat/approve`
* **Headers:** `x-api-key`, `x-tenant-id`
* **Body:** `{"session_id": "string", "question": "string"}`
* **Returns:** `200 OK` (Graph resumes and executes the restricted tool).

### 3. Fetch Tenant-Isolated History
* **Endpoint:** `GET /history/{session_id}`
* **Headers:** `x-api-key`, `x-tenant-id`
* **Returns:** `200 OK` (Returns strictly the data mapped to that specific tenant and session).