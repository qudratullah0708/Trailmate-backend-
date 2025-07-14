
---

# 🧳 **Smart Travel Planning Chatbot — Project Plan & Tech Stack**

## 🌐 **Project Overview**

A smart travel planning chatbot that helps individuals or groups find **accommodation**, **experiences**, and **budget-friendly trip plans**, powered by **AI agent orchestration**.

---

## 🖥️ **Tech Stack**

✅ **LLM + Toolcalling & Inference:** OpenRouter
✅ **Agent Orchestration:** OpenAI Agents SDK
✅ **Memory Store:** mem0
✅ **Frontend:** Streamlit
✅ **Backend:** FastAPI
✅ **Database & Authentication:** Supabase
✅ **Containerization:** Docker
✅ **Logging:** Python standard logging

---

## 🗂️ **Folder Structure**

The project will follow a clean, modular structure:

```
/agents            # Accommodation, Experience, Budget Optimizer agents
/frontend          # Streamlit frontend code 
/backend           # FastAPI endpoints & orchestration logic
/memory            # mem0 integration
/database          # Supabase utilities
/utils             # Helper functions, logging setup
/config            # Environment and settings files
/tests             # Unit and integration tests
```

---

## 🪜 **Step-by-Step Plan**

### 1️⃣ **Project Setup**

* Initialize Git repository and version control.
* Create the folder structure above.
* Add `.env` for secure configuration of API keys and settings.
* Install dependencies for Python, Streamlit, FastAPI, Supabase client.
* Configure logging with meaningful levels (INFO, ERROR, DEBUG).
* Write a `Dockerfile` and `.dockerignore` for containerization.

### 2️⃣ **Supabase**

* Set up Supabase project with:

  * Tables: `users`, `sessions`, `saved_plans`
  * Authentication: email/password or social login.
* Test Supabase connection from backend.

### 3️⃣ **Memory**

* Integrate mem0 for per-user conversational memory.
* Ensure memory persists across sessions and integrates with Supabase user IDs.

### 4️⃣ **Agents**

* Implement the three independent agents:

  * **Accommodation Agent**
  * **Experience Planner Agent**
  * **Budget Optimizer Agent**
* Define clear APIs and outputs for each.
* Build orchestration logic in FastAPI backend to coordinate them.

### 5️⃣ **Frontend**

* Build Streamlit UI with:

  * Login/register screen (using Supabase auth).
  * Trip planning form: location, dates, preferences, budget.
  * Chat-style conversation interface showing agent responses.
  * Saved trips dashboard for returning users.

### 6️⃣ **Docker**

* Build and test Docker container for the full stack.
* Use `docker-compose` if needed for local development with Supabase emulator.

### 7️⃣ **Testing & Logs**

* Write tests for:

  * Each agent’s logic.
  * Orchestration workflow.
  * Supabase & mem0 integration.
* Review logs regularly to debug and improve reliability.
* Ensure a good user experience on the frontend.

---

## 💡 **Future Enhancements**

✅ Add `pytest` or similar for automated testing.
✅ Use `dotenv` or `pydantic` for config validation.
✅ Enable rate limiting and basic error handling on backend endpoints.
✅ Optionally add monitoring with tools like Prometheus + Grafana or simple log alerts.
✅ Consider adding CI/CD (GitHub Actions) later for automated builds & tests.
✅ Plan for scaling: keep agent implementations stateless where possible.

---

## 🔒 **Environment Variables**

All sensitive keys and configuration (e.g., OpenRouter, Supabase URLs, mem0 credentials) will be kept in `.env` and never committed to version control.

---

## 🚀 **Next Steps**

🟢 **Phase 1:** Setup & Dockerize
🟢 **Phase 2:** Supabase & mem0 integration
🟢 **Phase 3:** Agent development & orchestration
🟢 **Phase 4:** Frontend development
🟢 **Phase 5:** Testing, polish & deploy (to Vercel or DigitalOcean)

---

