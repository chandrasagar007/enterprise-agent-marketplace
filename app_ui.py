import os
import streamlit as st
import requests
import time
import uuid

# --------------------------------------------------
# 1. CONFIGURATION & STATE SETUP
# --------------------------------------------------
st.set_page_config(page_title="Enterprise AI Interface", page_icon="🤖", layout="wide")
st.title("🤖 Enterprise Agent Marketplace")

# Use the Docker network API URL, but fallback to localhost for local testing
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Initialize Session State variables
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4()) # Generate a unique chat session ID
if "active_approval" not in st.session_state:
    st.session_state.active_approval = None
if "polling_task" not in st.session_state:
    st.session_state.polling_task = None

# Sidebar for Credentials
with st.sidebar:
    st.header("🔐 Authentication")
    api_key = st.text_input("API Key", type="password", value="123456")
    tenant_id = st.selectbox("Tenant Tier", ["basic", "pro", "enterprise"], index=1)
    st.divider()
    st.caption(f"**Session ID:**\n{st.session_state.session_id}")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.active_approval = None
        st.session_state.polling_task = None
        st.rerun()

headers = {
    "x-api-key": api_key,
    "x-tenant-id": tenant_id,
    "Content-Type": "application/json"
}

# --------------------------------------------------
# 2. DISPLAY CHAT HISTORY & FEEDBACK BUTTONS
# --------------------------------------------------
for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
        # 🧠 MACRO-LEARNING: Render thumbs up/down for assistant messages
        if message["role"] == "assistant" and "original_prompt" in message:
            col1, col2, col3 = st.columns([1, 1, 10])
            with col1:
                if st.button("👍", key=f"up_{i}"):
                    st.toast("Glad it helped!")
            with col2:
                if st.button("👎", key=f"down_{i}"):
                    feedback_payload = {
                        "session_id": st.session_state.session_id,
                        "prompt": message["original_prompt"],
                        "is_positive": False
                    }
                    try:
                        res = requests.post(
                            f"{API_URL}/chat/feedback", 
                            json=feedback_payload, 
                            headers=headers
                        )
                        if res.status_code == 200:
                            st.toast("Feedback received. The AI is analyzing its mistake to learn for next time.", icon="🧠")
                    except Exception as e:
                        st.error("Failed to send feedback.")

# --------------------------------------------------
# 3. INTERACTIVE HITL APPROVAL WIDGET
# --------------------------------------------------
if st.session_state.active_approval:
    approval_data = st.session_state.active_approval
    task_id = approval_data["task_id"]
    
    st.write("---")
    with st.container():
        st.warning(f"🛑 **Human-in-the-Loop Action Required**\n\n**Proposed Action:** {approval_data['action_msg']}")
        
        # Text field for optional rejection instructions
        feedback_input = st.text_input(
            "Provide feedback / revision instructions (Required only if clicking Reject):",
            key="hitl_feedback_text",
            placeholder="e.g., Don't delete that folder, refactor main.py instead."
        )
        
        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("✅ Approve & Resume Execution", use_container_width=True):
                try:
                    # 🚀 FIX: Pass the session_id payload
                    payload = {"session_id": st.session_state.session_id}
                    res = requests.post(f"{API_URL}/api/tasks/{task_id}/approve", json=payload, headers=headers)
                    res.raise_for_status()
                    st.toast("Action approved! Resuming worker workflow...", icon="🚀")
                    
                    # Transition back into the polling phase for this task
                    new_task_id = res.json().get("task_id")
                    st.session_state.polling_task = {
                        "task_id": new_task_id,
                        "prompt": approval_data["original_prompt"]
                    }
                    st.session_state.active_approval = None
                    st.divider()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to transmit approval: {e}")
                    
        with c2:
            if st.button("❌ Reject Action & Route Back", use_container_width=True):
                if not feedback_input.strip():
                    st.error("You must provide feedback explaining why the action was rejected.")
                else:
                    try:
                        # 🚀 FIX: Pass the session_id and the human feedback payload
                        reject_payload = {
                            "session_id": st.session_state.session_id,
                            "feedback": feedback_input
                        }
                        res = requests.post(f"{API_URL}/api/tasks/{task_id}/reject", json=reject_payload, headers=headers)
                        res.raise_for_status()
                        st.toast("Action rejected. Routing agent backward with feedback.", icon="↩️")
                        
                        # Set up polling to track the agent as it re-processes with feedback
                        new_task_id = res.json().get("task_id")
                        st.session_state.polling_task = {
                            "task_id": new_task_id,
                            "prompt": approval_data["original_prompt"]
                        }
                        st.session_state.active_approval = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to transmit rejection: {e}")
    st.write("---")

# --------------------------------------------------
# 4. SHARED POLLING FUNCTIONALITY
# --------------------------------------------------
def run_polling_loop(task_id: str, original_prompt: str):
    status = "processing"
    start_time = time.time()
    
    while status == "processing":
        if time.time() - start_time > 300:
            st.error("Task timed out.")
            st.session_state.polling_task = None
            break
        
        with st.spinner(f"Agents are actively executing... (Task ID: {task_id[:8]}...)"):
            time.sleep(3)
            
            try:
                get_response = requests.get(f"{API_URL}/chat/status/{task_id}", headers=headers)
                get_response.raise_for_status()
                result_data = get_response.json()
                status = result_data.get("status")
                
                if status == "completed":
                    final_answer = result_data.get("answer")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_answer, 
                        "original_prompt": original_prompt
                    })
                    st.session_state.polling_task = None
                    st.rerun()
                    
                elif status in ["requires_approval", "requires_action"]:
                    action_msg = result_data.get("pending_action") or result_data.get("details") or "Destructive codebase modification requested."
                    st.session_state.active_approval = {
                        "task_id": task_id,
                        "action_msg": action_msg,
                        "original_prompt": original_prompt
                    }
                    st.session_state.polling_task = None
                    st.rerun()
                    
                elif status == "failed":
                    err_msg = result_data.get("message", "Unknown execution error occurred in background worker.")
                    st.error(f"❌ **Task Failed:** {err_msg}")
                    st.session_state.polling_task = None
                    break
                    
            except Exception as e:
                st.error(f"Polling Exception Error: {e}")
                st.session_state.polling_task = None
                break

# If an action was just approved or rejected, handle stateful resume polling here
if st.session_state.polling_task:
    task_info = st.session_state.polling_task
    run_polling_loop(task_info["task_id"], task_info["prompt"])

# --------------------------------------------------
# 5. HANDLE NEW USER INPUT DISPATCH
# --------------------------------------------------
if prompt := st.chat_input("Ask the AI a question or give it a task...", disabled=(st.session_state.active_approval is not None)):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = {
        "session_id": st.session_state.session_id,
        "question": prompt
    }

    try:
        with st.spinner("Dispatching task to worker..."):
            post_response = requests.post(f"{API_URL}/chat", json=payload, headers=headers)
            post_response.raise_for_status()
            task_data = post_response.json()
            task_id = task_data.get("task_id")

        if not task_id:
            st.error(f"Failed to retrieve Task ID. Server returned: {task_data}")
            st.stop()

        run_polling_loop(task_id, prompt)

    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: Ensure your FastAPI gateway is running.\n\nDetails: {e}")