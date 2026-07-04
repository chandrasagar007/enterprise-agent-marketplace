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

# Sidebar for Credentials
with st.sidebar:
    st.header("🔐 Authentication")
    api_key = st.text_input("API Key", type="password", value="123456")
    tenant_id = st.selectbox("Tenant Tier", ["basic", "pro", "enterprise"], index=1)
    st.divider()
    st.caption(f"**Session ID:**\n{st.session_state.session_id}")
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

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
                            headers={"x-api-key": api_key, "x-tenant-id": tenant_id}
                        )
                        if res.status_code == 200:
                            st.toast("Feedback received. The AI is analyzing its mistake to learn for next time.", icon="🧠")
                    except Exception as e:
                        st.error("Failed to send feedback.")

# --------------------------------------------------
# 3. HANDLE USER INPUT & ASYNC POLLING
# --------------------------------------------------

if prompt := st.chat_input("Ask the AI a question or give it a task..."):
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    headers = {
        "x-api-key": api_key,
        "x-tenant-id": tenant_id,
        "Content-Type": "application/json"
    }
    
    payload = {
        "session_id": st.session_state.session_id,
        "question": prompt
    }

    try:
        # STEP A: Dispatch the Task (POST)
        with st.spinner("Dispatching task to worker..."):
            post_response = requests.post(f"{API_URL}/chat", json=payload, headers=headers)
            post_response.raise_for_status()
            task_data = post_response.json()
            task_id = task_data.get("task_id")

        if not task_id:
            st.error(f"Failed to retrieve Task ID. Server returned: {task_data}")
            st.stop()

        # STEP B: Poll for the Result (GET)
        status = "processing"
        start_time = time.time()
        
        while status == "processing":
            if time.time() - start_time > 300:
                st.error("Task timed out.")
                break
            
            with st.spinner(f"Agents are analyzing... (Task: {task_id[:8]}...)"):
                time.sleep(3)
                
                get_response = requests.get(f"{API_URL}/chat/status/{task_id}", headers=headers)
                get_response.raise_for_status()
                result_data = get_response.json()
                status = result_data.get("status")
                
                if status == "completed":
                    final_answer = result_data.get("answer")
                    # 🧠 Store the original prompt so we know what they are downvoting later
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": final_answer, 
                        "original_prompt": prompt
                    })
                    st.rerun() # Refresh UI to show the new message and feedback buttons
                    
                elif status == "requires_approval":
                    action_msg = result_data.get("pending_action")
                    warning = f"⚠️ **Approval Required:** {action_msg}\n\n*(HITL Approval via UI coming soon!)*"
                    st.session_state.messages.append({"role": "assistant", "content": warning, "original_prompt": prompt})
                    st.rerun()
                    
                elif status == "failed":
                    err_msg = result_data.get("message", "Unknown error occurred in worker.")
                    st.error(f"❌ **Task Failed:** {err_msg}")
                    break

    except requests.exceptions.RequestException as e:
        st.error(f"API Connection Error: Make sure your FastAPI server is running on port 8000.\n\nDetails: {e}")