🤖 Sample Project — Agentic AI API (FastAPI + LangGraph)
A progressively built, production-ready AI Agent API using FastAPI, LangGraph, and OpenAI —
evolving from a basic agent to a governed, observable, and memory-aware Agentic AI service.

📁 Current Project Structure
Sample_Project/
│
├── app.py                    # FastAPI entry point
├── agent.py                  # LangGraph ReAct Agent + OpenAI LLM
├── tools.py                  # Tool definitions (Weather, DateTime, Search, Calculator)
│
├── middleware/
│   ├── auth.py               # API Key authentication
│   ├── ratelimit.py          # Rate limiting (slowapi)
│   └── validation.py         # Request validation
│
├── models/
│   └── request_models.py     # Pydantic request/response models
│
├── utils/
│   ├── logger.py             # Structured logging
│   └── token_counter.py      # Token counting (tiktoken)
│
├── logs/
│   └── api.log               # Log output
│
├── requirements.txt
├── pyproject.toml
├── uv.lock
└── README.md

⚙️ Setup

1 — Activate Virtual Environment
bash
Copy
source .venv/bin/activate

2 — Configure Environment Variables
Create a .env file:
env
Copy
OPENAI_API_KEY=your_openai_key_here

3 — Install Dependencies
bash
Copy
pip install -r requirements.txt

4 — Start the Server
bash
Copy

uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
Open Swagger UI:

http://127.0.0.1:8000/docs
🧪 Testing the API
Swagger UI
Go to http://127.0.0.1:8000/docs
Click POST /chat → Try it out

Add API key in Authorize → 123456

Enter:
json
Copy
{
  "question": "What is the weather in Bangalore?"
}
✅ Expected Response:

json
Copy
{
  "request_id": "0c5c1d7d-...",
  "success": true,
  "question": "What is the weather in Bangalore?",
  "answer": "The current temperature in Bangalore is 27°C with wind speed of 10 km/h.",
  "execution_time": "1.23s",
  "token_usage": 145
}
cURL
bash
Copy
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -H "x-api-key: 123456" \
  -d '{"question": "What is the weather in Bangalore?"}'


📡 API Reference

Method	Endpoint	Description	Auth Required
GET	/	Health check	❌
POST	/chat	Query the AI Agent	✅


🗺️ Architecture
User Request
     ↓
FastAPI (app.py)
     ↓
Middleware Pipeline
  ├── Auth (x-api-key)
  ├── Rate Limiter (10 req/min)
  └── Token Validator (max 2000 tokens)
     ↓
LangGraph ReAct Agent (agent.py)
     ↓
     ├── Weather Tool
     ├── DateTime Tool
     ├── Calculator Tool
     └── Web Search Tool
     ↓
OpenAI LLM
     ↓
Structured JSON Response
🔒 Authentication

All /chat requests require an API key in the header:

x-api-key: 123456
Status	Meaning
200	Success
400	Bad Request / Validation Error
401	Unauthorized
403	Forbidden
429	Too Many Requests
500	Internal Server Error
503	Service Unavailable
Error response format:

json
Copy
{
  "success": false,
  "status_code": 401,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API key"
  }
}
🚦 Rate Limiting & Token Limits
Control	Limit	Library
Rate Limit	10 requests / minute	slowapi
Max Input Tokens	2000 tokens	tiktoken
Token exceeded response:

json
Copy
{
  "status_code": 400,
  "error": {
    "code": "TOKEN_LIMIT_EXCEEDED",
    "message": "Input exceeds maximum token limit of 2000"
  }
}


📋 Logging
All requests are logged to logs/api.log.

Each log entry tracks:

request_id — unique UUID per request
question — user input
execution_time — agent response time
token_count — tokens consumed
errors — any exceptions
Log levels used:

python
Copy
logger.info(...)       # Normal flow
logger.warning(...)    # Non-critical issues
logger.error(...)      # Handled errors
logger.exception(...)  # Unhandled exceptions
🌐 Exposing the API
Local Network (Same WiFi)
bash
Copy
uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload
bash
Copy
ifconfig | grep inet    # Find your local IP
Access at: http://YOUR_LOCAL_IP:8000/docs

