# 🎓 AI-Powered School Operations Evaluation Environment

An **OpenEnv-compliant** environment for evaluating AI agents on real-world school operations tasks including email triage, timetable scheduling, and student support response generation.

[![OpenEnv](https://img.shields.io/badge/OpenEnv-Compliant-brightgreen)](https://github.com/openenv/openenv)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

---

## 📋 Overview

This environment simulates **real-world school operations tasks** that educators and administrators encounter daily. It provides a benchmark for evaluating how well AI agents can handle nuanced decision-making across three domains of increasing complexity:

1. **Email Classification (Easy)** - Categorize incoming emails
2. **Timetable Scheduling (Medium)** - Create conflict-free class schedules
3. **Student Support Response (Hard)** - Generate empathetic, contextual support responses

### Key Features

✅ **Full OpenEnv Specification Compliance** - Typed Pydantic models, step/reset/state interface, YAML manifest
✅ **Deterministic Graders** - Reproducible evaluation using keyword matching, constraint checking, and multi-criteria scoring
✅ **Three Task Difficulties** - Easy, Medium, Hard progression
✅ **Meaningful Reward Signals** - Task score + efficiency bonus + partial credit + penalties
✅ **Reproducible Baseline** - GPT-4 baseline with ~82-95% performance across tasks
✅ **Production-Ready** - Dockerized, deployed to Hugging Face Spaces, comprehensive documentation

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://huggingface.co/spaces/raccoon-ai/school-operations-env
cd school_operations_env

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Baseline

```bash
# Set up API credentials
export HF_TOKEN="your-openai-api-key"  # Or OPENAI_API_KEY

# Run baseline evaluation
python baseline_inference.py

# Results saved to baseline_results.json
```

### Using the Environment

```python
from environment import SchoolOperationsEnv
from models import DifficultyLevel, EmailAction, Action, TaskType

# Initialize environment
env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)

# Reset for first observation
observation = env.reset()

# Generate and execute action
action = Action(
    task_type=TaskType.EMAIL_CLASSIFICATION,
    email_action=EmailAction(category="academic")
)

# Step and get reward
next_obs, reward, done, info = env.step(action)

print(f"Reward: {reward.total_reward:.3f}")
print(f"Feedback: {reward.feedback}")
print(f"Episode Complete: {done}")
```

---

## 📊 Task Descriptions

### Task 1: Email Classification (Easy)

**Objective:** Categorize incoming student/parent emails into one of 6 categories

**Input (Observation):**
```python
EmailData(
    subject: str,      # Email subject line
    body: str,         # Email body content
    sender: str        # Sender identifier
)
```

**Output (Action):**
```python
EmailAction(
    category: Literal["admission", "academic", "behavioral", "health", "extracurricular", "other"]
)
```

**Grading:**
- **Method:** Exact match against ground truth (inferred from email content)
- **Score:** 1.0 if correct, 0.0 if incorrect
- **Keywords by Category:**
  - `admission`: "admit", "enrollment", "application", "registration"
  - `academic`: "grade", "homework", "exam", "course"
  - `behavioral`: "behavior", "discipline", "incident", "bullying"
  - `health`: "health", "medical", "illness", "medication"
  - `extracurricular`: "club", "sports", "event", "competition"

**Example:**
```
Subject: "Midterm exam results"
Body: "The midterm exam scores are now available..."
→ Correct Category: "academic"
```

---

### Task 2: Timetable Scheduling (Medium)

**Objective:** Schedule classes across Monday-Friday (9:00-15:00) respecting constraints

**Input (Observation):**
```python
ScheduleConstraint(
    class_name: str,              # e.g., "Class_A"
    teacher: str,                 # e.g., "Ms. Smith"
    duration_minutes: int,        # Total class duration needed
    students: List[str],          # Student names
    preferred_times: List[str]    # Optional preferred slots
)
```

**Output (Action):**
```python
ScheduleSlot(
    class_name: str,              # Must match input class_name
    day: Literal["Mon"-"Fri"],
    start_time: str,              # "HH:MM" format
    end_time: str,                # "HH:MM" format
    location: str                 # Room identifier
)
```

**Grading Criteria:**
1. **No Time Clashes (50%):** Same room can't have overlapping classes
2. **Duration Compliance (35%):** Total scheduled time = constraint duration
3. **Preference Satisfaction (15%):** Bonus for respecting preferred times

**Example:**
```python
# Input
ScheduleConstraint(
    class_name="Class_A",
    teacher="Ms. Smith",
    duration_minutes=90,
    students=["Alice", "Bob", "Charlie"],
    preferred_times=["09:00", "14:00"]
)

# Valid Output
[
    ScheduleSlot(class_name="Class_A", day="Monday", start_time="09:00", end_time="10:30", location="101"),
]
```

---

### Task 3: Student Support Response (Hard)

**Objective:** Generate appropriate support response to student query

**Input (Observation):**
```python
StudentQuery(
    student_name: str,
    issue_type: str,              # "academic", "behavioral", "health", "personal"
    query: str,                   # Detailed query
    context: Optional[str]        # Background information
)
```

**Output (Action):**
```python
SupportResponse(
    response: str,                # Support message
    action_items: List[str],      # Follow-up actions
    urgency: Literal["low", "medium", "high"]
)
```

**Grading Criteria:**
1. **Keyword Coverage (25%):** Does response include issue-relevant keywords?
   - Academic: "help", "tutor", "resource", "study"
   - Behavioral: "discuss", "understand", "improvement"
   - Health: "nurse", "doctor", "medical", "wellness"
2. **Correctness (40%):** Does response address the query appropriately?
   - Acknowledges the issue
   - Proposes solutions or next steps
3. **Tone (25%):** Is the response supportive and non-judgmental?
   - Positive tone keywords: "support", "help", "together"
   - Avoid negative: "fail", "bad", "wrong"
4. **Action Items (10%):** Bonus for including concrete next steps

**Example:**
```
Query: "I'm struggling with calculus and my grades are dropping."

Good Response:
"I understand calculus can be challenging. We have tutoring resources available 
through the academic center, and I'd recommend meeting with your teacher Ms. Smith 
for specific guidance. Let's set up a plan together."

Scores:
- Keywords: 0.67 (help, resource, tutor present)
- Correctness: 1.0 (acknowledges + proposes solutions)
- Tone: 1.0 (supportive, collaborative)
- Action items: +0.1 (specific next steps mentioned)
→ Total: 0.92
```

---

## 🏗️ Architecture

### Environment Interface

```python
class SchoolOperationsEnv:
    
    def reset() -> Observation:
        """Initialize episode, return initial observation"""
        
    def step(action: Action) -> Tuple[Observation, Reward, bool, Dict]:
        """Execute action, return (next_obs, reward, done, info)"""
        
    def state() -> EnvironmentState:
        """Return current environment state"""
```

### Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `task_type` | TaskType enum | Current task (email_classification, timetable_scheduling, student_support) |
| `difficulty` | DifficultyLevel enum | Task difficulty (easy, medium, hard) |
| `step_number` | int | Current step in episode |
| `max_steps` | int | Maximum steps allowed (5 for easy, 10 for medium, 15 for hard) |
| `email_data` | EmailData \| None | For email classification task |
| `schedule_constraints` | List[ScheduleConstraint] \| None | For scheduling task |
| `student_query` | StudentQuery \| None | For support task |
| `timestamp` | str | ISO 8601 timestamp |
| `episode_id` | str | Unique episode identifier |

### Action Space

| Field | Type | Description |
|-------|------|-------------|
| `task_type` | TaskType enum | Must match observation task_type |
| `email_action` | EmailAction \| None | For email classification |
| `schedule_action` | ScheduleAction \| None | For scheduling |
| `support_action` | SupportResponse \| None | For support response |

### Reward Space

```python
Reward(
    total_reward: float,           # [-1.0, 1.0]
    breakdown: RewardBreakdown(
        task_score: float,         # [0.0, 1.0] - main grader score
        efficiency_bonus: float,   # [-0.1, 0.1] - quick solutions
        partial_credit: float,     # [0.0, 0.2] - incremental progress
        penalty: float             # [-1.0, 0.0] - violations
    ),
    feedback: str,                 # Human-readable feedback
    is_terminal: bool              # Episode complete?
)
```

---

## 📈 Baseline Performance

Evaluated using **GPT-4** with **10 episodes per difficulty** (seed=42):

| Task | Difficulty | Score | Notes |
|------|-----------|-------|-------|
| Email Classification | Easy | 0.95 | Excellent keyword recognition |
| Timetable Scheduling | Medium | 0.87 | Minor constraint violations on complex schedules |
| Student Support | Hard | 0.82 | Good coverage, tone mostly appropriate |
| **Overall Average** | - | **0.88** | Reproducible across runs |

**Reproducibility:** Set `seed=42` in `baseline_inference.py` for identical results

---

## 🔧 Configuration

### Environment Parameters

```python
env = SchoolOperationsEnv(
    difficulty=DifficultyLevel.MEDIUM,  # Easy, Medium, or Hard
    seed=42                              # For reproducibility
)
```

### Max Steps by Difficulty

| Difficulty | Max Steps | Termination Condition |
|-----------|-----------|----------------------|
| Easy | 5 | Score ≥ 0.8 OR max steps reached |
| Medium | 10 | Score ≥ 0.8 OR max steps reached |
| Hard | 15 | Score ≥ 0.8 OR max steps reached |

### Reward Function

```
total_reward = task_score + efficiency_bonus + partial_credit + penalty

- task_score: 0.0-1.0 from grader
- efficiency_bonus: +0.1 if solved in ≤2 steps, +0.05 if ≤5 steps
- partial_credit: +0.1 if 0.5≤score<0.8, +0.05 if 0.3≤score<0.5
- penalty: -0.05 if steps > 80% of max_steps
```

---

## 📚 API Examples

### Email Classification Example

```python
from environment import SchoolOperationsEnv
from models import DifficultyLevel, Action, TaskType, EmailAction

env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY)
obs = env.reset()

# Create action
action = Action(
    task_type=TaskType.EMAIL_CLASSIFICATION,
    email_action=EmailAction(category="academic")
)

# Execute step
next_obs, reward, done, info = env.step(action)

print(f"Reward: {reward.total_reward}")
print(f"Feedback: {reward.feedback}")
print(f"Breakdown: {reward.breakdown.model_dump()}")
```

### Timetable Scheduling Example

```python
from models import ScheduleAction, ScheduleSlot

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
            day="Monday",
            start_time="11:00",
            end_time="12:00",
            location="102"
        ),
    ])
)

next_obs, reward, done, info = env.step(action)
```

### Student Support Example

```python
from models import SupportResponse

action = Action(
    task_type=TaskType.STUDENT_SUPPORT,
    support_action=SupportResponse(
        response="I understand your concerns about calculus. Let me help you connect with tutoring resources...",
        action_items=[
            "Schedule meeting with Ms. Smith",
            "Register for tutoring program",
            "Complete practice problems by Friday"
        ],
        urgency="medium"
    )
)

next_obs, reward, done, info = env.step(action)
```

---

## 🧪 Testing & Validation

### Run Environment Tests

```bash
# Test basic functionality
python -c "
from environment import SchoolOperationsEnv
from models import DifficultyLevel

env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY)
obs = env.reset()
print('✓ Environment initialized')
print(f'✓ Task: {obs.task_type.value}')
print(f'✓ Difficulty: {obs.difficulty.value}')
"
```

### Validate OpenEnv Spec

```bash
# Install validator
pip install openenv

# Validate YAML manifest
openenv validate openenv.yaml

# Output should show: ✓ Valid OpenEnv manifest
```

### Run Baseline

```bash
# Requires HF_TOKEN or OPENAI_API_KEY
export HF_TOKEN="sk-..."
python baseline_inference.py

# Check results
cat baseline_results.json
```

---

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t school-operations-env:latest .
```

### Run Container

```bash
# Interactive mode
docker run -it \
  -e HF_TOKEN="your-api-key" \
  school-operations-env:latest \
  python baseline_inference.py

# Or mount local directory
docker run -it \
  -v $(pwd):/app \
  -e HF_TOKEN="your-api-key" \
  school-operations-env:latest \
  python baseline_inference.py
```

---

## 🌐 Hugging Face Spaces Deployment

### Deploy Steps

1. **Create Space** on Hugging Face
   - Go to [huggingface.co/new-space](https://huggingface.co/new-space)
   - Select "Docker" runtime
   - Add tags: `openenv`, `benchmark`, `school-operations`

2. **Push Repository**
   ```bash
   git remote add hf https://huggingface.co/spaces/username/school-operations-env
   git push hf main
   ```

3. **Configure Secrets**
   - Add `HF_TOKEN` in Space secrets for API access

4. **Access Space**
   - Environment will be available at `huggingface.co/spaces/username/school-operations-env`

---

## 📋 Reproducibility

### Seeding

All randomness is controlled by seed parameter:

```python
# Identical sequence across runs
env1 = SchoolOperationsEnv(seed=42)
env2 = SchoolOperationsEnv(seed=42)

obs1 = env1.reset()
obs2 = env2.reset()

assert obs1.email_data == obs2.email_data  # True
```

### Baseline Reproducibility

```bash
# Always produces same scores
python baseline_inference.py --seed 42 --num_episodes 10
# → Overall Average: 0.881
```

---

## 📊 Evaluation Metrics

### Per-Task Metrics

| Task | Metric | Definition |
|------|--------|-----------|
| Email Classification | Accuracy | % correct classifications |
| Timetable Scheduling | Constraint Satisfaction | % of constraints met |
| Student Support | Composite Score | Weighted: keyword (25%) + correctness (40%) + tone (25%) + action items (10%) |

### Episode Metrics

| Metric | Definition |
|--------|-----------|
| Episode Reward | Sum of step rewards |
| Steps to Completion | Number of steps until terminal state |
| Success Rate | % of episodes reaching score ≥ 0.8 |

---

## 🔍 Troubleshooting

### API Key Issues

```bash
# Error: "API key not found"
# Solution: Set environment variable
export HF_TOKEN="your-openai-api-key"
# Or
export OPENAI_API_KEY="your-openai-api-key"
```

### Validation Errors

```bash
# Error: "Invalid action for task type"
# Solution: Ensure action task_type matches observation task_type
observation.task_type  # EMAIL_CLASSIFICATION
action.task_type       # Must be EMAIL_CLASSIFICATION
```

### Docker Build Issues

```bash
# Error: "packages not found"
# Solution: Ensure requirements.txt is in same directory
ls -la requirements.txt
docker build -t school-operations-env:latest .
```

---

## 📝 Citation

If you use this environment in your research, please cite:

```bibtex
@misc{school-operations-env,
  title={AI-Powered School Operations Evaluation Environment},
  author={Raccoon AI Hackathon},
  year={2024},
  howpublished={\url{https://huggingface.co/spaces/raccoon-ai/school-operations-env}}
}
```

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-task`
3. Add tests for new functionality
4. Submit pull request with description

---

## 📞 Support

- **Issues:** Report bugs on GitHub
- **Documentation:** See [README.md](README.md)
- **Baseline Help:** Check [baseline_inference.py](baseline_inference.py) examples

---

## 🎯 Future Enhancements

- [ ] Additional task domains (code review, data cleaning)
- [ ] Multi-agent coordination scenarios
- [ ] Adversarial task variants
- [ ] Real dataset integration with FERPA compliance
- [ ] Web interface for interactive evaluation

---

**OpenEnv-Compliant ✓** | **Production-Ready ✓** | **Fully Documented ✓**
