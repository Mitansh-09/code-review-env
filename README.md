# 🔍 Code Review Environment

**Team: Meta Mesh** | OpenEnv Hackathon — Round 1

An OpenEnv-compliant reinforcement learning environment where AI agents learn to perform automated code review across three difficulty levels: syntax error detection, code smell analysis, and security vulnerability identification.

---

## 🎯 Motivation

Code review is one of the most important — and time-consuming — tasks in software engineering. Automating it with AI agents has massive real-world value. This environment trains agents to:
- Detect bugs and syntax errors
- Identify code quality issues and smells
- Find critical security vulnerabilities

---

## 📦 Environment Description

| Property | Value |
|---|---|
| Language | Python |
| Framework | OpenEnv |
| Tasks | 3 (easy → medium → hard) |
| Action Type | Structured JSON (issues list + summary + approval) |
| Reward | Float 0.0–1.0 (composite score) |

---

## 🧠 Observation Space

```json
{
  "task_id": "string",
  "task_name": "string",
  "task_description": "string",
  "code_snippet": "string",
  "language": "python",
  "difficulty": "easy | medium | hard",
  "step_count": 0,
  "max_steps": 5,
  "issues_found_so_far": ["list of issue types"]
}
```

## ⚡ Action Space

```json
{
  "issues": [
    {
      "type": "string (e.g. sql_injection, syntax_error)",
      "line": 42,
      "description": "clear description of the issue",
      "severity": "critical | high | medium | low"
    }
  ],
  "summary": "Overall review summary",
  "approved": false
}
```

---

## 📋 Tasks

### Task 1 — Syntax & Basic Error Detection (Easy)
Identify syntax errors, undefined variables, and type errors in a simple Python function.
- **Max Steps:** 3
- **Expected Issues:** 4 (missing colon, undefined variables, type concatenation error)

### Task 2 — Code Smell & Quality Review (Medium)
Identify code quality issues: poor naming, magic numbers, missing error handling, hardcoded paths, missing docstrings, SRP violations.
- **Max Steps:** 4
- **Expected Issues:** 6

### Task 3 — Security Vulnerability Detection (Hard)
Find critical security vulnerabilities: SQL injection, hardcoded credentials, insecure randomness, path traversal, sensitive data exposure.
- **Max Steps:** 5
- **Expected Issues:** 6 (including critical CVEs)

---

## 🏆 Reward Function

The reward is a composite score (0.0–1.0):

| Component | Weight | Description |
|---|---|---|
| Issue Detection | 60% | Did the agent find the right issues? |
| Issue Count | 15% | Did the agent report the right number? |
| Approval Correctness | 10% | Should the code be approved? |
| Summary Quality | 10% | Is the summary meaningful? |
| Severity Labels | 5% | Did the agent label severity correctly? |

Partial progress is rewarded — agents get signal even for finding some but not all issues.

---

## 🚀 Setup & Usage

### Local Setup

```bash
git clone https://huggingface.co/spaces/MetaMesh/code-review-env
cd code-review-env
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t code-review-env .
docker run -p 7860:7860 code-review-env
```

### API Usage

```python
import requests

# Start a new episode
obs = requests.post("http://localhost:7860/reset", json={"task_id": "task_1_syntax_errors"}).json()

# Take an action
action = {
    "issues": [
        {"type": "syntax_error", "line": 3, "description": "Missing colon in for loop", "severity": "high"}
    ],
    "summary": "Found syntax error on line 3.",
    "approved": False
}
result = requests.post("http://localhost:7860/step", json=action).json()
print(result["reward"]["score"])  # 0.0–1.0
```

### Baseline Script

```bash
export OPENAI_API_KEY=your_key_here
python baseline.py
```

---

## 📊 Baseline Scores

| Task | Model | Score |
|---|---|---|
| Syntax Detection (Easy) | gpt-4o-mini | ~0.75 |
| Code Smell Review (Medium) | gpt-4o-mini | ~0.55 |
| Security Review (Hard) | gpt-4o-mini | ~0.45 |

---

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Health check |
| `/reset` | POST | Start new episode |
| `/step` | POST | Take action |
| `/state` | GET | Get current state |
| `/tasks` | GET | List all tasks |
| `/grader` | POST | Score an action |
| `/baseline` | POST | Run baseline agent |

---

*Built with ❤️ by Meta Mesh for the OpenEnv Hackathon*