Public Internet — Ngrok
bash
Copy
ngrok http 8000
https://hardcopy-mulberry-rotunda.ngrok-free.dev/docs
✅ Now anyone on the internet can call your API.

🔧 Troubleshooting
Port already in use:

bash
Copy
lsof -i :8000
kill -9 <PID>

📊 Current Maturity Score
Capability	Status
Basic Agent	✅
FastAPI Server	✅
Swagger UI	✅
Tool Calling	✅
Logging	✅
Error Handling	✅
Request ID Tracking	✅
Request Validation	✅
API Key Auth	✅
Rate Limiting	✅
Token Limits	✅
Internet Exposure	✅
Memory (Session)	⏳ Next
Langfuse Observability	⏳ Next
Cost Tracking	⏳
LLM Trace Debugging	⏳
Quality Evals	⏳
Metrics / Prometheus	⏳
Audit Logs	⏳
Agent Governance	⏳
Multi-Agent Support	⏳
Enterprise Deployment	⏳




####### Memory #############

                   FastAPI
                      |
                      |
              Agent Gateway
                      |
      ----------------------------------
      |                                |
 Authentication                 Rate Limits
      |                                |
      ----------------------------------
                      |
                LangGraph
                      |
             Agent Orchestrator
                      |
      ----------------------------------
      |                                |
   Redis                         Chroma
Short-Term                     Long-Term
Memory                          Memory
      |                                |
      ----------------------------------
                      |
                  OpenAI
                      |
                 Langfuse
                      |
             Governance Layer


Level 0  ✅ Basic Agent API
Level 1  ✅ Logging & Error Handling
Level 2  ✅ Auth + Limits
Level 3  ✅ Memory (Redis + Chroma + LangGraph)

Level 4  ← NEXT
Multi-Agent Architecture

Level 5
Observability (Langfuse)

Level 6
Agent Governance

Level 7
Human-in-the-Loop

Level 8
Multi-Tenant SaaS

Level 9
Agent Marketplace

Level 10
Enterprise AI Platform

###############

🚀 Evolution Roadmap
Level 0  — Basic Agent API              ✅ Done
Level 1  — Logging & Error Handling     ✅ Done
Level 2  — Auth + Validation + Limits   ✅ Done
Level 3  — Memory Layer(Long term+Short term)                 ⏳ Next
Level 4  — Observability (Langfuse)     ⏳
Level 5  — Agent Governance / Gateway   ⏳
Level 6  — Multi-Agent Platform         ⏳
Level 7  — Human-in-the-Loop            ⏳
Level 8  — Multi-Tenant SaaS            ⏳
Level 9  — Agent Marketplace            ⏳
Level 10 — Enterprise AI Platform       ⏳
🧠 What's Missing — Memory Layer (Level 3)
Currently, every request is stateless. The agent forgets context after each response.

Example of the problem:

Request 1: "My name is Chandra"  →  "Nice to meet you, Chandra"
Request 2: "What is my name?"    →  "I don't know your name."   ← ❌ No memory
Memory Roadmap
Phase	Type	Storage	Capability
1	In-Memory Session	Python dict	Conversation history per session
2	LangGraph Checkpointer	MemorySaver()	Thread-based persistent memory
3	Redis Memory	Redis	Multi-user, scalable sessions
4	Vector Memory	Qdrant / Chroma	Long-term semantic retrieval
Recommended next step: Implement LangGraph MemorySaver with session_id / thread_id support.


Run this command to delete the old Chroma database:

> rm -rf chroma_db

python
Copy
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
agent = create_react_agent(model, tools, checkpointer=memory)

config = {"configurable": {"thread_id": "session_abc123"}}
response = agent.invoke({"messages": [...]}, config)
🔭 Observability — Langfuse (Level 4)
Currently missing. Your logs/api.log tracks basic request info, but gives zero visibility into what the LLM is doing inside the agent.

