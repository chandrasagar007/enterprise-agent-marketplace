# tasks.py
import os
from dotenv import load_dotenv

# 🚀 LEVEL 10 FIX: Tell the worker process to load the API keys!
load_dotenv()

from langchain_core.messages import HumanMessage
from memory.redis_store import save_message

# 🚀 LEVEL 10: Import SQLite tools and uncompiled workflow
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from agents.supervisor import workflow

def execute_agent_graph(session_id: str, tenant_id: str, question: str):
    """This function is executed by the background RQ Worker safely."""
    
    isolated_thread_id = f"{tenant_id}:{session_id}"
    
    config = {
        "configurable": {
            "thread_id": isolated_thread_id,
            "tenant_id": tenant_id
        }
    }
    
    initial_state = {
        "messages": [HumanMessage(content=question)],
        "session_id": session_id,
        "next_node": "supervisor"
    }

    # 🚀 JUST-IN-TIME CONNECTION: Opens the DB safely inside the isolated worker process
    with sqlite3.connect("langgraph_checkpoints.sqlite", check_same_thread=False) as db_conn:
        memory = SqliteSaver(db_conn)
        
        # Compile the graph on the fly inside the worker
        app_graph = workflow.compile(checkpointer=memory, interrupt_before=["admin_coding_node"])
        
        # Execute Graph
        final_state = app_graph.invoke(initial_state, config=config)

        # Check if the execution was frozen by the HITL (Admin Write)
        current_state = app_graph.get_state(config)
        if current_state.next and 'admin_coding_node' in current_state.next:
            return {
                "status": "requires_approval",
                "pending_action": "The agent is requesting permission to execute a destructive codebase operation.",
                "answer": None
            }

        # Graph finished successfully
        answer = final_state["messages"][-1].content

    # Save to your long-term chat history (Outside the DB block)
    save_message(session_id, tenant_id, "human", question)
    save_message(session_id, tenant_id, "assistant", answer)

    return {
        "status": "completed",
        "answer": answer
    }