"""
Gradio app for interactive testing of the School Operations Environment.
Deployed on Hugging Face Spaces.
"""

import gradio as gr
import json
import os
from typing import Dict, Tuple, List
from datetime import datetime

from environment import SchoolOperationsEnv
from models import (
    DifficultyLevel, TaskType, Action, EmailAction, 
    ScheduleAction, ScheduleSlot, SupportResponse
)


class InteractiveEnvironmentDemo:
    """Interactive demo for the School Operations Environment."""
    
    def __init__(self):
        self.env = None
        self.current_observation = None
        self.episode_history = []
        
    def initialize_environment(self, difficulty: str) -> Tuple[str, str, str]:
        """Initialize environment with selected difficulty."""
        try:
            diff_level = DifficultyLevel[difficulty.upper()]
            self.env = SchoolOperationsEnv(difficulty=diff_level, seed=42)
            self.current_observation = self.env.reset()
            self.episode_history = []
            
            status = f"✓ Environment initialized (Difficulty: {difficulty.upper()})"
            task_info = f"**Task:** {self.current_observation.task_type.value}\n"
            task_info += f"**Episode:** {self.env.episode_number}\n"
            task_info += f"**Max Steps:** {self.current_observation.max_steps}"
            
            return status, task_info, self._get_current_task_display()
        except Exception as e:
            return f"✗ Error: {str(e)}", "", ""
    
    def _get_current_task_display(self) -> str:
        """Get display string for current task."""
        if self.current_observation is None:
            return "Initialize environment first"
        
        task_type = self.current_observation.task_type
        
        if task_type == TaskType.EMAIL_CLASSIFICATION:
            email = self.current_observation.email_data
            display = f"""
## 📧 Email Classification Task

**From:** {email.sender}
**Subject:** {email.subject}

**Body:**
{email.body}

---
**Action Required:** Select the appropriate category
            """
        
        elif task_type == TaskType.TIMETABLE_SCHEDULING:
            constraints = self.current_observation.schedule_constraints
            display = "## 📅 Timetable Scheduling Task\n\n**Constraints:**\n"
            for i, c in enumerate(constraints, 1):
                display += f"\n**Class {i}: {c.class_name}**\n"
                display += f"- Teacher: {c.teacher}\n"
                display += f"- Duration: {c.duration_minutes} minutes\n"
                display += f"- Students: {len(c.students)} students\n"
                if c.preferred_times:
                    display += f"- Preferred times: {', '.join(c.preferred_times)}\n"
            display += "\n---\n**Action Required:** Create a conflict-free schedule"
        
        elif task_type == TaskType.STUDENT_SUPPORT:
            query = self.current_observation.student_query
            display = f"""
## 💬 Student Support Response Task

**Student:** {query.student_name}
**Issue Type:** {query.issue_type}

**Query:**
{query.query}

"""
            if query.context:
                display += f"**Context:** {query.context}\n"
            
            display += "\n---\n**Action Required:** Generate a supportive response"
        
        return display
    
    def submit_email_action(self, category: str) -> Tuple[str, str, str, str]:
        """Submit email classification action."""
        if self.env is None or self.current_observation is None:
            return "Initialize environment first", "", "", ""
        
        try:
            action = Action(
                task_type=TaskType.EMAIL_CLASSIFICATION,
                email_action=EmailAction(category=category)
            )
            
            next_obs, reward, done, info = self.env.step(action)
            
            result = f"""
**Reward:** {reward.total_reward:.3f}
**Feedback:** {reward.feedback}

**Breakdown:**
- Task Score: {reward.breakdown.task_score:.3f}
- Efficiency Bonus: {reward.breakdown.efficiency_bonus:.3f}
- Partial Credit: {reward.breakdown.partial_credit:.3f}
- Penalty: {reward.breakdown.penalty:.3f}

**Episode Complete:** {done}
"""
            
            self.current_observation = next_obs
            self.episode_history.append({
                "step": len(self.episode_history) + 1,
                "action": f"Email category: {category}",
                "reward": reward.total_reward,
                "feedback": reward.feedback
            })
            
            return result, self._get_current_task_display(), self._get_history(), self._get_state()
        
        except Exception as e:
            return f"✗ Error: {str(e)}", "", "", ""
    
    def submit_schedule_action(self, schedule_json: str) -> Tuple[str, str, str, str]:
        """Submit timetable scheduling action."""
        if self.env is None or self.current_observation is None:
            return "Initialize environment first", "", "", ""
        
        try:
            schedule_data = json.loads(schedule_json)
            
            slots = []
            for slot_dict in schedule_data:
                slot = ScheduleSlot(
                    class_name=slot_dict["class_name"],
                    day=slot_dict["day"],
                    start_time=slot_dict["start_time"],
                    end_time=slot_dict["end_time"],
                    location=slot_dict["location"],
                )
                slots.append(slot)
            
            action = Action(
                task_type=TaskType.TIMETABLE_SCHEDULING,
                schedule_action=ScheduleAction(schedule=slots)
            )
            
            next_obs, reward, done, info = self.env.step(action)
            
            result = f"""
**Reward:** {reward.total_reward:.3f}
**Feedback:** {reward.feedback}

**Breakdown:**
- Task Score: {reward.breakdown.task_score:.3f}
- Efficiency Bonus: {reward.breakdown.efficiency_bonus:.3f}
- Partial Credit: {reward.breakdown.partial_credit:.3f}
- Penalty: {reward.breakdown.penalty:.3f}

**Episode Complete:** {done}
**Slots Scheduled:** {len(slots)}
"""
            
            self.current_observation = next_obs
            self.episode_history.append({
                "step": len(self.episode_history) + 1,
                "action": f"Schedule with {len(slots)} slots",
                "reward": reward.total_reward,
                "feedback": reward.feedback
            })
            
            return result, self._get_current_task_display(), self._get_history(), self._get_state()
        
        except json.JSONDecodeError as e:
            return f"✗ Invalid JSON: {str(e)}", "", "", ""
        except Exception as e:
            return f"✗ Error: {str(e)}", "", "", ""
    
    def submit_support_action(self, response: str, action_items: str, urgency: str) -> Tuple[str, str, str, str]:
        """Submit student support response action."""
        if self.env is None or self.current_observation is None:
            return "Initialize environment first", "", "", ""
        
        try:
            # Parse action items (comma-separated)
            items = [item.strip() for item in action_items.split(",") if item.strip()]
            
            action = Action(
                task_type=TaskType.STUDENT_SUPPORT,
                support_action=SupportResponse(
                    response=response,
                    action_items=items,
                    urgency=urgency,
                )
            )
            
            next_obs, reward, done, info = self.env.step(action)
            
            result = f"""
**Reward:** {reward.total_reward:.3f}
**Feedback:** {reward.feedback}

**Breakdown:**
- Task Score: {reward.breakdown.task_score:.3f}
- Efficiency Bonus: {reward.breakdown.efficiency_bonus:.3f}
- Partial Credit: {reward.breakdown.partial_credit:.3f}
- Penalty: {reward.breakdown.penalty:.3f}

**Episode Complete:** {done}
**Action Items:** {len(items)}
"""
            
            self.current_observation = next_obs
            self.episode_history.append({
                "step": len(self.episode_history) + 1,
                "action": f"Support response with {len(items)} action items",
                "reward": reward.total_reward,
                "feedback": reward.feedback
            })
            
            return result, self._get_current_task_display(), self._get_history(), self._get_state()
        
        except Exception as e:
            return f"✗ Error: {str(e)}", "", "", ""
    
    def _get_history(self) -> str:
        """Get episode history."""
        if not self.episode_history:
            return "No steps taken yet"
        
        history = "## Episode History\n\n"
        for entry in self.episode_history:
            history += f"**Step {entry['step']}:** {entry['action']}\n"
            history += f"- Reward: {entry['reward']:.3f}\n"
            history += f"- Feedback: {entry['feedback']}\n\n"
        
        return history
    
    def _get_state(self) -> str:
        """Get current environment state."""
        if self.env is None:
            return "Environment not initialized"
        
        state = self.env.state()
        
        info = f"""
## Current State

**Episode:** {state.episode_number}
**Episode ID:** {state.episode_id}

**Current Task:**
- Type: {state.current_task.task_type.value}
- Difficulty: {state.current_task.difficulty.value}
- Steps Taken: {state.current_task.steps_taken}/{state.current_task.max_steps}
- Cumulative Reward: {state.current_task.cumulative_reward:.3f}
- Completed: {state.current_task.is_completed}

**All Task Scores:** {state.all_task_scores}

**Timestamp:** {state.timestamp}
"""
        
        return info


