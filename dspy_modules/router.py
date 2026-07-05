import os
import dspy

# 🧠 ADDED: We must configure the LM specifically for this module so the worker knows what to use!
llm = dspy.LM('openai/gpt-4o-mini', max_tokens=500)
dspy.configure(lm=llm)

# 1. Define the Classification Signature
class AgentRouter(dspy.Signature):
    """
    Classify the user's query and route it to the exact appropriate specialist agent.
    
    Routing Rules:
    - "coding_agent": For READ-ONLY codebase tasks (explaining code, listing files, summarizing architecture).
    - "admin_coding_node": For DESTRUCTIVE codebase tasks (writing, editing, deleting, or refactoring files).
    - "mentor_agent": For executive strategy, legacy family business consulting, and mental models (decision making under uncertainty).
    - "interview_agent": For AI PM interview prep, MLOps system design mock interviews, and STAR method grading.
    - "research_agent": For deep-dive web research, market sizing, competitor analysis, and gathering real-world facts.
    - "performance_agent": For system audits, analyzing failed interactions, processing macro-learning feedback, and writing optimization rules.
    - "FINISH": For general greetings, casual conversation, or queries that do not require any specialized agent.
    """
    
    query = dspy.InputField(desc="The user query to be routed.")
    # The prefix forces the LLM to output exactly what we want without conversational filler
    target_agent = dspy.OutputField(desc="The exact string name of the agent to route to.", prefix="Target Agent:")

# 2. Synchronous wrapper for LangGraph to call
def get_agent_route(query: str) -> str:
    """Passes the query to the DSPy classifier to determine the exact node route."""
    router = dspy.Predict(AgentRouter)
    
    # 🧠 LOAD THE COMPILED MACRO-LEARNING WEIGHTS
    # Dynamically resolve the path to ensure it finds the JSON file in the dspy_modules folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    weights_path = os.path.join(current_dir, "router_weights.json")
    
    try:
        router.load(weights_path)
    except Exception:
        pass # Fallback to zero-shot if the file hasn't been generated yet
        
    result = router(query=query)
    
    # Sanitize the output just in case the LLM adds quotes, spaces, or backticks
    route = result.target_agent.strip().replace('"', '').replace("'", "").replace("`", "")
    
    # 🛡️ Defensive Fallback: Ensure the route actually exists in your LangGraph
    valid_routes = [
        "coding_agent", 
        "admin_coding_node", 
        "mentor_agent", 
        "interview_agent",
        "research_agent",
        "performance_agent",
        "FINISH"
    ]
    
    if route not in valid_routes:
        # If it hallucinates a node, default to the mentor agent safely
        return "mentor_agent"
        
    return route