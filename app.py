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

# 🧠 DSPy PHASE 1: Import the newly updated query optimization module
from dspy_modules.query_enhancer import enhance_user_query 

# 🚀 LEVEL 10: Import Redis & RQ for Background Processing
from redis import Redis
from rq import Queue
from rq.job import Job

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
    version="10.0" 
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class ChatRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    question: str = Field(min_length=2, max_length=5000)

class FeedbackRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    prompt: str = Field(min_length=2, max_length=5000)
    is_positive: bool

# 🚀 NEW: Payload models for HITL async resume
class ResumePayload(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    feedback: str | None = None

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
    request_id = str(uuid.uuid4())

    try:
        if not body.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")

        token_count = count_tokens(body.question)
        if token_count > MAX_TOKENS:
            raise HTTPException(status_code=400, detail=f"Token limit exceeded.")

        try:
            history_list = get_history(body.session_id, tenant_id) or []
            optimized_question = enhance_user_query(body.question, history_list)
            logger.info(f"DSPy OPTIMIZATION: '{body.question}' -> '{optimized_question}'")
        except Exception as e:
            logger.error(f"DSPy Enhancement failed, falling back to raw query. Error: {e}")
            optimized_question = body.question  

        job = task_queue.enqueue(
            "tasks.execute_agent_graph", 
            body.session_id, 
            tenant_id, 
            optimized_question,
            job_timeout=600 
        )

        logger.info(f"REQUEST_ID={request_id} | QUEUED TASK={job.id} | TENANT_ID={tenant_id}")

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
# 3.5 MACRO-LEARNING FEEDBACK ENDPOINT
# --------------------------------------------------
@app.post("/chat/feedback")
@limiter.limit("20/minute")
def submit_feedback(
    request: Request,
    body: FeedbackRequest,
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    if body.is_positive:
        return {"status": "success", "message": "Feedback recorded."}
    
    job = task_queue.enqueue(
        "tasks.execute_performance_audit",
        body.session_id,
        tenant_id,
        body.prompt,
        job_timeout=300
    )
    
    return {"status": "audit_started", "job_id": job.id}


# --------------------------------------------------
# 4. STATUS POLLING ENDPOINT
# --------------------------------------------------
@app.get("/chat/status/{task_id}")
def check_task_status(
    request: Request,
    task_id: str,
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    try:
        job = Job.fetch(task_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Task ID not found or expired.")

    if job.is_finished:
        result = job.result
        
        if result.get("status") == "requires_approval":
            return {
                "task_id": task_id,
                "status": "requires_approval", 
                "pending_action": result["pending_action"]
            }
        else:
            return {
                "task_id": task_id,
                "status": "completed", 
                "answer": result["answer"]
            }
            
    elif job.is_failed:
        return {"task_id": task_id, "status": "failed", "message": "The background worker encountered a critical error."}
        
    else:
        return {"task_id": task_id, "status": "processing", "message": "The agents are still analyzing your request..."}

# --------------------------------------------------
# 5. ASYNC HITL: APPROVE & REJECT ENDPOINTS
# --------------------------------------------------
@app.post("/api/tasks/{task_id}/approve")
@limiter.limit("10/minute")
def approve_action(
    request: Request,
    task_id: str, 
    payload: ResumePayload, 
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    """Catches the UI approval and enqueues the worker to resume the graph."""
    job = task_queue.enqueue(
        "tasks.resume_agent_graph", 
        payload.session_id, 
        tenant_id, 
        "approve", 
        None,
        job_timeout=600
    )
    return {"status": "approved", "task_id": job.id}

@app.post("/api/tasks/{task_id}/reject")
@limiter.limit("10/minute")
def reject_action(
    request: Request,
    task_id: str, 
    payload: ResumePayload, 
    auth=Depends(verify_api_key),
    tenant_id: str = Depends(get_verified_tenant)
):
    """Catches the UI rejection and injects human feedback back into the graph."""
    job = task_queue.enqueue(
        "tasks.resume_agent_graph", 
        payload.session_id, 
        tenant_id, 
        "reject", 
        payload.feedback,
        job_timeout=600
    )
    return {"status": "rejected", "task_id": job.id}

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