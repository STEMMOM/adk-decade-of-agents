# P01 — Minimal Agent Cell

**Series:** Decade of Agents (P01–P10)  
**Status:** Stable · Runnable  
**Goal:** Build the smallest agent cell that thinks once, acts once, and completes a full model-backed execution loop.

---

## What P01 Is (and Is Not)

P01 is **not** a chatbot demo. It is the minimal executable unit of an agent system that already has:
- Identity (`name`)
- Behavioral rules (`instructions`)
- Explicit execution path (`run_once()`)
- Tool interface (`ask_gemini()`)
- Separation of Agent / Tool / Model

Mission: prove your environment, API keys, and code structure support a real agent execution loop, not just a prompt → text response.

---

## Quick Structure

```
adk-decade-of-agents/
  projects/
    p01-minimal-agent/
      README.md
      project.card.yaml
      src/
        main.py
```

`src/main.py` should roughly include:
- `MinimalAgent.__init__(name, instructions, model="gemini-2.0-flash")`
- `ask_gemini(user_question: str) -> str`
- `run_once(user_question: str) -> str`
- `main()` prints a header, defines a real-world question, runs `agent.run_once(...)`, and prints the answer.

Example run:
```bash
(.venv) ➜  p01-minimal-agent git:(main) ✗ python src/main.py
[P01] Minimal Agent Cell Demo
Both GOOGLE_API_KEY and GEMINI_API_KEY are set. Using GOOGLE_API_KEY.
User: What happened in AI this week? Please summarize briefly.

Agent:
AI saw developments in text-to-video, concerns over AI bias in hiring, and continued advancements in large language model capabilities.
```

---

## Prerequisites

### Python & Virtualenv
- Python 3.10+ recommended
- Repo-local venv at `adk-decade-of-agents/.venv`
- Activate:
  - macOS/Linux: `source .venv/bin/activate`
  - Windows PowerShell: `.venv\Scripts\Activate.ps1`

### Dependencies
Install inside the venv:
```bash
pip install google-genai
```

### API Keys (.env)
At repo root `adk-decade-of-agents/.env`:
```
GOOGLE_API_KEY=YOUR_GEMINI_KEY_FROM_AI_STUDIO
GEMINI_API_KEY=YOUR_GEMINI_KEY_FROM_AI_STUDIO
```
Use keys from Google AI Studio (not GCP Console).

`.gitignore` should cover:
```
.env
*.env
*.key
*.pem
```

Load env vars into the shell:
```bash
cd /Users/Agent/adk-decade-of-agents
export $(grep -v '^#' .env | xargs)
```

Sanity check:
```bash
python - << 'EOF'
from google import genai
client = genai.Client()
resp = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say 'API_OK' only."
)
print("Model response:", resp.text)
EOF
```
Expected: `Model response: API_OK`

---

## How to Run

From project directory:
```bash
cd /Users/Agent/adk-decade-of-agents/projects/p01-minimal-agent
python src/main.py
```

Expected behavior:
- Prints header `[P01] Minimal Agent Cell Demo`
- Shows user question (e.g., “What happened in AI this week?”)
- Calls Gemini once via `ask_gemini`
- Prints answer under `Agent:`

---

## What to Observe

- **Identity & rules:** Constructed agent with attached instructions.
- **Explicit execution path:** `run_once` wraps thought → tool → model → output.
- **Tool abstraction:** `ask_gemini` is a tool hook; later can call search/APIs/db/etc.
- **System, not UI:** No web/chat UI; this is an agent process.

---

## Road to P02–P10

- P02: Stateful sessions & event ledger  
- P03: Observability (logs/traces/metrics)  
- P04: Memory & persona  
- P05: Planner (plan → act → reflect → retry)  
- P06: ToolPack  
- P07: Model routing  
- P08: Multi-agent  
- P09: Governance & ACL  
- P10: Self-evolving runtime  

P01 is the first heartbeat for all of these.

---

## Debug Notes

- **API key not valid:** Use Gemini key from Google AI Studio, not GCP Console.
- **ClientError / HTTP 400–403:** Check model name `gemini-2.0-flash` (or current).
- **ModuleNotFoundError: google.genai:** `pip install google-genai` in your venv.

Once `API_OK` passes and P01 prints a valid AI answer, you’re ready for P02.
