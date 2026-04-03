# Visual Setup & Execution Guide
## LPG Crisis Allocation — OpenEnv Environment

---

## PHASE 1 — Install Prerequisites (Do This First)

```
┌─────────────────────────────────────────────────────────────────┐
│                     YOUR MACHINE SETUP                          │
│                                                                 │
│   Step 1          Step 2           Step 3         Step 4       │
│                                                                 │
│ ┌─────────┐    ┌──────────┐    ┌──────────┐   ┌───────────┐   │
│ │ Python  │───▶│  VS Code │───▶│  Docker  │──▶│    Git    │   │
│ │  3.11+  │    │ + Exts   │    │ Desktop  │   │           │   │
│ └─────────┘    └──────────┘    └──────────┘   └───────────┘   │
│                                                                 │
│  python.org     code.vscode      docker.com     git-scm.com   │
└─────────────────────────────────────────────────────────────────┘
```

### VS Code Extensions to Install (Ctrl+Shift+X → search each):
```
  ✅ Python          (Microsoft)   — language support
  ✅ Pylance         (Microsoft)   — IntelliSense
  ✅ Docker          (Microsoft)   — container management
  ✅ Even Better TOML              — config file support
```

---

## PHASE 2 — Project Folder Structure

```
D:\Meta hackathon\
│
├── 📄 openenv.yaml          ← environment metadata (hackathon reads this)
├── 📄 Dockerfile            ← container definition
├── 📄 requirements.txt      ← Python dependencies
├── 📄 inference.py          ← MAIN script to run the agent
│
├── 📁 lpg_crisis_env\       ← core Python package
│   ├── 📄 __init__.py       ← package entry point
│   ├── 📄 models.py         ← data types (Observation, Action, Reward)
│   ├── 📄 env.py            ← the environment itself
│   ├── 📄 reward.py         ← reward calculation
│   ├── 📄 graders.py        ← task scoring functions
│   ├── 📄 tasks.py          ← task descriptions
│   ├── 📄 trends.py         ← Google Trends induction data (optional)
│   └── 📁 data\
│       └── 📄 districts.py  ← 30 Indian districts data
│
└── 📁 tests\
    └── 📄 test_env.py       ← automated tests
```

---

## PHASE 3 — Terminal Setup Commands (Run in Order)

