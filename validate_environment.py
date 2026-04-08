"""
Validation script for OpenEnv compliance and environment functionality.
Performs comprehensive checks before deployment.
"""

import json
import yaml
import sys
from pathlib import Path
from typing import List, Tuple

from environment import SchoolOperationsEnv
from models import (
    DifficultyLevel, TaskType, Action, EmailAction, 
    ScheduleAction, ScheduleSlot, SupportResponse, Observation, Reward
)


class EnvironmentValidator:
    """Validates OpenEnv compliance and functionality."""
    
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0
    
    def add_check(self, name: str, passed: bool, details: str = ""):
        """Record a validation check."""
        status = "✓ PASS" if passed else "✗ FAIL"
        self.checks.append((name, passed, details))
        
        if passed:
            self.passed += 1
            print(f"{status}: {name}")
        else:
            self.failed += 1
            print(f"{status}: {name}")
            if details:
                print(f"       {details}")
    
    def validate_pydantic_models(self):
        """Check Pydantic model compliance."""
        print("\n[1/5] Validating Pydantic Models...")
        
        try:
            # Test Observation
            from models import EmailData, Observation
            email = EmailData(
                subject="Test", 
                body="Test body", 
                sender="test@school.edu"
            )
            obs = Observation(
                task_type=TaskType.EMAIL_CLASSIFICATION,
                difficulty=DifficultyLevel.EASY,
                step_number=0,
                max_steps=5,
                email_data=email,
                timestamp="2024-01-01T00:00:00",
                episode_id="test-episode"
            )
            self.add_check("Observation model creation", True)
        except Exception as e:
            self.add_check("Observation model creation", False, str(e))
        
        try:
            # Test Action
            action = Action(
                task_type=TaskType.EMAIL_CLASSIFICATION,
                email_action=EmailAction(category="academic")
            )
            self.add_check("Action model creation", True)
        except Exception as e:
            self.add_check("Action model creation", False, str(e))
        
        try:
            # Test Reward
            from models import RewardBreakdown, Reward
            breakdown = RewardBreakdown(
                task_score=0.8,
                efficiency_bonus=0.05,
                partial_credit=0.0,
                penalty=0.0
            )
            reward = Reward(
                total_reward=0.85,
                breakdown=breakdown,
                feedback="Good job",
                is_terminal=False
            )
            self.add_check("Reward model creation", True)
        except Exception as e:
            self.add_check("Reward model creation", False, str(e))
    
    def validate_environment_interface(self):
        """Check environment interface compliance."""
        print("\n[2/5] Validating Environment Interface...")
        
        try:
            env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
            self.add_check("Environment instantiation", True)
        except Exception as e:
            self.add_check("Environment instantiation", False, str(e))
            return
        
        try:
            # Test reset()
            obs = env.reset()
            assert isinstance(obs, Observation)
            self.add_check("reset() method", True)
        except Exception as e:
            self.add_check("reset() method", False, str(e))
            return
        
        try:
            # Test step()
            action = Action(
                task_type=TaskType.EMAIL_CLASSIFICATION,
                email_action=EmailAction(category="academic")
            )
            next_obs, reward, done, info = env.step(action)
            assert isinstance(next_obs, Observation)
            assert isinstance(reward, Reward)
            assert isinstance(done, bool)
            assert isinstance(info, dict)
            self.add_check("step() method", True)
        except Exception as e:
            self.add_check("step() method", False, str(e))
        
        try:
            # Test state()
            state = env.state()
            assert hasattr(state, 'episode_id')
            assert hasattr(state, 'current_task')
            self.add_check("state() method", True)
        except Exception as e:
            self.add_check("state() method", False, str(e))
    
    def validate_tasks(self):
        """Validate all three tasks."""
        print("\n[3/5] Validating Tasks...")
        
        tasks_to_test = [
            (DifficultyLevel.EASY, TaskType.EMAIL_CLASSIFICATION, "Email Classification"),
            (DifficultyLevel.MEDIUM, TaskType.TIMETABLE_SCHEDULING, "Timetable Scheduling"),
            (DifficultyLevel.HARD, TaskType.STUDENT_SUPPORT, "Student Support"),
        ]
        
        for difficulty, expected_task, name in tasks_to_test:
            try:
                env = SchoolOperationsEnv(difficulty=difficulty, seed=42)
                obs = env.reset()
                
                if obs.task_type == expected_task:
                    self.add_check(f"Task {name}", True)
                else:
                    self.add_check(
                        f"Task {name}", 
                        False, 
                        f"Expected {expected_task}, got {obs.task_type}"
                    )
            except Exception as e:
                self.add_check(f"Task {name}", False, str(e))
    
    def validate_graders(self):
        """Validate grading functionality."""
        print("\n[4/5] Validating Graders...")
        
        try:
            from graders import EmailGrader
            from models import EmailData, EmailAction
            
            email = EmailData(
                subject="Grade update",
                body="Your exam grade is posted",
                sender="teacher@school.edu"
            )
            action = EmailAction(category="academic")
            
            score, feedback = EmailGrader.grade(email, action)
            assert 0.0 <= score <= 1.0
            assert isinstance(feedback, str)
            self.add_check("Email grader", True, f"Score: {score}")
        except Exception as e:
            self.add_check("Email grader", False, str(e))
        
        try:
            from graders import ScheduleGrader
            from models import ScheduleConstraint, ScheduleAction, ScheduleSlot
            
            constraints = [
                ScheduleConstraint(
                    class_name="Class_A",
                    teacher="Ms. Smith",
                    duration_minutes=60,
                    students=["Alice", "Bob"],
                    preferred_times=None
                )
            ]
            action = ScheduleAction(schedule=[
                ScheduleSlot(
                    class_name="Class_A",
                    day="Monday",
                    start_time="09:00",
                    end_time="10:00",
                    location="101"
                )
            ])
            
            score, feedback, breakdown = ScheduleGrader.grade(constraints, action)
            assert 0.0 <= score <= 1.0
            self.add_check("Schedule grader", True, f"Score: {score}")
        except Exception as e:
            self.add_check("Schedule grader", False, str(e))
        
        try:
            from graders import StudentSupportGrader
            from models import StudentQuery, SupportResponse
            
            query = StudentQuery(
                student_name="Alice",
                issue_type="academic",
                query="Help with math",
                context=None
            )
            action = SupportResponse(
                response="I can help you with tutoring resources",
                action_items=["Schedule tutoring"],
                urgency="medium"
            )
            
            score, feedback, breakdown = StudentSupportGrader.grade(query, action)
            assert 0.0 <= score <= 1.0
            self.add_check("Support grader", True, f"Score: {score}")
        except Exception as e:
            self.add_check("Support grader", False, str(e))
    
    def validate_openenv_yaml(self):
        """Validate OpenEnv YAML manifest."""
        print("\n[5/5] Validating OpenEnv Manifest...")
        
        try:
            with open("openenv.yaml", "r") as f:
                manifest = yaml.safe_load(f)
            
            required_fields = [
                "name", "version", "openenv_version", "tasks",
                "observation_space", "action_space", "reward_space",
                "interface"
            ]
            
            missing = [f for f in required_fields if f not in manifest]
            
            if not missing:
                self.add_check("OpenEnv YAML structure", True)
            else:
                self.add_check(
                    "OpenEnv YAML structure", 
                    False, 
                    f"Missing fields: {', '.join(missing)}"
                )
            
            # Check tasks
            if "tasks" in manifest:
                num_tasks = len(manifest["tasks"])
                if num_tasks >= 3:
                    self.add_check("Minimum 3 tasks", True, f"Found {num_tasks} tasks")
                else:
                    self.add_check("Minimum 3 tasks", False, f"Found {num_tasks} tasks")
        
        except FileNotFoundError:
            self.add_check("OpenEnv YAML exists", False, "File not found")
        except Exception as e:
            self.add_check("OpenEnv YAML validation", False, str(e))
    
    def run_all_validations(self) -> bool:
        """Run all validation checks."""
        print("\n" + "="*60)
        print("OpenEnv Environment Validation")
        print("="*60)
        
        self.validate_pydantic_models()
        self.validate_environment_interface()
        self.validate_tasks()
        self.validate_graders()
        self.validate_openenv_yaml()
        
        print("\n" + "="*60)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("="*60)
        
        return self.failed == 0


def main():
    """Run validation and exit with appropriate code."""
    validator = EnvironmentValidator()
    success = validator.run_all_validations()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
