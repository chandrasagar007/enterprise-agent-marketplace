import os
from dotenv import load_dotenv

# --------------------------------------------------
# 1. ENVIRONMENT VARIABLES & IMPORTS
# --------------------------------------------------
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends, Request, Path
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from pydantic import BaseModel, Field

import time
import uuid

from middleware.auth import verify_api_key, get_verified_tenant
from utils.logger import logger
from utils.token_counter import count_tokens
from memory.redis_store import save_message, get_history

# 🚀 LEVEL 10: Import Redis & RQ for Background Processing
from redis import Redis
from rq import Queue
from rq.job import Job

# 🚀 LEVEL 10 FIX: Import uncompiled workflow and SQLite tools
from agents.supervisor import workflow
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

# --------------------------------------------------
# 2. CONSTANTS, LIMITER, & QUEUES
# --------------------------------------------------
MAX_TOKENS = 2000
limiter = Limiter(key_func=get_remote_address)

# ✅ DYNAMIC FIX: Automatically uses Docker's internal network if available, falls back to local host
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_conn = Redis.from_url(redis_url)
task_queue = Queue("enterprise_tasks", connection=redis_conn)

app = FastAPI(
    title="Agent API",
    version="10.0"  # Level 10 Asynchronous Workers
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=2, max_length=5000)

@app.get("/")
def health():
    return {"status": "running", "service": "Agent API", "version": "10.0"}

# --------------------------------------------------
# 3. CORE CHAT ENDPOINT (LEVEL 10 ASYNC QUEUE)
# --------------------------------------------------
@app.post("/chat")
@limiter.limit("20/minute")
def chat(
    request: Request,
    body: ChatRequest,
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    """
    LEVEL 10: ASYNCHRONOUS DECOUPLING
    This endpoint no longer runs the LLM graph. It validates the request, 
    shoves it into the Redis Queue, and returns a Task ID instantly. 
    This entirely prevents HTTP 504 Gateway Timeouts.
    """
    request_id = str(uuid.uuid4())

    try:
        # Validation checks
        if not body.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        token_count = count_tokens(body.question)
        if token_count > MAX_TOKENS:
            raise HTTPException(status_code=400, detail=f"Token limit exceeded.")

        # 🚀 ENQUEUE THE TASK to the background worker (tasks.py)
        job = task_queue.enqueue(
            "tasks.execute_agent_graph", 
            body.session_id, 
            tenant_id, 
            body.question,
            job_timeout=600 
        )

        logger.info(f"REQUEST_ID={request_id} | QUEUED TASK={job.id} | TENANT_ID={tenant_id}")

        # Return instantly to the client
        return {
            "request_id": request_id,
            "task_id": job.id,
            "session_id": body.session_id,
            "tenant_id": tenant_id,
            "status": "processing",
            "message": f"Task queued successfully. Poll /chat/status/{job.id} for the result."
        }

    except HTTPException as e:
        return {"request_id": request_id, "success": False, "status_code": e.status_code, "error": {"code": "VALIDATION_ERROR", "message": e.detail}}
    except Exception as e:
        logger.exception(f"REQUEST_ID={request_id} | ERROR ENQUEUING TASK")
        return {"request_id": request_id, "success": False, "status_code": 500, "error": {"code": "INTERNAL_SERVER_ERROR", "message": "Failed to queue task."}}

# --------------------------------------------------
# 4. STATUS POLLING ENDPOINT (LEVEL 10)
# --------------------------------------------------
@app.get("/chat/status/{task_id}")
def check_task_status(
    request: Request,
    task_id: str,
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    """
    LEVEL 10: CLIENT POLLING
    The client hits this endpoint to check if the background worker has finished.
    """
    try:
        job = Job.fetch(task_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Task ID not found or expired.")

    # Check the state of the background job
    if job.is_finished:
        result = job.result
        
        # Did the worker hit an Admin code write freeze?
        if result.get("status") == "requires_approval":
            return {
                "task_id": task_id,
                "status": "requires_approval", 
                "pending_action": result["pending_action"]
            }
        else:
            # Normal completion
            return {
                "task_id": task_id,
                "status": "completed", 
                "answer": result["answer"]
            }
            
    elif job.is_failed:
        return {"task_id": task_id, "status": "failed", "message": "The background worker encountered a critical error."}
        
    else:
        # Still running in the background queue
        return {"task_id": task_id, "status": "processing", "message": "The agents are still analyzing your request..."}

# --------------------------------------------------
# 5. LEVEL 7 HITL: APPROVAL ENDPOINT
# --------------------------------------------------
@app.post("/chat/approve")
@limiter.limit("10/minute")
def approve_action(
    request: Request,
    body: ChatRequest,
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    """
    Because SQLite Checkpointer is used, the API can resume the graph 
    from exactly where the background worker froze it.
    """
    try:
        isolated_thread_id = f"{tenant_id}:{body.session_id}"
        config = {
            "configurable": {
                "thread_id": isolated_thread_id,
                "tenant_id": tenant_id
            }
        }
        
        # 🚀 JUST-IN-TIME CONNECTION: Compile the graph dynamically to access the saved state safely
        with sqlite3.connect("langgraph_checkpoints.sqlite", check_same_thread=False) as db_conn:
            memory = SqliteSaver(db_conn)
            app_graph = workflow.compile(checkpointer=memory, interrupt_before=["admin_coding_node"])
            
            # Check the database to see if a freeze exists
            current_state = app_graph.get_state(config)
            if not current_state.next:
                raise HTTPException(status_code=400, detail="No pending actions require approval for this session.")

            # Resume execution (happens synchronously since Admin writing is fast)
            resumed_state = app_graph.invoke(None, config=config)
            answer = resumed_state["messages"][-1].content
        
        save_message(body.session_id, tenant_id, "human", "[ACTION APPROVED BY USER]")
        save_message(body.session_id, tenant_id, "assistant", answer)
        
        return {
            "session_id": body.session_id,
            "tenant_id": tenant_id,
            "success": True,
            "status_code": 200,
            "action_status": "Approved and Executed",
            "answer": answer
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.exception(f"APPROVAL_ERROR | SESSION_ID={body.session_id} | TENANT_ID={tenant_id}")
        raise HTTPException(status_code=500, detail="Failed to execute approved action.")

# --------------------------------------------------
# 6. GET HISTORY ENDPOINT
# --------------------------------------------------
@app.get("/history/{session_id}")
@limiter.limit("20/minute")
def fetch_history(
    request: Request,
    session_id: str = Path(..., min_length=1, max_length=100),
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    try:
        chat_history = get_history(session_id, tenant_id)
        
        if not chat_history:
            return {"session_id": session_id, "tenant_id": tenant_id, "message": "No active history found.", "history": []}
            
        return {
            "session_id": session_id,
            "tenant_id": tenant_id,
            "message": "History retrieved successfully",
            "total_messages": len(chat_history),
            "history": chat_history
        }
        
    except Exception as e:
        logger.exception(f"HISTORY_FETCH_ERROR | SESSION_ID={session_id} | TENANT_ID={tenant_id}")
        raise HTTPException(status_code=500, detail="Could not retrieve history")