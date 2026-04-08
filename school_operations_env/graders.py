"""
Deterministic graders for each task.
Each grader returns a score between 0.0 and 1.0.
"""

import re
from typing import Dict, List, Tuple
from models import (
    EmailAction, EmailData, ScheduleAction, ScheduleConstraint,
    SupportResponse, StudentQuery
)


class EmailGrader:
    """Grader for email classification task (EASY)."""
    
    # Ground truth mapping
    CATEGORY_MAPPING = {
        "admission": ["admit", "enrollment", "application", "registration", "new student"],
        "academic": ["grade", "homework", "assignment", "exam", "course", "curriculum", "syllabus"],
        "behavioral": ["behavior", "conduct", "discipline", "incident", "bullying"],
        "health": ["health", "medical", "illness", "medication", "nurse", "doctor", "sick", "absent"],
        "extracurricular": ["club", "sports", "event", "competition", "activity"],
    }
    
    @staticmethod
    def infer_ground_truth(email: EmailData) -> str:
        """Infer the correct category from email content."""
        combined_text = (email.subject + " " + email.body).lower()
        
        scores = {}
        for category, keywords in EmailGrader.CATEGORY_MAPPING.items():
            score = sum(1 for kw in keywords if kw in combined_text)
            scores[category] = score
        
        if not scores or max(scores.values()) == 0:
            return "other"
        return max(scores, key=scores.get)
    
    @staticmethod
    def grade(email: EmailData, action: EmailAction) -> Tuple[float, str]:
        """
        Grade email classification.
        Returns (score, feedback)
        """
        ground_truth = EmailGrader.infer_ground_truth(email)
        
        if action.category == ground_truth:
            return 1.0, f"Correct classification: {action.category}"
        else:
            return 0.0, f"Incorrect. Expected '{ground_truth}', got '{action.category}'"


class ScheduleGrader:
    """Grader for timetable scheduling task (MEDIUM)."""
    
    @staticmethod
    def check_no_clashes(slots: List[Dict]) -> Tuple[bool, List[str]]:
        """Check if schedule has no overlapping classes."""
        conflicts = []
        
        for i, slot1 in enumerate(slots):
            for slot2 in slots[i+1:]:
                # Same day and location
                if slot1["day"] == slot2["day"] and slot1["location"] == slot2["location"]:
                    # Check time overlap
                    start1 = ScheduleGrader._time_to_minutes(slot1["start_time"])
                    end1 = ScheduleGrader._time_to_minutes(slot1["end_time"])
                    start2 = ScheduleGrader._time_to_minutes(slot2["start_time"])
                    end2 = ScheduleGrader._time_to_minutes(slot2["end_time"])
                    
                    if not (end1 <= start2 or end2 <= start1):
                        conflicts.append(
                            f"Clash: {slot1['class_name']} and {slot2['class_name']} "
                            f"on {slot1['day']}"
                        )
        
        return len(conflicts) == 0, conflicts
    
    @staticmethod
    def check_duration_match(
        constraints: List[ScheduleConstraint],
        slots: List[Dict]
    ) -> Tuple[float, List[str]]:
        """Check if scheduled durations match constraints."""
        issues = []
        score = 0.0
        
        for constraint in constraints:
            matching_slots = [s for s in slots if s["class_name"] == constraint.class_name]
            
            if not matching_slots:
                issues.append(f"Missing schedule for {constraint.class_name}")
                continue
            
            total_duration = sum(
                ScheduleGrader._time_to_minutes(s["end_time"]) - 
                ScheduleGrader._time_to_minutes(s["start_time"])
                for s in matching_slots
            )
            
            if total_duration == constraint.duration_minutes:
                score += 1.0 / len(constraints)
            else:
                issues.append(
                    f"{constraint.class_name}: expected {constraint.duration_minutes}min, "
                    f"got {total_duration}min"
                )
        
        return score, issues
    
    @staticmethod
    def check_time_preferences(
        constraints: List[ScheduleConstraint],
        slots: List[Dict]
    ) -> float:
        """Bonus for respecting preferred times."""
        if not constraints:
            return 0.0
        
        preferences_met = 0
        preferences_total = 0
        
        for constraint in constraints:
            if not constraint.preferred_times:
                continue
            
            preferences_total += 1
            matching_slots = [s for s in slots if s["class_name"] == constraint.class_name]
            
            for slot in matching_slots:
                slot_time = slot["start_time"]
                if slot_time in constraint.preferred_times:
                    preferences_met += 1
                    break
        
        if preferences_total == 0:
            return 0.0
        return preferences_met / preferences_total * 0.1
    
    @staticmethod
    def grade(
        constraints: List[ScheduleConstraint],
        action: ScheduleAction
    ) -> Tuple[float, str, Dict]:
        """
        Grade timetable schedule.
        Returns (score, feedback, breakdown)
        """
        slots = [s.model_dump() for s in action.schedule]
        
        # Check for clashes (critical)
        no_clashes, clash_issues = ScheduleGrader.check_no_clashes(slots)
        clash_penalty = 0.0 if no_clashes else -0.3
        
        # Check duration match
        duration_score, duration_issues = ScheduleGrader.check_duration_match(constraints, slots)
        
        # Check time preferences
        preference_bonus = ScheduleGrader.check_time_preferences(constraints, slots)
        
        total_score = max(0.0, min(1.0, duration_score + clash_penalty + preference_bonus))
        
        all_issues = clash_issues + duration_issues
        feedback = f"Score: {total_score:.2f}. " + " | ".join(all_issues) if all_issues else "Perfect schedule!"
        
        return total_score, feedback, {
            "duration_match": duration_score,
            "clash_penalty": clash_penalty,
            "preference_bonus": preference_bonus
        }
    
    @staticmethod
    def _time_to_minutes(time_str: str) -> int:
        """Convert HH:MM to minutes since midnight."""
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes


