import os
from dotenv import load_dotenv

# 🚀 Tell the worker process to load the API keys!
load_dotenv()

# 🚀 FIX: Added AIMessage to the imports for the rejection state manipulation
from langchain_core.messages import HumanMessage, AIMessage
from memory.redis_store import save_message

import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from agents.supervisor import workflow

# 📊 OBSERVABILITY: Langfuse v4 import path
from langfuse.langchain import CallbackHandler


def execute_agent_graph(session_id: str, tenant_id: str, question: str):
    """This function is executed by the background RQ Worker safely."""
    
    isolated_thread_id = f"{tenant_id}:{session_id}"
    langfuse_handler = CallbackHandler()
    
    config = {
        "configurable": {
            "thread_id": isolated_thread_id,
            "tenant_id": tenant_id
        },
        "callbacks": [langfuse_handler],
        "recursion_limit": 50
    }
    
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "session_id": session_id,
        "next_node": "supervisor"
    }

    try:
        with sqlite3.connect("langgraph_checkpoints.sqlite", check_same_thread=False) as db_conn:
            memory = SqliteSaver(db_conn)
            app_graph = workflow.compile(checkpointer=memory, interrupt_before=["admin_coding_node"])
            
            final_state = app_graph.invoke(initial_state, config=config)

            current_state = app_graph.get_state(config)
            if current_state.next and 'admin_coding_node' in current_state.next:
                return {
                    "status": "requires_approval",
                    "pending_action": "The agent is requesting permission to execute a destructive codebase operation.",
                    "answer": None
                }

            answer = final_state["messages"][-1].content

        save_message(session_id, tenant_id, "human", question)
        save_message(session_id, tenant_id, "assistant", answer)

        return {
            "status": "completed",
            "answer": answer
        }
        
    except Exception as e:
        raise e


# 🚀 NEW: Function to handle HITL State Resumption
def resume_agent_graph(session_id: str, tenant_id: str, action: str, feedback: str = None):
    """
    Hooks into the paused LangGraph state and resumes it based on human input.
    """
    isolated_thread_id = f"{tenant_id}:{session_id}"
    langfuse_handler = CallbackHandler()
    
    config = {
        "configurable": {
            "thread_id": isolated_thread_id,
            "tenant_id": tenant_id
        },
        "callbacks": [langfuse_handler],
        "recursion_limit": 50
    }
    
    try:
        with sqlite3.connect("langgraph_checkpoints.sqlite", check_same_thread=False) as db_conn:
            memory = SqliteSaver(db_conn)
            app_graph = workflow.compile(checkpointer=memory, interrupt_before=["admin_coding_node"])
            
            if action == "approve":
                # 🚀 FIX: To approve, we DO NOT use update_state. 
                # We simply invoke the graph to unpause it, letting the DSPy agent actually run!
                final_state = app_graph.invoke(None, config=config)
                
            elif action == "reject":
                # 🚀 FIX: To reject, we DO use update_state. We fake the agent's output as an AIMessage 
                # so the graph skips the actual execution and routes backward correctly.
                rejection_message = AIMessage(content=f"❌ Action Rejected by Human: {feedback}", name="admin_coding_node")
                app_graph.update_state(config, {"messages": [rejection_message]}, as_node="admin_coding_node")
                final_state = app_graph.invoke(None, config=config)
                
            answer = final_state["messages"][-1].content
            
        # Log the manual override into the Redis chat history
        save_message(session_id, tenant_id, "human", f"[ACTION {action.upper()}ED BY USER]")
        save_message(session_id, tenant_id, "assistant", answer)
        
        return {
            "status": "completed",
            "answer": answer
        }
        
    except Exception as e:
        raise e


def execute_performance_audit(session_id: str, tenant_id: str, failed_prompt: str):
    """Background worker task to synthesize a rule after a failure."""
    from agents.performance_agent import performance_agent
    
    audit_prompt = f"The user gave negative feedback for this prompt: '{failed_prompt}'. Analyze the logs and generate a rule."
    
    try:
        performance_agent(audit_prompt, session_id, tenant_id)
        return {"status": "audit_complete_rule_saved"}
    except Exception as e:
        raise e