What You Track Now vs What Langfuse Adds
Metric	logs/api.log	Langfuse
Request ID	✅	✅
Execution Time	✅	✅
Token Count (estimated)	✅	✅ exact
Cost per request	❌	✅
LLM prompt & response	❌	✅
Tool call traces	❌	✅
Agent reasoning steps	❌	✅
Quality scores / Evals	❌	✅
Latency per tool / LLM	❌	✅
Error rate dashboard	❌	✅
User feedback tracking	❌	✅
Setup
Install:

bash
Copy
pip install langfuse
Add to .env:

env
Copy
LANGFUSE_PUBLIC_KEY=your_public_key
LANGFUSE_SECRET_KEY=your_secret_key
LANGFUSE_HOST=https://cloud.langfuse.com
Update agent.py:

python
Copy
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler()

# Pass as callback when invoking the agent
response = agent.invoke(
    {"messages": [HumanMessage(content=question)]},
    config={"callbacks": [langfuse_handler]}
)
✅ That's it — every LLM call, tool use, and agent reasoning step is automatically traced in the Langfuse dashboard.

What a Trace Looks Like
Trace: POST /chat  (request_id: 0c5c1d7d)
  ↓
  LLM Call  → prompt: 120 tokens | completion: 45 tokens | cost: $0.0003
  ↓
  Tool Call → weather_tool | latency: 320ms
  ↓
  LLM Call  → prompt: 200 tokens | completion: 80 tokens | cost: $0.0006
  ↓
  Final Answer → total latency: 1.8s | total cost: $0.0009

What Langfuse Enables
Capability	Description
💰 Cost Tracking	Per-request, per-user, per-tool cost breakdown
🐛 Trace Debugging	Step-by-step agent reasoning visibility
📊 Quality Evals	Score outputs with LLM-as-judge or human review
⏱️ Latency Analysis	Identify which tool/LLM step is the bottleneck
📁 Prompt Management	Version and A/B test prompts
👥 User Analytics	Track usage patterns across users/sessions

Recommended Implementation Order
Now (parallel with Memory)  →  Add Langfuse callback to agent.py  ← 3 lines
After Memory is done        →  Add session_id to Langfuse traces
Later                       →  Add LLM-as-judge quality scoring
Production                  →  Add user feedback loop + prompt A/B testing


🛠️ Tech Stack
Layer	Technology
API Server	FastAPI + Uvicorn
Agent Logic	LangGraph ReAct Agent
LLM	OpenAI GPT-4
Tools	DuckDuckGo Search, Requests
Auth	Custom API Key Middleware
Rate Limit	slowapi
Token Count	tiktoken
Logging	Python logging (structured)
Config	python-dotenv
Observability	Langfuse (planned)
Exposure	Ngrok

⚠️ Security Note: Never commit .env, API keys, or uv.lock secrets to version control.
The API key 123456 is for local dev only — replace with a secure key before going public.




🛠️ 1. Testing the Coding AgentRouting triggers: "python", "code", "sql", "api", "fastapi", "bug"

Test A: Web Search + Syntax Check

"I am writing a new API in Python using FastAPI and Pydantic v2. Can you search for the latest Pydantic v2 syntax for field validation and write a small code example?

"Expected Result: Routes to Coding Agent. The agent should pause, use the web_search_tool to look up Pydantic v2 documentation, and return a highly accurate code snippet.Test B: Calculator + System Design

"I am designing a Python rate limiter for my API. If I have a hard limit of 2,500,000 requests per month, and I want to distribute this evenly across 4 server pods, calculate the exact requests per second (RPS) limit I should set per pod.

"Expected Result: Routes to Coding Agent. The agent should use the calculator_tool to perform the exact math ($2.5M \div 30 \div 24 \div 3600 \div 4$) before answering.Test C: Persona + Best Practices"Review this idea: 

"I want to store raw SQL queries inside my frontend React code and just pass them to my FastAPI backend to execute. Is this a good idea?"

Expected Result: Routes to Coding Agent. It should reject this idea strongly (acting as a Senior SWE) and concisely explain SQL injection risks and architectural best practices.