Open VS Code → Terminal (Ctrl + `)

```
┌──────────────────────────────────────────────────────────┐
│                   TERMINAL COMMANDS                      │
│                 (run top to bottom)                      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  1. Go to project folder                                 │
│     cd "D:\Meta hackathon"                               │
│                                                          │
│  2. Create virtual environment                           │
│     python -m venv .venv                                 │
│                                                          │
│  3. Activate it (Windows)                                │
│     .venv\Scripts\activate                               │
│     ── you'll see (.venv) appear in terminal ──          │
│                                                          │
│  4. Install dependencies                                 │
│     pip install -r requirements.txt                      │
│                                                          │
│  5. Verify install                                       │
│     python -c "from lpg_crisis_env import LPGCrisisEnv;  │
│                print('OK')"                              │
│                                                          │
│  6. Run tests                                            │
│     pytest tests/ -v                                     │
│                                                          │
│  7. Set your API credentials                             │
│     set HF_TOKEN=hf_your_token_here                      │
│     set MODEL_NAME=meta-llama/Llama-3.3-70B-Instruct     │
│     set API_BASE_URL=https://router.huggingface.co/v1    │
│                                                          │
│  8. Run baseline inference                               │
│     python inference.py                                  │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## PHASE 4 — File Dependency Order (Internal)

This shows which files depend on which — **you never run these manually**,
Python imports them automatically. But understanding the order helps debugging.

```
         LAYER 0              LAYER 1            LAYER 2
      (no dependencies)    (uses Layer 0)     (uses Layer 1)
      ┌──────────────┐
      │ data/        │
      │ districts.py │──────────────────────┐
      └──────────────┘                      │
                                            ▼
      ┌──────────────┐              ┌───────────────┐
      │  models.py   │─────────────▶│    env.py     │
      │  (Pydantic)  │              │  (main env)   │
      └──────────────┘              └───────┬───────┘
             │                             │
             │       ┌─────────────┐       │
             └──────▶│  reward.py  │───────┘
                     └─────────────┘
                                            │
                                    ┌───────▼────────┐
                                    │  graders.py    │
                                    │  tasks.py      │
                                    └───────┬────────┘
                                            │
                                    ┌───────▼────────┐
                                    │  __init__.py   │
                                    │  (exports all) │
                                    └───────┬────────┘
                                            │
                           ┌────────────────┴──────────────┐
                           │                               │
                   ┌───────▼───────┐             ┌─────────▼──────┐
                   │ inference.py  │             │ tests/         │
                   │ (run this!)   │             │ test_env.py    │
                   └───────────────┘             └────────────────┘
```

---

## PHASE 5 — What Each File Does (Quick Reference)

```
┌────────────────────┬──────────┬───────────────────────────────────────────┐
│ File               │ You Run? │ Purpose                                   │
├────────────────────┼──────────┼───────────────────────────────────────────┤
│ districts.py       │    NO    │ Raw data: 30 districts, Census 2011       │
│ models.py          │    NO    │ Defines what Observation/Action look like │
│ reward.py          │    NO    │ Calculates reward score each step         │
│ env.py             │    NO    │ The environment: reset(), step(), state() │
│ graders.py         │    NO    │ Scores the agent 0.0–1.0 per task         │
│ tasks.py           │    NO    │ Task descriptions and thresholds          │
│ trends.py          │    NO    │ Optional: live Google Trends data         │
│ __init__.py        │    NO    │ Glues the package together                │
├────────────────────┼──────────┼───────────────────────────────────────────┤
│ tests/test_env.py  │   YES*   │ Verifies everything works correctly       │
│ inference.py       │   YES    │ Runs the LLM agent on all 3 tasks         │
├────────────────────┼──────────┼───────────────────────────────────────────┤
│ Dockerfile         │  docker  │ Packages everything into a container      │
│ openenv.yaml       │ auto     │ Hackathon validator reads this            │
└────────────────────┴──────────┴───────────────────────────────────────────┘
  * via: pytest tests/ -v
```

---

## PHASE 6 — Execution Flow When You Run inference.py

```
python inference.py
        │
        ▼
  Load API credentials
  (HF_TOKEN, MODEL_NAME, API_BASE_URL)
        │
        ▼
  Create OpenAI client
  pointing to HuggingFace Router
        │
        ├──────────────────────────────────────────────┐
        │                                              │
        ▼                                              │
  ┌─────────────┐   TASK 1 (easy)                     │
  │  Reset env  │──▶ 10 districts, 1 day              │
  │  Get obs    │                                      │
  └──────┬──────┘                                      │
         │                                             │
         ▼                                             │
  Format observation                                  │
  as text prompt                                      │
         │                                             │
         ▼                                             │
  Send to LLM (HuggingFace)                           │
  via OpenAI client                                   │
         │                                             │
         ▼                                             │
  Parse JSON response                                 │
  → Action(allocations=[...])                         │
         │                                             │
         ▼                                             │
  env.step(action)                                    │
  ← reward, done, info                                │
         │                                             │
         ▼                                             │
  done? ──NO──▶ loop back                             │
         │                                             │
        YES                                            │
         │                                             │
         ▼                                             │
  grader(env, rewards, final_state)                   │
  → score (0.0 – 1.0)                                 │
         │                                             │
         └──────────────── repeat for TASK 2 & 3 ─────┘
         │
         ▼
  Print final scores table
  PASS / FAIL per task
```

---

## PHASE 7 — Docker Workflow

```
┌─────────────────────────────────────────────────────┐
│                  DOCKER WORKFLOW                    │
│                                                     │
│  1. Build image                                     │
│     ┌─────────────────────────────────────┐         │
│     │ docker build -t lpg-crisis-env .   │         │
│     └─────────────────────────────────────┘         │
│            reads: Dockerfile                        │
│            installs: requirements.txt               │
│            copies: all source files                 │
│                                                     │
│  2. Run container                                   │
│     ┌─────────────────────────────────────┐         │
│     │ docker run --rm \                   │         │
│     │   -e HF_TOKEN=hf_xxx \             │         │
│     │   -e MODEL_NAME=llama-3 \          │         │
│     │   lpg-crisis-env                   │         │
│     └─────────────────────────────────────┘         │
│            runs: python inference.py                │
│                                                     │
│  3. Check it works                                  │
│     ┌─────────────────────────────────────┐         │
│     │ docker images   ← see your image   │         │
│     │ docker ps       ← see running      │         │
│     └─────────────────────────────────────┘         │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## PHASE 8 — HuggingFace Deployment

```
┌─────────────────────────────────────────────────────────────┐
│               DEPLOY TO HF SPACE                            │
│                                                             │
│  1. Create account at huggingface.co                        │
│                                                             │
│  2. Get access token                                        │
│     huggingface.co → Settings → Access Tokens              │
│     → New Token → Role: Write → Copy the hf_xxx token      │
│                                                             │
│  3. Create new Space                                        │
│     huggingface.co/new-space                                │
│     → SDK: Docker                                           │
│     → Tag: openenv                                          │
│     → Visibility: Public                                    │
│                                                             │
│  4. Push your code                                          │
│     git init                                                │
│     git add .                                               │
│     git commit -m "initial submission"                      │
│     git remote add origin                                   │
│       https://huggingface.co/spaces/YOUR_USER/lpg-crisis    │
│     git push origin main                                    │
│                                                             │
│  5. Add secrets in Space Settings                           │
│     HF_TOKEN   = hf_your_token                              │
│     MODEL_NAME = meta-llama/Llama-3.3-70B-Instruct          │
│                                                             │
│  HF Space auto-builds from Dockerfile and runs!            │
└─────────────────────────────────────────────────────────────┘
```

---

## PHASE 9 — Postman API Testing

```
  NEW REQUEST in Postman:

  Method:  POST
  URL:     https://router.huggingface.co/v1/chat/completions

  Headers tab:
  ┌────────────────────┬─────────────────────────────────┐
  │ Authorization      │ Bearer hf_your_token_here       │
  │ Content-Type       │ application/json                │
  └────────────────────┴─────────────────────────────────┘

  Body tab → raw → JSON:
  {
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "messages": [
      {
        "role": "user",
        "content": "Allocate 5000 cylinders across 3 districts fairly."
      }
    ],
    "max_tokens": 200,
    "temperature": 0.1
  }

  Click Send → expect 200 OK with JSON response
  If you get 401 → token is wrong
  If you get 404 → model name is wrong
```

---

## QUICK CHECKLIST

```
  SETUP
  □ Python 3.11+ installed         python --version
  □ VS Code + extensions installed
  □ Docker Desktop installed        docker --version
  □ Git installed                   git --version

  PROJECT
  □ Virtual env created             python -m venv .venv
  □ Dependencies installed          pip install -r requirements.txt
  □ Import works                    python -c "from lpg_crisis_env import LPGCrisisEnv"
  □ All tests pass                  pytest tests/ -v

  API
  □ HuggingFace account created
  □ Token generated (hf_xxx)
  □ Token tested in Postman

  INFERENCE
  □ HF_TOKEN set in terminal
  □ MODEL_NAME set in terminal
  □ inference.py runs successfully

  DEPLOYMENT
  □ Docker image builds             docker build -t lpg-crisis-env .
  □ Docker image runs               docker run --rm -e HF_TOKEN=... lpg-crisis-env
  □ HF Space created (Docker SDK)
  □ Code pushed to HF Space
  □ openenv validate passes
```
