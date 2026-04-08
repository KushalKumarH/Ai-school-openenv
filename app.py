from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Action(BaseModel):
    action: str

# Dummy state
current_state = {"task": "email_classification"}

@app.post("/reset")
def reset():
    return {
        "observation": "New email: I need help with math",
        "reward": 0.0,
        "done": False,
        "info": {}
    }

@app.post("/step")
def step(action: Action):
    if action.action == "academic":
        return {
            "observation": "Correct",
            "reward": 1.0,
            "done": True,
            "info": {}
        }
    else:
        return {
            "observation": "Wrong",
            "reward": 0.0,
            "done": True,
            "info": {}
        }

@app.get("/state")\ndef state():\n    return current_state\n\n@app.get("/health")\ndef health():\n    return {\"status\": \"healthy\"}\n\n@app.get("/")\ndef root():\n    return {\"OpenEnv\": \"School Operations Environment\"}
