from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import CodeReviewEnv
from models import Action, StepResult, EnvironmentState, Observation
from tasks import get_task_list

app = FastAPI(
    title="Code Review Environment — Meta Mesh",
    description="OpenEnv-compliant RL environment for AI code review agents.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

env = CodeReviewEnv()


@app.get("/")
def root():
    return {"status": "ok", "environment": "code-review-env", "team": "Meta Mesh"}


class ResetRequest(BaseModel):
    task_id: Optional[str] = "task_1_syntax_errors"


@app.post("/reset", response_model=Observation)
def reset(request: ResetRequest = Body(default=ResetRequest())):
    try:
        obs = env.reset(task_id=request.task_id)
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResult)
def step(action: Action):
    try:
        result = env.step(action)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/state", response_model=EnvironmentState)
def state():
    return env.state()


@app.get("/tasks")
def tasks():
    return {"tasks": get_task_list()}


@app.post("/grader")
def grader(action: Action):
    if env._task_data is None:
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")
    from graders import grade
    reward = grade(env._task_data, action)
    return reward


@app.post("/baseline")
def baseline():
    try:
        from inference import main
        scores = main()
        return {"baseline_scores": scores}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Baseline failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
