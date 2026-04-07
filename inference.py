"""
Inference script for Code Review Environment — Meta Mesh
"""

import os
import json
from typing import List, Optional
from openai import OpenAI
from env import CodeReviewEnv
from models import Action

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN     = os.environ.get("HF_TOKEN", "")

TEMPERATURE  = 0.0
MAX_TOKENS   = 1000
BENCHMARK    = "code-review-env"

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


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)


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
        return {"issues": [], "summary": "Parse error", "approved": False}


def main():
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN environment variable not set.")

    client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)
    env = CodeReviewEnv()
    results = {}

    for task_id in TASK_IDS:
        log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

        obs = env.reset(task_id=task_id)

        rewards: List[float] = []
        steps_taken = 0
        score = 0.0
        success = False
        result = None

        try:
            for step in range(1, obs.max_steps + 1):
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
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ]

                error = None
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
                    error = str(exc)
                    response_text = '{"issues": [], "summary": "Model request failed.", "approved": false}'

                parsed = parse_model_action(response_text)
                action = Action(
                    issues=parsed.get("issues", []),
                    summary=parsed.get("summary", ""),
                    approved=parsed.get("approved", False),
                )

                result = env.step(action)
                reward = result.reward.score
                done = result.done
                rewards.append(reward)
                steps_taken = step
                obs = result.observation

                action_str = f"issues={len(action.issues)}"
                log_step(step=step, action=action_str, reward=reward, done=done, error=error)

                if done:
                    break

            score = max(rewards) if rewards else 0.0
            success = score >= 0.5

        finally:
            log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

        results[task_id] = {
            "task_name": obs.task_name,
            "final_score": score,
            "issues_reported": len(action.issues) if result else 0,
        }

    return results


if __name__ == "__main__":
    main()
