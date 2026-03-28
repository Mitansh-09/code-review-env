from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class Observation(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    task_name: str = Field(..., description="Human-readable task name")
    task_description: str = Field(..., description="What the agent must do")
    code_snippet: str = Field(..., description="The code to review")
    language: str = Field(default="python", description="Programming language")
    difficulty: str = Field(..., description="easy | medium | hard")
    step_count: int = Field(default=0, description="Steps taken in this episode")
    max_steps: int = Field(default=5, description="Max steps per episode")
    issues_found_so_far: List[str] = Field(default_factory=list, description="Issues agent has reported so far")


class Action(BaseModel):
    issues: List[Dict[str, Any]] = Field(
        ...,
        description="List of issues found. Each issue: {type, line, description, severity}"
    )
    summary: str = Field(..., description="Overall review summary")
    approved: bool = Field(..., description="Whether code passes review")


class Reward(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0, description="Reward score 0.0-1.0")
    breakdown: Dict[str, float] = Field(..., description="Per-criterion scores")
    feedback: str = Field(..., description="Human-readable feedback on the action")


class StepResult(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any]


class EnvironmentState(BaseModel):
    task_id: str
    step_count: int
    max_steps: int
    episode_done: bool
    cumulative_reward: float
    current_task: str