class StudentSupportGrader:
    """Grader for student support response task (HARD)."""
    
    # Keywords that should be in responses based on issue type
    ISSUE_KEYWORDS = {
        "academic": ["help", "tutor", "resource", "study", "support", "teacher"],
        "behavioral": ["discuss", "understand", "consequence", "improvement", "support"],
        "health": ["nurse", "doctor", "medical", "wellness", "care", "well-being"],
        "personal": ["listen", "support", "resource", "counselor", "talk", "help"],
    }
    
    # Tone rules
    POSITIVE_TONE_KEYWORDS = ["support", "help", "understand", "together", "can", "will", "let's"]
    NEGATIVE_TONE_KEYWORDS = ["fail", "bad", "wrong", "stupid", "lazy", "problem"]
    
    @staticmethod
    def check_keyword_coverage(query: StudentQuery, response: str) -> float:
        """Check if response covers relevant keywords for the issue type."""
        issue_type = query.issue_type.lower()
        keywords = StudentSupportGrader.ISSUE_KEYWORDS.get(issue_type, [])
        
        if not keywords:
            return 0.5
        
        response_lower = response.lower()
        covered = sum(1 for kw in keywords if kw in response_lower)
        
        return covered / len(keywords)
    
    @staticmethod
    def check_correctness(query: StudentQuery, response: str) -> float:
        """Check if response addresses the query appropriately."""
        response_lower = response.lower()
        
        # Check if response is long enough
        if len(response.split()) < 10:
            return 0.0
        
        # Check for acknowledgment of the issue
        acknowledgment_keywords = ["understand", "hear", "concern", "issue", "challenge"]
        acknowledges = any(kw in response_lower for kw in acknowledgment_keywords)
        
        if not acknowledges:
            return 0.3
        
        # Check for proposed solution or next steps
        solution_keywords = ["can", "will", "help", "support", "resource", "plan", "next"]
        has_solution = any(kw in response_lower for kw in solution_keywords)
        
        if not has_solution:
            return 0.5
        
        return 1.0
    
    @staticmethod
    def check_tone(response: str) -> float:
        """Check if tone is appropriate (supportive, not judgmental)."""
        response_lower = response.lower()
        
        # Check for negative tone
        negative_count = sum(1 for kw in StudentSupportGrader.NEGATIVE_TONE_KEYWORDS 
                            if kw in response_lower)
        
        # Check for positive tone
        positive_count = sum(1 for kw in StudentSupportGrader.POSITIVE_TONE_KEYWORDS 
                            if kw in response_lower)
        
        if negative_count > 0:
            return max(0.0, 1.0 - (negative_count * 0.2))
        
        if positive_count > 0:
            return min(1.0, positive_count * 0.15)
        
        return 0.5
    
    @staticmethod
    def grade(query: StudentQuery, action: SupportResponse) -> Tuple[float, str, Dict]:
        """
        Grade student support response.
        Returns (score, feedback, breakdown)
        """
        keyword_score = StudentSupportGrader.check_keyword_coverage(query, action.response)
        correctness_score = StudentSupportGrader.check_correctness(query, action.response)
        tone_score = StudentSupportGrader.check_tone(action.response)
        
        # Check if action items are provided
        action_item_bonus = 0.1 if action.action_items else 0.0
        
        # Weighted average
        total_score = (
            keyword_score * 0.25 +
            correctness_score * 0.40 +
            tone_score * 0.25 +
            action_item_bonus
        )
        
        breakdown = {
            "keyword_coverage": keyword_score,
            "correctness": correctness_score,
            "tone": tone_score,
            "action_item_bonus": action_item_bonus
        }
        
        feedback = (
            f"Keyword coverage: {keyword_score:.2f} | "
            f"Correctness: {correctness_score:.2f} | "
            f"Tone: {tone_score:.2f} | "
            f"Action items: {'Yes (+0.1)' if action.action_items else 'No (0.0)'}"
        )
        
        return total_score, feedback, breakdown