📊 2. Testing the Research Agent
Routing triggers: "market", "research", "industry", "competitor", "rmc", "demand"

Test A: Web Search + Fact Extraction

"What is the current estimated market size and demand for the Ready Mix Concrete (RMC) industry in India as of 2024/2025?"

Expected Result: Routes to Research Agent. It should trigger the web_search_tool to find recent industry reports and return data with clear headings, bullet points, and source citations (as requested in its prompt).

Test B: Competitor Analysis (Structured Output)

"Provide a quick competitor research breakdown of the top 3 AI-powered construction equipment rental platforms. If you cannot find exact data, state what is unknown."

Expected Result: Routes to Research Agent. It should search the web and format the output highly systematically, explicitly stating if certain unit economics or funding numbers are unavailable.

🎧 3. Testing the Support Agent
Routing triggers: Everything else (No coding/research keywords)

Test A: Empathy + Step-by-Step Logic

"I've tried resetting my password three times but the email never arrives. I am getting completely locked out and I have an urgent deadline today!"

Expected Result: Routes to Support Agent. It should immediately validate the frustration ("I understand how stressful that is with a deadline"), provide step-by-step troubleshooting (check spam, wait 5 mins, clear cache), and offer an escalation path.

Test B: UI Navigation Simulation

"How do I update my billing credit card on your platform? The old one expired."

Expected Result: Routes to Support Agent. It should provide clear instructions, using bolding for UI elements (e.g., "Click on Settings -> Billing").

⚠️ 4. The "Edge Case" Test (Testing the Router limits)
To truly test your Supervisor, try giving it conflicting keywords.

"I need to write a Python script to scrape competitor market research."

What to watch for: Because your supervisor.py evaluates if (Coding) before elif (Research), the word "Python" will trigger the Coding Agent. The Coding Agent will receive this prompt and attempt to write a web scraper, rather than doing the market research itself.

This is the exact limitation of a rule-based router that Phase 4.2 (LangGraph Supervisor Node) will solve, as an LLM Supervisor would be able to intelligently decide which agent is better suited for the primary intent of the prompt!

##################################################################################################

What We Have Done So Far
Multi-Agent Routing Architecture: Built a FastAPI application backed by a Supervisor (supervisor.py) that serves as a traffic cop, dynamically classifying and routing user questions to specialized workers (research_agent, coding_agent, support_agent).

Upgraded Search Infrastructure: Replaced the default DuckDuckGo search library with Tavily API. This allows the Research Agent to read deeply scraped webpage content and actual text from reports instead of being limited to 2-3 sentence search engine previews.

Decentralized Agent Memory: Shifted long-term memory retrieval and persistence from a global level in app.py directly into the downstream worker agents.

Metadata Tagging (Categorized Memory): Upgraded chroma_store.py to use explicit logical operators ($and and $eq) to filter long-term vector records simultaneously by session_id and a distinct domain category (research, coding, support).

Why We Isolated Context Within the Same Session
When building complex enterprise AI assistants, users expect a single chat session (session_id) to function like a normal conversation where they can jump between tasks. However, mixing data creates severe performance bottlenecks. Here is why we isolated the context:

Eliminating Context Bleed-over: LLMs are highly impressionable. If a user performs a complex server calculation and immediately follows up with a request for a web-scraping script within the same session, a global memory search dumps the old math parameters straight into the prompt. The LLM gets confused and tries to finish or incorporate the old math logic into the new coding task.

Enforcing Domain Relevance: A technical script should be informed by past programming constraints, not by general customer service interactions or market research numbers. Tagging memories by category ensures that the coding_agent only remembers code, while the research_agent only remembers market facts.

Minimizing Prompt Noise & Token Costs: Dumping every historical message from a session into the vector database search fills the context window with irrelevant data. Filtering by metadata ensures only highly targeted, contextually clean past facts are injected into the agent's prompt.

Securing Cross-Version Stability: Moving the memory execution inside the agent functions and updating the ChromaDB queries to use rigid keyword filters ensures that local environment variations or dependency caching won't cause unexpected internal server errors (500).