# Initialize demo
demo = InteractiveEnvironmentDemo()


def create_interface():
    """Create Gradio interface."""
    
    with gr.Blocks(title="School Operations Environment", theme=gr.themes.Soft()) as app:
        
        gr.Markdown("""
# 🎓 AI-Powered School Operations Evaluation Environment

An **OpenEnv-compliant** environment for evaluating AI agents on real-world school operations tasks.

**Tasks:**
- 📧 **Email Classification** (Easy) - Categorize incoming emails
- 📅 **Timetable Scheduling** (Medium) - Create conflict-free schedules  
- 💬 **Student Support** (Hard) - Generate support responses

---
        """)
        
        # Control panel
        with gr.Row():
            difficulty_selector = gr.Radio(
                choices=["easy", "medium", "hard"],
                value="easy",
                label="Select Difficulty",
                scale=1
            )
            init_button = gr.Button("Initialize Environment", scale=1)
        
        init_status = gr.Textbox(label="Status", interactive=False)
        
        with gr.Row():
            task_info = gr.Textbox(label="Task Information", interactive=False)
            state_display = gr.Textbox(label="Environment State", interactive=False)
        
        # Task display
        task_display = gr.Markdown(label="Current Task")
        
        # Dynamic action panel
        with gr.Tabs():
            
            # Email Classification Tab
            with gr.TabItem("Email Classification"):
                with gr.Column():
                    email_category = gr.Radio(
                        choices=["admission", "academic", "behavioral", "health", "extracurricular", "other"],
                        label="Select Category"
                    )
                    email_submit = gr.Button("Submit Classification")
                    email_result = gr.Textbox(label="Result", interactive=False)
            
            # Timetable Scheduling Tab
            with gr.TabItem("Timetable Scheduling"):
                with gr.Column():
                    gr.Markdown("""
### Schedule Format (JSON)

```json
[
  {
    "class_name": "Class_A",
    "day": "Monday",
    "start_time": "09:00",
    "end_time": "10:30",
    "location": "101"
  }
]
```
                    """)
                    schedule_json = gr.Textbox(
                        value="[]",
                        label="Schedule (JSON)",
                        lines=10
                    )
                    schedule_submit = gr.Button("Submit Schedule")
                    schedule_result = gr.Textbox(label="Result", interactive=False)
            
            # Student Support Tab
            with gr.TabItem("Student Support"):
                with gr.Column():
                    support_response = gr.Textbox(
                        label="Support Response",
                        lines=6,
                        placeholder="Write your support response here..."
                    )
                    action_items_input = gr.Textbox(
                        label="Action Items (comma-separated)",
                        placeholder="Action 1, Action 2, Action 3"
                    )
                    urgency_input = gr.Radio(
                        choices=["low", "medium", "high"],
                        value="medium",
                        label="Urgency Level"
                    )
                    support_submit = gr.Button("Submit Response")
                    support_result = gr.Textbox(label="Result", interactive=False)
        
        # History and detailed display
        with gr.Row():
            history_display = gr.Markdown(label="Episode History")
        
        # Event handlers
        init_button.click(
            fn=demo.initialize_environment,
            inputs=[difficulty_selector],
            outputs=[init_status, task_info, task_display]
        ).then(
            fn=lambda: demo._get_state(),
            outputs=[state_display]
        )
        
        email_submit.click(
            fn=demo.submit_email_action,
            inputs=[email_category],
            outputs=[email_result, task_display, history_display, state_display]
        )
        
        schedule_submit.click(
            fn=demo.submit_schedule_action,
            inputs=[schedule_json],
            outputs=[schedule_result, task_display, history_display, state_display]
        )
        
        support_submit.click(
            fn=demo.submit_support_action,
            inputs=[support_response, action_items_input, urgency_input],
            outputs=[support_result, task_display, history_display, state_display]
        )
    
    return app


if __name__ == "__main__":
    app = create_interface()
    
    # Get port from environment or default to 7860
    port = int(os.getenv("GRADIO_SERVER_PORT", 7860))
    
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=False,
        show_error=True,
    )
