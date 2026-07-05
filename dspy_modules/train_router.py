import dspy
from dspy.teleprompt import BootstrapFewShot
from dspy_modules.router import AgentRouter, get_agent_route

# 1. Configure the LLM for the training run
llm = dspy.LM('openai/gpt-4o-mini', max_tokens=500)
dspy.configure(lm=llm)

# 2. Define the Golden Dataset (Examples of perfect routing)
training_data = [
    dspy.Example(query="Delete the logs folder.", target_agent="admin_coding_node").with_inputs("query"),
    dspy.Example(query="Refactor main.py to use async functions.", target_agent="admin_coding_node").with_inputs("query"),
    dspy.Example(query="What files are in the database directory?", target_agent="coding_agent").with_inputs("query"),
    dspy.Example(query="Explain how the authentication middleware works.", target_agent="coding_agent").with_inputs("query"),
    dspy.Example(query="Should I use a microservices or monolithic architecture?", target_agent="mentor_agent").with_inputs("query"),
    dspy.Example(query="What is the framework for decision making under uncertainty?", target_agent="mentor_agent").with_inputs("query"),
    dspy.Example(query="Ask me a behavioral question about stakeholder management.", target_agent="interview_agent").with_inputs("query"),
    dspy.Example(query="Review my resume for an AI PM role.", target_agent="interview_agent").with_inputs("query"),
    dspy.Example(query="What is the market size of commercial real estate in India?", target_agent="research_agent").with_inputs("query"),
    dspy.Example(query="Search the web for the latest competitors to Infra.Market.", target_agent="research_agent").with_inputs("query"),
    dspy.Example(query="Why did the last agent fail to answer my question?", target_agent="performance_agent").with_inputs("query"),
    dspy.Example(query="Hello, how are you doing today?", target_agent="FINISH").with_inputs("query"),
    dspy.Example(query="Who built you?", target_agent="FINISH").with_inputs("query"),
    dspy.Example(query="Good, I need this type of explanation style.", target_agent="FINISH").with_inputs("query"),
    dspy.Example(query="Perfect, thanks for the detailed breakdown.", target_agent="FINISH").with_inputs("query"),
    dspy.Example(query="Wow, this is exactly what I was looking for.", target_agent="FINISH").with_inputs("query"),
]

# 3. Define the evaluation metric (Exact string match)
def exact_match_metric(example, pred, trace=None):
    return example.target_agent.strip().lower() == pred.target_agent.strip().lower()

print("🚀 Starting DSPy Compilation process...")

# 4. Initialize the Optimizer
# BootstrapFewShot will simulate the routing, grade it, and optimize the prompts automatically
optimizer = BootstrapFewShot(metric=exact_match_metric, max_bootstrapped_demos=4, max_labeled_demos=13)

# 5. Compile the router module
compiled_router = optimizer.compile(dspy.Predict(AgentRouter), trainset=training_data)

# 6. Save the optimized neural weights to a JSON file
compiled_router.save("dspy_modules/router_weights.json")

print("✅ Compilation complete! Optimized weights saved to router_weights.json")