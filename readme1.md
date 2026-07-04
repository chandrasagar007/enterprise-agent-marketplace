# 🤖 Sample Project — AI Agent API (FastAPI + LangGraph)

A simple AI Agent API that can:
- Answer questions
- Get weather
- Get current date/time
- Search web

Built using:
- FastAPI (API layer)
- LangGraph (Agent)
- OpenAI (LLM)
- Tools (Weather, Search, Calculator)

---

# 📁 Project Structure

```text
project/
├── app.py              # FastAPI server (API entry point)
├── agent.py            # AI Agent (LLM + tools logic)
├── tools.py            # All tools (weather, datetime, search)
├── .env                # API keys (DO NOT share)
├── requirements.txt    # Dependencies
└── test_api.py         # API testing file

⚙️ Setup Instructions
1. Install Dependencies
uv pip install -r requirements.txt
2. Add API Key

Create a .env file:

OPENAI_API_KEY=your_openai_key_here
🚀 Run the Project (IMPORTANT)
Step 1 — Start FastAPI Server

Run this in Terminal 1:

uv run uvicorn app:app --host 0.0.0.0 --port 8000 --reload

RUn this in Termianl 2:

ngrok http 8000


What this does:

Starts your API server
Runs on: http://localhost:8000
Enables auto-reload when code changes
Step 2 — Open API in Browser

Now open:

http://127.0.0.1:8000/docs

You will see Swagger UI where you can test API.

🌐 How to Expose API to Internet (NGROK)
Step 1 — Install Ngrok
Mac (recommended)
brew install ngrok/ngrok/ngrok

OR download from:

https://ngrok.com/download

Step 2 — Login to Ngrok

Create free account:

https://dashboard.ngrok.com/signup

Then get your auth token:

https://dashboard.ngrok.com/get-started/your-authtoken

Run this:

ngrok config add-authtoken YOUR_AUTH_TOKEN
Step 3 — Start Public Tunnel

Run this in Terminal 2:

ngrok http 8000
Step 4 — You will see output like this:
Forwarding:
https://abc123.ngrok-free.app  → http://localhost:8000
Step 5 — Use Public API

Now your API is LIVE on the internet 🎉

Open:

https://abc123.ngrok-free.app/docs

You can:

Test API from mobile
Share with anyone
Call from frontend apps
🧪 Example API Request
POST /chat
{
  "question": "What is the weather in Bangalore?"
}
Example Response
{
  "question": "What is the weather in Bangalore?",
  "answer": "Temperature: 27°C, Wind Speed: 10 km/h"
}
🔧 Common Issues
❌ Port already running
lsof -i :8000
kill -9 <PID>
❌ API not responding on ngrok

Make sure:

FastAPI is running FIRST
Then run ngrok
Both terminals should stay open
🧠 What You Built (Simple View)
User
  ↓
FastAPI API
  ↓
AI Agent (LangGraph)
  ↓
Tools
  ├── Weather
  ├── DateTime
  ├── Search
  └── Calculator
  ↓
OpenAI LLM
🚀 Next Learning Steps

After this project, improve step-by-step:

Level 1
Add logging (store requests-store logs)
Add error handling

Level 2
Add authentication (API keys)
Add request limits

Level 3
Add observability (Langfuse)
Track cost + latency
add 
Level 4
Add multiple agents (Router Agent)
Weather Agent / Finance Agent / Search Agent

Level 5
Deploy on AWS (real production)
Use Docker + API Gateway

🎯 Summary

You now have:

✔ AI Agent
✔ API Server
✔ Tool calling
✔ Local testing
✔ Internet exposure (Ngrok)

This is your first working AI Agent product API 🚀



###############
Level 1
✓ Logging
✓ Error Handling

Level 2
→ Request Validation
→ API Key Authentication
→ Rate Limiting

Level 3
-> Memory

Level 4
→ Langfuse Observability
→ Cost Tracking
→ Latency Tracking

Level 5
→ Multi-Agent Architecture
→ Agent Gateway

Level 6
→ Docker
→ AWS Deployment
→ API Gateway
→ Monitoring


############
Level 0  → Basic Agent API           ✅
Level 1  → Logging & Error Handling  ✅
Level 2  → Auth + Limits             ✅
Level 3  → Memory                    ← NEXT
Level 4  → Multi-Agent Support
Level 5  → Observability (Langfuse)
Level 6  → Agent Governance
Level 7  → Human-in-the-Loop
Level 8  → Multi-Tenant SaaS
Level 9  → Agent Marketplace
Level 10 → Enterprise AI Platform