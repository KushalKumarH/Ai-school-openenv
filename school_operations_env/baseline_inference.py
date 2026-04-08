"""
Baseline inference script for School Operations Environment.

Uses OpenAI API (GPT-4) to evaluate the environment.
Reads API key from HF_TOKEN environment variable.
Produces reproducible baseline scores across all tasks.

Usage:
    export HF_TOKEN="your-openai-api-key"
    python baseline_inference.py
"""

import os
import json
import random
from typing import Dict, Tuple
from dotenv import load_dotenv
from openai import OpenAI

from environment import SchoolOperationsEnv
from models import (
    DifficultyLevel, Action, TaskType, EmailAction, ScheduleAction, 
    ScheduleSlot, SupportResponse
)


class BaselineAgent:
    """Baseline agent using OpenAI API for inference."""
    
    def __init__(self, model: str = "gpt-4", api_key: str = None):
        """
        Initialize baseline agent.
        
        Args:
            model: OpenAI model to use (gpt-4, gpt-3.5-turbo, etc.)
            api_key: OpenAI API key (uses HF_TOKEN env var if not provided)
        """
        if api_key is None:
            api_key = os.getenv("HF_TOKEN") or os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(
                "API key not found. Set HF_TOKEN or OPENAI_API_KEY environment variable."
            )
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.inference_count = 0
    
    def classify_email(self, subject: str, body: str, sender: str) -> str:
        """Use LLM to classify email."""
        prompt = f"""You are an email classification system for a school.
        
Classify this email into ONE of these categories:
- admission: about student admission, enrollment, applications
- academic: about grades, homework, assignments, exams, courses
- behavioral: about student behavior, discipline, incidents
- health: about health, medical, illness, medication, wellness
- extracurricular: about clubs, sports, events, competitions
- other: doesn't fit above categories

Email:
Subject: {subject}
From: {sender}
Body: {body}

Respond with ONLY the category name (e.g., "academic")."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )
        
        self.inference_count += 1
        category = response.content[0].text.strip().lower()
        
        # Validate category
        valid_categories = ["admission", "academic", "behavioral", "health", "extracurricular", "other"]
        if category not in valid_categories:
            category = "other"
        
        return category
    
    def schedule_classes(self, constraints_text: str) -> list:
        """Use LLM to generate schedule."""
        prompt = f"""You are a school timetable scheduling system.

Given these constraints, create a schedule for the week (Monday-Friday, 9:00-15:00).

{constraints_text}

Output a JSON array of schedule slots with this format:
[
  {{
    "class_name": "Class_A",
    "day": "Monday",
    "start_time": "09:00",
    "end_time": "10:00",
    "location": "101"
  }},
  ...
]

Requirements:
- No time clashes in the same location
- Each class's total duration must match the constraint
- Try to use preferred times when available
- Distribute classes across different rooms and times

Respond with ONLY valid JSON array, no explanation."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        self.inference_count += 1
        
        try:
            # Extract JSON from response
            response_text = response.content[0].text.strip()
            # Try to parse JSON
            schedule = json.loads(response_text)
            return schedule
        except json.JSONDecodeError:
            # Fallback: return empty schedule
            return []
    
    def generate_support_response(
        self, student_name: str, issue_type: str, query: str, context: str = None
    ) -> Tuple[str, list, str]:
        """Use LLM to generate student support response."""
        context_text = f"Context: {context}" if context else ""
        
        prompt = f"""You are a school counselor/administrator providing support to a student.

Student Name: {student_name}
Issue Type: {issue_type}
Query: {query}
{context_text}

Provide a supportive, appropriate response that:
1. Acknowledges the student's concern
2. Shows understanding and empathy
3. Provides concrete next steps or resources
4. Maintains a professional, supportive tone

Additionally, suggest 2-3 action items (specific follow-up actions).

Format your response as JSON:
{{
  "response": "Your support message here...",
  "action_items": ["Action 1", "Action 2", "Action 3"],
  "urgency": "low|medium|high"
}}

Respond with ONLY valid JSON, no explanation."""
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        self.inference_count += 1
        
        try:
            response_text = response.content[0].text.strip()
            data = json.loads(response_text)
            return (
                data.get("response", ""),
                data.get("action_items", []),
                data.get("urgency", "medium")
            )
        except (json.JSONDecodeError, KeyError):
            return ("Unable to process request.", [], "medium")
    
    def generate_action(self, observation) -> Action:
        """Generate action based on observation."""
        if observation.task_type == TaskType.EMAIL_CLASSIFICATION:
            category = self.classify_email(
                observation.email_data.subject,
                observation.email_data.body,
                observation.email_data.sender,
            )
            return Action(
                task_type=TaskType.EMAIL_CLASSIFICATION,
                email_action=EmailAction(category=category)
            )
        
        elif observation.task_type == TaskType.TIMETABLE_SCHEDULING:
            # Format constraints for LLM
            constraints_text = "Constraints:\n"
            for c in observation.schedule_constraints:
                constraints_text += f"- {c.class_name}: {c.duration_minutes} min, Teacher: {c.teacher}, "
                constraints_text += f"Students: {len(c.students)}, "
                if c.preferred_times:
                    constraints_text += f"Preferred: {', '.join(c.preferred_times)}\n"
                else:
                    constraints_text += "Any time\n"
            
            schedule_json = self.schedule_classes(constraints_text)
            slots = []
            
            for slot_dict in schedule_json:
                try:
                    slot = ScheduleSlot(
                        class_name=slot_dict.get("class_name", ""),
                        day=slot_dict.get("day", "Monday"),
                        start_time=slot_dict.get("start_time", "09:00"),
                        end_time=slot_dict.get("end_time", "10:00"),
                        location=slot_dict.get("location", "101"),
                    )
                    slots.append(slot)
                except Exception:
                    continue
            
            return Action(
                task_type=TaskType.TIMETABLE_SCHEDULING,
                schedule_action=ScheduleAction(schedule=slots)
            )
        
        elif observation.task_type == TaskType.STUDENT_SUPPORT:
            response, action_items, urgency = self.generate_support_response(
                observation.student_query.student_name,
                observation.student_query.issue_type,
                observation.student_query.query,
                observation.student_query.context,
            )
            return Action(
                task_type=TaskType.STUDENT_SUPPORT,
                support_action=SupportResponse(
                    response=response,
                    action_items=action_items,
                    urgency=urgency,
                )
            )


