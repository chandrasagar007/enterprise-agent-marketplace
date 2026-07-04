# utils/telemetry.py
import os
from langfuse.langchain import CallbackHandler
from utils.logger import logger

def get_langfuse_callback():
    """
    Generates a localized Langfuse callback handler for LangGraph tracking.
    In Langfuse v3+, this takes no arguments and reads ENV variables automatically.
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")

    if not public_key or not secret_key:
        logger.warning("Langfuse credentials missing. Tracing will be disabled.")
        return None

    # V3 SDK: Initialize empty. Do not pass keys or session tags here.
    return CallbackHandler()