"""
Pydantic models for OpenEnv compliance.
Defines typed Observation, Action, and Reward structures.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Any
from enum import Enum


class TaskType(str, Enum):
    """Available task types in the environment."""
    EMAIL_CLASSIFICATION = "email_classification"
    TIMETABLE_SCHEDULING = "timetable_scheduling"
    STUDENT_SUPPORT = "student_support"


class DifficultyLevel(str, Enum):
    """Difficulty levels for tasks."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# ============= OBSERVATION MODELS =============

class EmailData(BaseModel):
    """Email to be classified."""
    subject: str = Field(..., description="Email subject line")
    body: str = Field(..., description="Email body content")
    sender: str = Field(..., description="Sender's email or name")


class ScheduleConstraint(BaseModel):
    """Constraint for timetable scheduling."""
    class_name: str = Field(..., description="Class identifier")
    teacher: str = Field(..., description="Teacher name")
    duration_minutes: int = Field(..., description="Class duration in minutes")
    students: List[str] = Field(..., description="List of student names")
    preferred_times: Optional[List[str]] = Field(
        default=None, description="Preferred time slots (HH:MM format)"
    )


class StudentQuery(BaseModel):
    """Student query for support response."""
    student_name: str = Field(..., description="Name of the student")
    issue_type: str = Field(..., description="Type of issue (e.g., academic, behavioral, health)")
    query: str = Field(..., description="Detailed query/concern")
    context: Optional[str] = Field(default=None, description="Additional context")


class Observation(BaseModel):
    """OpenEnv Observation structure."""
    task_type: TaskType = Field(..., description="Type of task")
    difficulty: DifficultyLevel = Field(..., description="Task difficulty level")
    step_number: int = Field(..., description="Current step number in episode")
    max_steps: int = Field(..., description="Maximum steps allowed")
    
    # Task-specific data
    email_data: Optional[EmailData] = Field(default=None)
    schedule_constraints: Optional[List[ScheduleConstraint]] = Field(default=None)
    student_query: Optional[StudentQuery] = Field(default=None)
    
    # Metadata
    timestamp: str = Field(..., description="ISO timestamp")
    episode_id: str = Field(..., description="Unique episode identifier")


# ============= ACTION MODELS =============

class EmailAction(BaseModel):
    """Action for email classification task."""
    category: Literal[
        "admission",
        "academic",
        "behavioral",
        "health",
        "extracurricular",
        "other"
    ] = Field(..., description="Email category classification")


class ScheduleSlot(BaseModel):
    """A single time slot in the schedule."""
    class_name: str = Field(..., description="Class identifier")
    day: Literal["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] = Field(
        ..., description="Day of week"
    )
    start_time: str = Field(..., description="Start time (HH:MM format)")
    end_time: str = Field(..., description="End time (HH:MM format)")
    location: str = Field(..., description="Room/location identifier")


class ScheduleAction(BaseModel):
    """Action for timetable scheduling task."""
    schedule: List[ScheduleSlot] = Field(
        ..., description="List of scheduled time slots"
    )


class SupportResponse(BaseModel):
    """Action for student support response task."""
    response: str = Field(..., description="Support response to the student")
    action_items: List[str] = Field(
        default=[], description="Follow-up actions or recommendations"
    )
    urgency: Literal["low", "medium", "high"] = Field(
        default="medium", description="Urgency level of response"
    )


class Action(BaseModel):
    """OpenEnv Action structure - can be one of multiple task actions."""
    task_type: TaskType = Field(..., description="Type of task")
    
    # Task-specific actions
    email_action: Optional[EmailAction] = Field(default=None)
    schedule_action: Optional[ScheduleAction] = Field(default=None)
    support_action: Optional[SupportResponse] = Field(default=None)


# ============= REWARD MODELS =============

class RewardBreakdown(BaseModel):
    """Detailed breakdown of reward components."""
    task_score: float = Field(..., ge=0.0, le=1.0, description="Main task score")
    efficiency_bonus: float = Field(..., ge=-0.1, le=0.1, description="Efficiency bonus/penalty")
    partial_credit: float = Field(..., ge=0.0, le=0.2, description="Partial credit for partial progress")
    penalty: float = Field(..., ge=-1.0, le=0.0, description="Penalties for violations")


class Reward(BaseModel):
    """OpenEnv Reward structure."""
    total_reward: float = Field(..., ge=-1.0, le=1.0, description="Total reward value")
    breakdown: RewardBreakdown = Field(..., description="Detailed reward breakdown")
    feedback: str = Field(..., description="Human-readable feedback")
    is_terminal: bool = Field(..., description="Whether episode is complete")


# ============= STATE MODELS =============

class TaskState(BaseModel):
    """Current state of a task."""
    task_type: TaskType
    difficulty: DifficultyLevel
    is_completed: bool
    cumulative_reward: float
    steps_taken: int
    max_steps: int


class EnvironmentState(BaseModel):
    """Complete environment state."""
    episode_id: str
    episode_number: int
    current_task: TaskState
    all_task_scores: Dict[str, float] = Field(
        default_factory=dict, description="Scores for all completed tasks"
    )
    total_episodes: int
    timestamp: str
