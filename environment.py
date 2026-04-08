"""
Main OpenEnv-compliant School Operations Environment.
Implements step(), reset(), state() and full OpenEnv interface.
"""

import random
import uuid
from datetime import datetime
from typing import Tuple, Dict, Any, Optional, List
import json

from models import (
    Observation, Action, Reward, RewardBreakdown, TaskState, EnvironmentState,
    TaskType, DifficultyLevel, EmailData, ScheduleConstraint, StudentQuery,
    EmailAction, ScheduleAction, SupportResponse
)
from graders import EmailGrader, ScheduleGrader, StudentSupportGrader


class SchoolOperationsEnv:
    """
    OpenEnv-compliant School Operations Evaluation Environment.
    
    Provides three tasks of increasing difficulty:
    1. Email Classification (Easy)
    2. Timetable Scheduling (Medium)
    3. Student Support Response (Hard)
    """
    
    # Task datasets
    EMAIL_SAMPLES = [
        {
            "subject": "New student enrollment",
            "body": "Hello, we have a new student joining us next semester. Please process the admission.",
            "sender": "admin@school.edu"
        },
        {
            "subject": "Midterm exam results",
            "body": "The midterm exam scores are now available. Please check your grades in the student portal.",
            "sender": "academics@school.edu"
        },
        {
            "subject": "Student behavior incident",
            "body": "A student was involved in a behavioral incident today during lunch. Please advise.",
            "sender": "principal@school.edu"
        },
        {
            "subject": "Health office - flu outbreak",
            "body": "We have several students with flu symptoms in the health office. Isolation protocols activated.",
            "sender": "nurse@school.edu"
        },
        {
            "subject": "Basketball tournament this weekend",
            "body": "Reminder: Basketball team competition is scheduled for Saturday. Practice Friday afternoon.",
            "sender": "sports@school.edu"
        },
    ]
    
    TEACHERS = ["Ms. Smith", "Mr. Johnson", "Dr. Patel", "Ms. Garcia", "Mr. Lee"]
    STUDENTS = [
        "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
        "Iris", "Jack", "Kate", "Liam"
    ]
    ROOMS = ["101", "102", "103", "104", "105", "Lab", "Gym", "Library"]
    
    STUDENT_QUERIES = [
        {
            "student_name": "Alice",
            "issue_type": "academic",
            "query": "I'm struggling with calculus and my grades are dropping. What resources are available?",
            "context": "Takes honors math class"
        },
        {
            "student_name": "Bob",
            "issue_type": "behavioral",
            "query": "I was involved in a conflict with a classmate. How do we resolve this?",
            "context": "First incident"
        },
        {
            "student_name": "Charlie",
            "issue_type": "health",
            "query": "I've been having frequent headaches and can't concentrate in class.",
            "context": "New symptom, no prior health concerns"
        },
        {
            "student_name": "Diana",
            "issue_type": "personal",
            "query": "I'm feeling overwhelmed with school and home pressure. Can someone help?",
            "context": "Recent family change"
        },
    ]
    
    def __init__(self, difficulty: DifficultyLevel = DifficultyLevel.EASY, seed: int = 42):
        """Initialize the environment."""
        self.difficulty = difficulty
        self.seed = seed
        random.seed(seed)
        
        self.episode_id = str(uuid.uuid4())
        self.episode_number = 0
        self.current_task: Optional[TaskState] = None
        self.all_task_scores: Dict[str, float] = {}
        self.step_count = 0
        self.max_steps = self._get_max_steps(difficulty)
        
        self.current_observation: Optional[Observation] = None
        self.cumulative_reward = 0.0
        
    def _get_max_steps(self, difficulty: DifficultyLevel) -> int:
        """Get maximum steps based on difficulty."""
        mapping = {
            DifficultyLevel.EASY: 5,
            DifficultyLevel.MEDIUM: 10,
            DifficultyLevel.HARD: 15,
        }
        return mapping.get(difficulty, 10)
    
    def _select_task_for_difficulty(self) -> TaskType:
        """Select a task based on difficulty level."""
        if self.difficulty == DifficultyLevel.EASY:
            return TaskType.EMAIL_CLASSIFICATION
        elif self.difficulty == DifficultyLevel.MEDIUM:
            return TaskType.TIMETABLE_SCHEDULING
        else:
            return TaskType.STUDENT_SUPPORT
    
    def _generate_email_observation(self) -> Tuple[Observation, EmailData]:
        """Generate an email classification task."""
        email_dict = random.choice(self.EMAIL_SAMPLES)
        email = EmailData(**email_dict)
        
        obs = Observation(
            task_type=TaskType.EMAIL_CLASSIFICATION,
            difficulty=self.difficulty,
            step_number=self.step_count,
            max_steps=self.max_steps,
            email_data=email,
            timestamp=datetime.now().isoformat(),
            episode_id=self.episode_id,
        )
        return obs, email
    
    def _generate_schedule_observation(self) -> Tuple[Observation, List[ScheduleConstraint]]:
        """Generate a timetable scheduling task."""
        num_classes = 3 + (2 if self.difficulty == DifficultyLevel.HARD else 0)
        constraints = []
        
        for i in range(num_classes):
            teacher = random.choice(self.TEACHERS)
            num_students = min(len(self.STUDENTS), random.randint(15, 25))
            students = random.sample(self.STUDENTS, num_students)
            duration = random.choice([45, 60, 90])
            
            constraint = ScheduleConstraint(
                class_name=f"Class_{chr(65+i)}",
                teacher=teacher,
                duration_minutes=duration,
                students=students,
                preferred_times=["09:00", "10:00", "13:00"] if random.random() > 0.3 else None,
            )
            constraints.append(constraint)
        
        obs = Observation(
            task_type=TaskType.TIMETABLE_SCHEDULING,
            difficulty=self.difficulty,
            step_number=self.step_count,
            max_steps=self.max_steps,
            schedule_constraints=constraints,
            timestamp=datetime.now().isoformat(),
            episode_id=self.episode_id,
        )
        return obs, constraints
    
    def _generate_student_query_observation(self) -> Tuple[Observation, StudentQuery]:
        """Generate a student support response task."""
        query_dict = random.choice(self.STUDENT_QUERIES)
        query = StudentQuery(**query_dict)
        
        obs = Observation(
            task_type=TaskType.STUDENT_SUPPORT,
            difficulty=self.difficulty,
            step_number=self.step_count,
            max_steps=self.max_steps,
            student_query=query,
            timestamp=datetime.now().isoformat(),
            episode_id=self.episode_id,
        )
        return obs, query
    
    def reset(self) -> Observation:
        """
        Reset the environment and return initial observation.
        OpenEnv spec: reset() → initial_observation
        """
        self.episode_number += 1
        self.episode_id = str(uuid.uuid4())
        self.step_count = 0
        self.cumulative_reward = 0.0
        
        task_type = self._select_task_for_difficulty()
        
        if task_type == TaskType.EMAIL_CLASSIFICATION:
            self.current_observation, self.current_email = self._generate_email_observation()
        elif task_type == TaskType.TIMETABLE_SCHEDULING:
            self.current_observation, self.current_constraints = self._generate_schedule_observation()
        else:
            self.current_observation, self.current_query = self._generate_student_query_observation()
        
        self.current_task = TaskState(
            task_type=task_type,
            difficulty=self.difficulty,
            is_completed=False,
            cumulative_reward=0.0,
            steps_taken=0,
            max_steps=self.max_steps,
        )
        
        return self.current_observation
    
    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Execute one step of the environment.
        OpenEnv spec: step(action) → (observation, reward, done, info)
        
        Args:
            action: Action to execute
            
        Returns:
            observation: New observation
            reward: Reward object with score and breakdown
            done: Whether episode is complete
            info: Additional information
        """
        self.step_count += 1
        self.current_task.steps_taken += 1
        
        # Grade the action
        task_score = 0.0
        grader_feedback = ""
        breakdown = {}
        
        if self.current_observation.task_type == TaskType.EMAIL_CLASSIFICATION:
            if action.email_action is None:
                task_score = 0.0
                grader_feedback = "No email action provided"
            else:
                task_score, grader_feedback = EmailGrader.grade(
                    self.current_email, action.email_action
                )
                breakdown = {"email_classification": task_score}
        
        elif self.current_observation.task_type == TaskType.TIMETABLE_SCHEDULING:
            if action.schedule_action is None:
                task_score = 0.0
                grader_feedback = "No schedule action provided"
            else:
                task_score, grader_feedback, breakdown = ScheduleGrader.grade(
                    self.current_constraints, action.schedule_action
                )
        
        elif self.current_observation.task_type == TaskType.STUDENT_SUPPORT:
            if action.support_action is None:
                task_score = 0.0
                grader_feedback = "No support action provided"
            else:
                task_score, grader_feedback, breakdown = StudentSupportGrader.grade(
                    self.current_query, action.support_action
                )
        
        # Calculate reward with partial progress signals
        efficiency_bonus = self._calculate_efficiency_bonus()
        partial_credit = self._calculate_partial_credit(task_score)
        penalty = self._calculate_penalty()
        
        total_reward = task_score + efficiency_bonus + partial_credit + penalty
        total_reward = max(-1.0, min(1.0, total_reward))  # Clamp to [-1, 1]
        
        reward_breakdown = RewardBreakdown(
            task_score=task_score,
            efficiency_bonus=efficiency_bonus,
            partial_credit=partial_credit,
            penalty=penalty,
        )
        
        reward = Reward(
            total_reward=total_reward,
            breakdown=reward_breakdown,
            feedback=grader_feedback,
            is_terminal=False,
        )
        
        self.cumulative_reward += total_reward
        self.current_task.cumulative_reward = self.cumulative_reward
        
        # Check if episode is done
        done = (self.step_count >= self.max_steps) or (task_score >= 0.8)
        
        if done:
            reward.is_terminal = True
            self.all_task_scores[self.current_observation.task_type.value] = task_score
        
        # Generate next observation (same task or new one)
        if done:
            next_obs = self.reset()
        else:
            # Slight variation in same task for next step
            next_obs = self.current_observation
            next_obs.step_number = self.step_count
        
        info = {
            "episode_id": self.episode_id,
            "episode_number": self.episode_number,
            "task_type": self.current_observation.task_type.value,
            "difficulty": self.difficulty.value,
            "step": self.step_count,
            "max_steps": self.max_steps,
            "grader_feedback": grader_feedback,
            "breakdown": breakdown,
            "cumulative_reward": self.cumulative_reward,
        }
        
        return next_obs, reward, done, info
    
    def state(self) -> EnvironmentState:
        """
        Return the current state of the environment.
        OpenEnv spec: state() → current_state
        """
        if self.current_task is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        
        return EnvironmentState(
            episode_id=self.episode_id,
            episode_number=self.episode_number,
            current_task=self.current_task,
            all_task_scores=self.all_task_scores,
            total_episodes=self.episode_number,
            timestamp=datetime.now().isoformat(),
        )
    
    def _calculate_efficiency_bonus(self) -> float:
        """Bonus for solving quickly (encourages efficiency)."""
        if self.step_count <= 2:
            return 0.1
        elif self.step_count <= 5:
            return 0.05
        return 0.0
    
    def _calculate_partial_credit(self, task_score: float) -> float:
        """Partial credit for partial progress toward solution."""
        if 0.5 <= task_score < 0.8:
            return 0.1
        elif 0.3 <= task_score < 0.5:
            return 0.05
        return 0.0
    
    def _calculate_penalty(self) -> float:
        """Penalties for undesirable behaviors."""
        # Penalty for taking too many steps
        if self.step_count > self.max_steps * 0.8:
            return -0.05
        
        # Penalty for infinite loops (stepping without progress)
        # This would be tracked in real implementation
        return 0.0
    
    def get_observation_spec(self) -> Dict[str, Any]:
        """Return specification of observation space."""
        return {
            "task_type": "TaskType enum (email_classification, timetable_scheduling, student_support)",
            "difficulty": "DifficultyLevel enum (easy, medium, hard)",
            "step_number": "int (current step in episode)",
            "max_steps": "int (maximum steps allowed)",
            "email_data": "EmailData | None (for email task)",
            "schedule_constraints": "List[ScheduleConstraint] | None (for scheduling task)",
            "student_query": "StudentQuery | None (for support task)",
            "timestamp": "ISO timestamp string",
            "episode_id": "Unique episode identifier",
        }
    
    def get_action_spec(self) -> Dict[str, Any]:
        """Return specification of action space."""
        return {
            "task_type": "TaskType enum (must match observation task_type)",
            "email_action": "EmailAction | None (for email task)",
            "schedule_action": "ScheduleAction | None (for scheduling task)",
            "support_action": "SupportResponse | None (for support task)",
        }
    
    def get_reward_spec(self) -> Dict[str, Any]:
        """Return specification of reward space."""
        return {
            "total_reward": "float in [-1.0, 1.0]",
            "breakdown": {
                "task_score": "float in [0.0, 1.0]",
                "efficiency_bonus": "float in [-0.1, 0.1]",
                "partial_credit": "float in [0.0, 0.2]",
                "penalty": "float in [-1.0, 0.0]",
            },
            "feedback": "Human-readable feedback string",
            "is_terminal": "bool indicating episode completion",
        }