def run_baseline_evaluation(
    num_episodes: int = 3,
    seed: int = 42,
    model: str = "gpt-4",
    save_results: bool = True,
) -> Dict:
    """
    Run baseline evaluation across all difficulty levels.
    
    Args:
        num_episodes: Number of episodes per difficulty level
        seed: Random seed for reproducibility
        model: OpenAI model to use
        save_results: Whether to save results to JSON
        
    Returns:
        Dictionary with evaluation results
    """
    print(f"Starting Baseline Evaluation")
    print(f"Model: {model}")
    print(f"Episodes per difficulty: {num_episodes}")
    print(f"Seed: {seed}\n")
    
    # Initialize agent
    try:
        agent = BaselineAgent(model=model)
    except ValueError as e:
        print(f"Error: {e}")
        return {}
    
    results = {
        "model": model,
        "num_episodes": num_episodes,
        "seed": seed,
        "difficulties": {}
    }
    
    # Run evaluation for each difficulty level
    for difficulty in [DifficultyLevel.EASY, DifficultyLevel.MEDIUM, DifficultyLevel.HARD]:
        print(f"\n{'='*60}")
        print(f"Difficulty: {difficulty.value.upper()}")
        print(f"{'='*60}")
        
        env = SchoolOperationsEnv(difficulty=difficulty, seed=seed)
        scores = []
        
        for episode in range(num_episodes):
            obs = env.reset()
            cumulative_reward = 0.0
            steps = 0
            
            print(f"\nEpisode {episode + 1}/{num_episodes}")
            print(f"Task: {obs.task_type.value}")
            
            # Run episode
            max_episode_steps = 3  # Allow a few steps
            while steps < max_episode_steps:
                try:
                    action = agent.generate_action(obs)
                    obs, reward, done, info = env.step(action)
                    
                    cumulative_reward += reward.total_reward
                    steps += 1
                    
                    print(f"  Step {steps}: Reward={reward.total_reward:.3f}, "
                          f"Cumulative={cumulative_reward:.3f}")
                    print(f"  Feedback: {reward.feedback}")
                    
                    if done:
                        break
                
                except Exception as e:
                    print(f"  Error in step: {str(e)}")
                    break
            
            state = env.state()
            task_score = state.current_task.cumulative_reward
            scores.append(task_score)
            
            print(f"Episode Score: {task_score:.3f}")
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        results["difficulties"][difficulty.value] = {
            "scores": scores,
            "average": avg_score,
            "min": min(scores) if scores else 0.0,
            "max": max(scores) if scores else 0.0,
            "std_dev": (sum((x - avg_score) ** 2 for x in scores) / len(scores)) ** 0.5 if scores else 0.0,
        }
        
        print(f"\nDifficulty Summary: {difficulty.value}")
        print(f"  Average Score: {avg_score:.3f}")
        print(f"  Min Score: {min(scores) if scores else 0.0:.3f}")
        print(f"  Max Score: {max(scores) if scores else 0.0:.3f}")
    
    # Calculate overall statistics
    all_scores = []
    for diff_results in results["difficulties"].values():
        all_scores.extend(diff_results["scores"])
    
    if all_scores:
        results["overall"] = {
            "average_score": sum(all_scores) / len(all_scores),
            "min_score": min(all_scores),
            "max_score": max(all_scores),
            "total_inferences": agent.inference_count,
        }
    
    # Save results
    if save_results:
        results_file = "baseline_results.json"
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {results_file}")
    
    print(f"\n{'='*60}")
    print("BASELINE EVALUATION COMPLETE")
    print(f"{'='*60}")
    print(f"Total API Calls: {agent.inference_count}")
    if "overall" in results:
        print(f"Overall Average Score: {results['overall']['average_score']:.3f}")
    
    return results


if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    
    # Run baseline evaluation
    # Modify parameters as needed
    results = run_baseline_evaluation(
        num_episodes=2,  # Reduced for quick testing
        seed=42,
        model="gpt-4",
        save_results=True,
    )
