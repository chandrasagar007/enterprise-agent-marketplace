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
# 2. DISPLAY CHAT HISTORY
# --------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --------------------------------------------------
# 3. HANDLE USER INPUT & ASYNC POLLING
# --------------------------------------------------

# Use the Docker network API URL, but fallback to localhost for local testing
API_URL = os.getenv("API_URL", "http://localhost:8000")

if prompt := st.chat_input("Ask the AI a question or give it a task..."):
    
    # Display user message instantly
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant loading state
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
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
                # ✅ Dynamically calling the API_URL variable
                post_response = requests.post(f"{API_URL}/chat", json=payload, headers=headers)
                post_response.raise_for_status()
                task_data = post_response.json()
                task_id = task_data.get("task_id")

            if not task_id:
                message_placeholder.error(f"Failed to retrieve Task ID. Server returned: {task_data}")
                st.stop()

            # STEP B: Poll for the Result (GET)
            status = "processing"
            start_time = time.time()
            
            while status == "processing":
                # Prevent infinite loops (timeout after 5 minutes)
                if time.time() - start_time > 300:
                    message_placeholder.error("Task timed out.")
                    break
                
                with st.spinner(f"Agents are analyzing... (Task: {task_id[:8]}...)"):
                    time.sleep(3) # Wait 3 seconds before polling again
                    
                    # ✅ Dynamically calling the API_URL variable
                    get_response = requests.get(f"{API_URL}/chat/status/{task_id}", headers=headers)
                    get_response.raise_for_status()
                    result_data = get_response.json()
                    status = result_data.get("status")
                    
                    if status == "completed":
                        final_answer = result_data.get("answer")
                        message_placeholder.markdown(final_answer)
                        st.session_state.messages.append({"role": "assistant", "content": final_answer})
                        break
                    
                    elif status == "requires_approval":
                        action_msg = result_data.get("pending_action")
                        warning = f"⚠️ **Approval Required:** {action_msg}\n\n*(HITL Approval via UI coming soon!)*"
                        message_placeholder.warning(warning)
                        st.session_state.messages.append({"role": "assistant", "content": warning})
                        break
                        
                    elif status == "failed":
                        err_msg = result_data.get("message", "Unknown error occurred in worker.")
                        message_placeholder.error(f"❌ **Task Failed:** {err_msg}")
                        break

        except requests.exceptions.RequestException as e:
            message_placeholder.error(f"API Connection Error: Make sure your FastAPI server is running on port 8000.\n\nDetails: {e}")