# ⚡ Quick Start Guide

Get started with the School Operations Environment in 5 minutes!

---

## Installation

```bash
# Clone or navigate to project
cd school_operations_env

# Run setup script
bash setup.sh

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

---

## Verify Installation

```bash
# Run validation
python validate_environment.py

# Expected output: 15 passed, 0 failed ✓
```

---

## Run Tests

```bash
# Run comprehensive test suite
python test_environment.py

# Expected output: Ran 18 tests - OK ✓
```

---

## Try Interactive Mode

```bash
# Start Gradio app
python app.py

# Opens at: http://localhost:7860
```

### Interactive Features:
1. **Select Difficulty:** Easy, Medium, or Hard
2. **Click "Initialize Environment"**
3. **Solve the task** displayed (email, schedule, or support response)
4. **View reward and feedback**
5. **Track episode history**

---

## Run Baseline Evaluation

```bash
# Set API key (get from https://platform.openai.com/account/api-keys)
export HF_TOKEN="sk-..."  # or OPENAI_API_KEY

# Run baseline
python baseline_inference.py

# Results saved to: baseline_results.json
```

---

## Use Environment Programmatically

### Example 1: Email Classification

```python
from environment import SchoolOperationsEnv
from models import DifficultyLevel, Action, TaskType, EmailAction

# Initialize
env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)

# Reset for first task
observation = env.reset()

print(f"Task: {observation.task_type.value}")
print(f"Email from: {observation.email_data.sender}")
print(f"Subject: {observation.email_data.subject}")

# Submit action
action = Action(
    task_type=TaskType.EMAIL_CLASSIFICATION,
    email_action=EmailAction(category="academic")
)

# Get reward
next_obs, reward, done, info = env.step(action)

print(f"\nReward: {reward.total_reward:.3f}")
print(f"Feedback: {reward.feedback}")
print(f"Done: {done}")
```

### Example 2: Timetable Scheduling

```python
from environment import SchoolOperationsEnv
from models import DifficultyLevel, Action, TaskType, ScheduleAction, ScheduleSlot

env = SchoolOperationsEnv(difficulty=DifficultyLevel.MEDIUM, seed=42)
observation = env.reset()

# View constraints
for constraint in observation.schedule_constraints:
    print(f"Class: {constraint.class_name}")
    print(f"  Teacher: {constraint.teacher}")
    print(f"  Duration: {constraint.duration_minutes} min")

# Create schedule
action = Action(
    task_type=TaskType.TIMETABLE_SCHEDULING,
    schedule_action=ScheduleAction(schedule=[
        ScheduleSlot(
            class_name="Class_A",
            day="Monday",
            start_time="09:00",
            end_time="10:30",
            location="101"
        ),
        ScheduleSlot(
            class_name="Class_B",
            day="Tuesday",
            start_time="10:00",
            end_time="11:00",
            location="102"
        ),
    ])
)

next_obs, reward, done, info = env.step(action)
print(f"\nSchedule Score: {reward.breakdown.task_score:.3f}")
print(f"Details: {reward.feedback}")
```

### Example 3: Student Support Response

```python
from environment import SchoolOperationsEnv
from models import DifficultyLevel, Action, TaskType, SupportResponse

env = SchoolOperationsEnv(difficulty=DifficultyLevel.HARD, seed=42)
observation = env.reset()

query = observation.student_query
print(f"Student: {query.student_name}")
print(f"Issue: {query.issue_type}")
print(f"Query: {query.query}")

# Generate response
action = Action(
    task_type=TaskType.STUDENT_SUPPORT,
    support_action=SupportResponse(
        response="I understand your concern about calculus. Let me connect you with our tutoring resources and schedule a meeting with Ms. Smith to create a study plan.",
        action_items=[
            "Schedule meeting with tutor",
            "Join study group on Thursdays",
            "Complete practice problems"
        ],
        urgency="medium"
    )
)

next_obs, reward, done, info = env.step(action)
print(f"\nResponse Score: {reward.breakdown.task_score:.3f}")
print(f"Breakdown:")
print(f"  - Keyword Coverage: {reward.breakdown.task_score:.3f}")
print(f"  - Efficiency Bonus: {reward.breakdown.efficiency_bonus:.3f}")
print(f"  - Partial Credit: {reward.breakdown.partial_credit:.3f}")
```

---

## Check Environment State

```python
from environment import SchoolOperationsEnv
from models import DifficultyLevel

env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY)
env.reset()

state = env.state()

print(f"Episode: {state.episode_number}")
print(f"Episode ID: {state.episode_id}")
print(f"Task: {state.current_task.task_type.value}")
print(f"Steps: {state.current_task.steps_taken}/{state.current_task.max_steps}")
print(f"Cumulative Reward: {state.current_task.cumulative_reward:.3f}")
print(f"Timestamp: {state.timestamp}")
```

---

## Understand Rewards

Each step returns a reward with breakdown:

```python
reward.total_reward          # [-1.0, 1.0] - final score
reward.breakdown.task_score  # [0.0, 1.0] - grader score
reward.breakdown.efficiency_bonus    # [-0.1, 0.1] - quick solutions
reward.breakdown.partial_credit      # [0.0, 0.2] - incremental progress
reward.breakdown.penalty             # [-1.0, 0.0] - violations
reward.feedback              # Human-readable feedback
reward.is_terminal           # True when episode complete
```

---

## Common Issues

### "API key not found"
```bash
export HF_TOKEN="your-key-here"
# or
export OPENAI_API_KEY="your-key-here"
```

### "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### "Port already in use"
```bash
# Use different port
python app.py --server_port 8000
```

---

## Next Steps

- 📖 Read full [README.md](README.md)
- 🚀 Deploy to [Hugging Face Spaces](DEPLOYMENT.md)
- 🧪 Run full test suite: `python test_environment.py`
- 📊 Generate baseline: `python baseline_inference.py`
- 📝 Review [openenv.yaml](openenv.yaml) for full spec

---

## Get Help

- **Issues:** Check validation: `python validate_environment.py`
- **Tests:** Run tests: `python test_environment.py`
- **Examples:** Check scripts in repo
- **Docs:** See README.md for comprehensive documentation

---

**Ready to use! Happy evaluating! 🎓**
