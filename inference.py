"""
Inference script for Code Review Environment — Meta Mesh
OpenEnv Hackathon, Round 1

Environment variables required:
    API_BASE_URL   The API endpoint for the LLM (OpenAI-compatible)
    MODEL_NAME     The model identifier to use for inference
    HF_TOKEN       Your Hugging Face / API key
"""

import os
import json
from openai import OpenAI
from env import CodeReviewEnv
from models import Action

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")

TEMPERATURE  = 0.0
MAX_TOKENS   = 1000
FALLBACK_ACTION = '{"issues": [], "summary": "Model request failed.", "approved": false}'

TASK_IDS = [
    "task_1_syntax_errors",
    "task_2_code_smells",
    "task_3_security",
]

SYSTEM_PROMPT = """\
You are an expert code reviewer. You will be given a code snippet and a task description.
Your job is to identify all issues in the code.

Respond ONLY with a valid JSON object in this exact format:
{
  "issues": [
    {
      "type": "string (e.g. syntax_error, undefined_variable, sql_injection, etc.)",
      "line": <line_number_as_integer>,
      "description": "clear description of the issue",
      "severity": "critical | high | medium | low"
    }
  ],
  "summary": "overall review summary (2-3 sentences)",
  "approved": false
}

Be thorough. Do not include markdown, code blocks, or any text outside the JSON.
"""


def parse_model_action(response_text: str) -> dict:
    clean = response_text.strip()
    if clean.startswith("```"):
        clean = clean.split("```")[1]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        print(f"[WARN] JSON parse failed. Raw:\n{response_text}")
        return {"issues": [], "summary": "Parse error", "approved": False}


def main():
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN environment variable not set.")

    print(f"API_BASE_URL : {API_BASE_URL}")
    print(f"MODEL_NAME   : {MODEL_NAME}")

    client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)
    env = CodeReviewEnv()
    results = {}

    for task_id in TASK_IDS:
        print(f"\n{'='*50}\nTask: {task_id}\n{'='*50}")
        obs = env.reset(task_id=task_id)
        print(f"Name: {obs.task_name} | Difficulty: {obs.difficulty}")

        for step in range(obs.max_steps):
            user_content = f"""Task: {obs.task_name}
Difficulty: {obs.difficulty}

Instructions:
{obs.task_description}

Code to Review:
```{obs.language}
{obs.code_snippet}
```

Issues found so far: {obs.issues_found_so_far}
Step: {obs.step_count + 1} / {obs.max_steps}
"""
            messages = [
                {"role": "system", "content": [{"type": "text", "text": SYSTEM_PROMPT}]},
                {"role": "user", "content": user_content},
            ]

            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=TEMPERATURE,
                    max_tokens=MAX_TOKENS,
                    stream=False,
                )
                response_text = completion.choices[0].message.content or ""
            except Exception as exc:
                print(f"Model request failed ({exc}). Using fallback.")
                response_text = FALLBACK_ACTION

            parsed = parse_model_action(response_text)
            action = Action(
                issues=parsed.get("issues", []),
                summary=parsed.get("summary", ""),
                approved=parsed.get("approved", False),
            )

            result = env.step(action)
            print(f"Step {step+1}: {len(action.issues)} issues -> reward {result.reward.score:+.4f} | Done: {result.done}")
            obs = result.observation

            if result.done:
                print("Episode complete.")
                break

        results[task_id] = {
            "task_name": obs.task_name,
            "difficulty": obs.difficulty,
            "final_score": result.reward.score,
            "breakdown": result.reward.breakdown,
            "issues_reported": len(action.issues),
        }

    print(f"\n\n{'='*50}\nINFERENCE SUMMARY\n{'='*50}")
    scores = []
    for task_id, data in results.items():
        print(f"{data['task_name']} ({data['difficulty']}): {data['final_score']:.4f}")
        scores.append(data["final_score"])

    avg = sum(scores) / len(scores)
    print(f"\nAverage Score: {avg:.4f}")
    results["average_score"] = round(avg, 4)
    return results


if __name__ == "__main__":
    main()
