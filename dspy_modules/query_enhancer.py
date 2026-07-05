import os
import dspy

# 1. Configure DSPy to use your existing OpenAI credentials
# DSPy will automatically pick up the OPENAI_API_KEY from your .env file
llm = dspy.LM('openai/gpt-4o-mini', max_tokens=500)
dspy.configure(lm=llm)

# 2. Define the Signature (Accepts Chat History for context tracking)
class QueryEnhancer(dspy.Signature):
    """
    Analyze the raw user query along with the recent chat history. 
    Resolve any ambiguous pronouns (e.g., 'they', 'it', 'this') by linking them to companies, entities, or topics discussed in the history.
    Rewrite the query into a highly specific, direct instruction optimized for downstream specialist agents.
    
    CRITICAL CRITERIA:
    - Never include brackets, placeholders, or variables like '[insert company]' or '[specific group]'.
    - If the context cannot be resolved from the history, preserve the user's raw query intent exactly as stated without creating placeholders.
    - Do not answer the question; only rewrite it to be clearer and keyword-rich for tool usage.
    """
    
    chat_history = dspy.InputField(desc="The string representation of recent messages in the conversation for context.")
    raw_query = dspy.InputField(desc="The original user input, which might be vague or poorly formatted.")
    enhanced_query = dspy.OutputField(desc="The optimized, detailed query ready for agent routing.")

# 3. Build the Module (Injecting Chain of Thought reasoning over context)
class OptimizeInput(dspy.Module):
    def __init__(self):
        super().__init__()
        # ChainOfThought forces the LLM to think about context dependencies before outputting the rewritten query
        self.enhancer = dspy.ChainOfThought(QueryEnhancer)
        
    def forward(self, chat_history, raw_query):
        return self.enhancer(chat_history=chat_history, raw_query=raw_query)

# 4. Clean, synchronous wrapper for FastAPI to execute
def enhance_user_query(raw_query: str, history_list: list) -> str:
    """Passes the user query and conversational history through the DSPy optimizer."""
    # Fast-fail for super short inputs
    if len(raw_query.split()) < 2:
        return raw_query
        
    # Format the history list into a clean, human-readable block for the DSPy engine
    formatted_history = ""
    if history_list:
        # Capture up to the last 6 messages to keep context window tight and high-signal
        recent_history = history_list[-6:]
        formatted_history = "\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in recent_history])
    else:
        formatted_history = "No prior history. This is the first message."

    optimizer = OptimizeInput()
    result = optimizer(chat_history=formatted_history, raw_query=raw_query)
    return result.enhanced_query