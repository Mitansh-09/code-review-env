from typing import Dict, Any, Optional
from environment.models import Observation, Action, Reward, StepResult, EnvironmentState
from environment.tasks import TASKS
from environment.graders import grade


class CodeReviewEnv:
    """
    OpenEnv-compliant Code Review Environment.

    An AI agent is given a code snippet and must identify issues (bugs,
    code smells, or security vulnerabilities) across 3 difficulty levels.

    Interface:
        reset(task_id)  → Observation
        step(action)    → StepResult (observation, reward, done, info)
        state()         → EnvironmentState
    """

    def __init__(self):
        self._task_id: Optional[str] = None
        self._task_data: Optional[Dict[str, Any]] = None
        self._step_count: int = 0
        self._done: bool = False
        self._cumulative_reward: float = 0.0
        self._history: list = []

    # ─────────────────────────────────────────
    # reset() — start a new episode
    # ─────────────────────────────────────────
    def reset(self, task_id: str = "task_1_syntax_errors") -> Observation:
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Choose from: {list(TASKS.keys())}")

        self._task_id = task_id
        self._task_data = TASKS[task_id]
        self._step_count = 0
        self._done = False
        self._cumulative_reward = 0.0
        self._history = []

        return self._build_observation()

    # ─────────────────────────────────────────
    # step() — agent takes one action
    # ─────────────────────────────────────────
    def step(self, action: Action) -> StepResult:
        if self._task_data is None:
            raise RuntimeError("Call reset() before step()")
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._step_count += 1

        # Grade the action
        reward: Reward = grade(self._task_data, action)
        self._cumulative_reward += reward.score

        # Penalize infinite loops / nonsense actions
        if len(action.issues) == 0 and len(action.summary.strip()) < 5:
            reward.score = max(0.0, reward.score - 0.05)
            reward.feedback += "\n⚠️ Penalty: Empty action submitted."

        # Track issues found so far
        found_types = [
            str(i.get("type", "")) for i in action.issues
        ]
        self._history.extend(found_types)

        # Episode ends when: max steps reached OR agent achieves perfect score
        max_steps = self._task_data.get("max_steps", 5)
        self._done = (
            self._step_count >= max_steps or
            reward.score >= 0.95
        )

        obs = self._build_observation()

        info = {
            "step": self._step_count,
            "max_steps": max_steps,
            "cumulative_reward": round(self._cumulative_reward, 4),
            "task_id": self._task_id,
        }

        return StepResult(
            observation=obs,
            reward=reward,
            done=self._done,
            info=info
        )

    # ─────────────────────────────────────────
    # state() — current environment state
    # ─────────────────────────────────────────
    def state(self) -> EnvironmentState:
        if self._task_data is None:
            return EnvironmentState(
                task_id="none",
                step_count=0,
                max_steps=0,
                episode_done=True,
                cumulative_reward=0.0,
                current_task="No active episode"
            )
        return EnvironmentState(
            task_id=self._task_id,
            step_count=self._step_count,
            max_steps=self._task_data.get("max_steps", 5),
            episode_done=self._done,
            cumulative_reward=round(self._cumulative_reward, 4),
            current_task=self._task_data.get("task_name", "")
        )

    # ─────────────────────────────────────────
    # Internal helper
    # ─────────────────────────────────────────
    def _build_observation(self) -> Observation:
        return Observation(
            task_id=self._task_data["task_id"],
            task_name=self._task_data["task_name"],
            task_description=self._task_data["task_description"],
            code_snippet=self._task_data["code_snippet"],
            language=self._task_data.get("language", "python"),
            difficulty=self._task_data["difficulty"],
            step_count=self._step_count,
            max_steps=self._task_data.get("max_steps", 5),
            issues_found_so_far=list(set(self._history))
        )
