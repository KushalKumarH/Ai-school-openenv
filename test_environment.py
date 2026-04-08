"""
Comprehensive test suite for the School Operations Environment.
Tests all core functionality and edge cases.
"""

import unittest
import json
from environment import SchoolOperationsEnv
from models import (
    DifficultyLevel, TaskType, Action, EmailAction, 
    ScheduleAction, ScheduleSlot, SupportResponse, Observation, Reward
)
from graders import EmailGrader, ScheduleGrader, StudentSupportGrader


class TestEnvironmentBasics(unittest.TestCase):
    """Test basic environment functionality."""
    
    def setUp(self):
        self.env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
    
    def test_initialization(self):
        """Test environment initialization."""
        self.assertIsNotNone(self.env)
        self.assertEqual(self.env.difficulty, DifficultyLevel.EASY)
        self.assertEqual(self.env.seed, 42)
    
    def test_reset_returns_observation(self):
        """Test reset() returns valid Observation."""
        obs = self.env.reset()
        self.assertIsInstance(obs, Observation)
        self.assertIsNotNone(obs.task_type)
        self.assertIsNotNone(obs.episode_id)
        self.assertEqual(obs.step_number, 0)
    
    def test_step_returns_tuple(self):
        """Test step() returns (obs, reward, done, info)."""
        obs = self.env.reset()
        action = Action(
            task_type=obs.task_type,
            email_action=EmailAction(category="academic")
        )
        result = self.env.step(action)
        
        self.assertEqual(len(result), 4)
        next_obs, reward, done, info = result
        
        self.assertIsInstance(next_obs, Observation)
        self.assertIsInstance(reward, Reward)
        self.assertIsInstance(done, bool)
        self.assertIsInstance(info, dict)
    
    def test_reward_bounds(self):
        """Test reward values are within [-1, 1]."""
        obs = self.env.reset()
        for _ in range(5):
            action = Action(
                task_type=obs.task_type,
                email_action=EmailAction(category="academic") if obs.task_type == TaskType.EMAIL_CLASSIFICATION else None
            )
            _, reward, done, _ = self.env.step(action)
            
            self.assertGreaterEqual(reward.total_reward, -1.0)
            self.assertLessEqual(reward.total_reward, 1.0)
            
            if done:
                break


class TestEmailClassification(unittest.TestCase):
    """Test email classification task."""
    
    def setUp(self):
        self.env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
    
    def test_email_task_generated(self):
        """Test email task is generated for EASY difficulty."""
        obs = self.env.reset()
        self.assertEqual(obs.task_type, TaskType.EMAIL_CLASSIFICATION)
        self.assertIsNotNone(obs.email_data)
    
    def test_email_grader_scoring(self):
        """Test email grader produces valid scores."""
        from models import EmailData
        
        email = EmailData(
            subject="Exam results",
            body="Your exam grade is posted",
            sender="teacher@school.edu"
        )
        action = EmailAction(category="academic")
        
        score, feedback = EmailGrader.grade(email, action)
        
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIsInstance(feedback, str)
    
    def test_email_action_handling(self):
        """Test email action execution."""
        obs = self.env.reset()
        
        action = Action(
            task_type=TaskType.EMAIL_CLASSIFICATION,
            email_action=EmailAction(category="health")
        )
        
        next_obs, reward, done, info = self.env.step(action)
        
        self.assertIsInstance(reward.total_reward, float)
        self.assertGreaterEqual(reward.breakdown.task_score, 0.0)


class TestTimetableScheduling(unittest.TestCase):
    """Test timetable scheduling task."""
    
    def setUp(self):
        self.env = SchoolOperationsEnv(difficulty=DifficultyLevel.MEDIUM, seed=42)
    
    def test_scheduling_task_generated(self):
        """Test scheduling task is generated for MEDIUM difficulty."""
        obs = self.env.reset()
        self.assertEqual(obs.task_type, TaskType.TIMETABLE_SCHEDULING)
        self.assertIsNotNone(obs.schedule_constraints)
        self.assertGreater(len(obs.schedule_constraints), 0)
    
    def test_schedule_action_handling(self):
        """Test schedule action execution."""
        obs = self.env.reset()
        
        action = Action(
            task_type=TaskType.TIMETABLE_SCHEDULING,
            schedule_action=ScheduleAction(schedule=[
                ScheduleSlot(
                    class_name="Class_A",
                    day="Monday",
                    start_time="09:00",
                    end_time="10:00",
                    location="101"
                )
            ])
        )
        
        next_obs, reward, done, info = self.env.step(action)
        
        self.assertIsInstance(reward.total_reward, float)
        self.assertGreaterEqual(reward.breakdown.task_score, 0.0)
        self.assertLessEqual(reward.breakdown.task_score, 1.0)
    
    def test_schedule_grader_clash_detection(self):
        """Test schedule grader detects clashes."""
        from models import ScheduleConstraint
        
        constraints = [
            ScheduleConstraint(
                class_name="Class_A",
                teacher="Ms. Smith",
                duration_minutes=60,
                students=["Alice", "Bob"],
                preferred_times=None
            )
        ]
        
        # Schedule with clash
        action = ScheduleAction(schedule=[
            ScheduleSlot(class_name="Class_A", day="Monday", start_time="09:00", end_time="10:00", location="101"),
            ScheduleSlot(class_name="Class_A", day="Monday", start_time="09:30", end_time="10:30", location="101"),
        ])
        
        score, feedback, breakdown = ScheduleGrader.grade(constraints, action)
        
        self.assertLess(score, 1.0, "Clashing schedule should not get perfect score")


class TestStudentSupport(unittest.TestCase):
    """Test student support response task."""
    
    def setUp(self):
        self.env = SchoolOperationsEnv(difficulty=DifficultyLevel.HARD, seed=42)
    
    def test_support_task_generated(self):
        """Test support task is generated for HARD difficulty."""
        obs = self.env.reset()
        self.assertEqual(obs.task_type, TaskType.STUDENT_SUPPORT)
        self.assertIsNotNone(obs.student_query)
    
    def test_support_action_handling(self):
        """Test support action execution."""
        obs = self.env.reset()
        
        action = Action(
            task_type=TaskType.STUDENT_SUPPORT,
            support_action=SupportResponse(
                response="I understand your concern and can help you connect with tutoring resources.",
                action_items=["Schedule with tutor", "Practice problems"],
                urgency="medium"
            )
        )
        
        next_obs, reward, done, info = self.env.step(action)
        
        self.assertIsInstance(reward.total_reward, float)
        self.assertGreater(reward.breakdown.task_score, 0.0)
    
    def test_support_grader_keyword_coverage(self):
        """Test support grader evaluates keyword coverage."""
        from models import StudentQuery
        
        query = StudentQuery(
            student_name="Alice",
            issue_type="academic",
            query="I'm struggling with calculus",
            context=None
        )
        
        response_with_keywords = SupportResponse(
            response="I can help you with tutoring resources and study support",
            action_items=[],
            urgency="medium"
        )
        
        response_without_keywords = SupportResponse(
            response="OK",
            action_items=[],
            urgency="medium"
        )
        
        score1, _, _ = StudentSupportGrader.grade(query, response_with_keywords)
        score2, _, _ = StudentSupportGrader.grade(query, response_without_keywords)
        
        self.assertGreater(score1, score2, "Response with keywords should score higher")


class TestReproducibility(unittest.TestCase):
    """Test reproducibility with same seed."""
    
    def test_same_seed_same_observations(self):
        """Test same seed produces same observations."""
        env1 = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
        env2 = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
        
        obs1 = env1.reset()
        obs2 = env2.reset()
        
        self.assertEqual(obs1.email_data.subject, obs2.email_data.subject)
        self.assertEqual(obs1.email_data.body, obs2.email_data.body)
    
    def test_different_seed_different_observations(self):
        """Test different seeds produce different observations."""
        env1 = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
        env2 = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=123)
        
        obs1 = env1.reset()
        obs2 = env2.reset()
        
        # At least one field should differ (not guaranteed but very likely)
        self.assertNotEqual(obs1.episode_id, obs2.episode_id)


class TestEpisodeTermination(unittest.TestCase):
    """Test episode termination logic."""
    
    def test_episode_terminates_on_max_steps(self):
        """Test episode terminates at max steps."""
        env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
        obs = env.reset()
        
        for _ in range(env.max_steps):
            action = Action(
                task_type=TaskType.EMAIL_CLASSIFICATION,
                email_action=EmailAction(category="academic")
            )
            obs, reward, done, info = env.step(action)
            
            if done:
                break
        
        # Should terminate either at good score or max steps
        self.assertTrue(done or env.step_count >= env.max_steps)


class TestEnvironmentState(unittest.TestCase):
    """Test environment state tracking."""
    
    def test_state_returns_valid_structure(self):
        """Test state() returns valid EnvironmentState."""
        env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
        env.reset()
        
        state = env.state()
        
        self.assertIsNotNone(state.episode_id)
        self.assertGreater(state.episode_number, 0)
        self.assertIsNotNone(state.current_task)
        self.assertIsNotNone(state.timestamp)
    
    def test_cumulative_reward_tracking(self):
        """Test cumulative reward is tracked correctly."""
        env = SchoolOperationsEnv(difficulty=DifficultyLevel.EASY, seed=42)
        env.reset()
        
        initial_state = env.state()
        initial_reward = initial_state.current_task.cumulative_reward
        
        action = Action(
            task_type=TaskType.EMAIL_CLASSIFICATION,
            email_action=EmailAction(category="academic")
        )
        _, reward, _, _ = env.step(action)
        
        final_state = env.state()
        final_reward = final_state.current_task.cumulative_reward
        
        self.assertEqual(final_reward, initial_reward + reward.total_reward)


def run_all_tests():
    """Run all test suites."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestEmailClassification))
    suite.addTests(loader.loadTestsFromTestCase(TestTimetableScheduling))
    suite.addTests(loader.loadTestsFromTestCase(TestStudentSupport))
    suite.addTests(loader.loadTestsFromTestCase(TestReproducibility))
    suite.addTests(loader.loadTestsFromTestCase(TestEpisodeTermination))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentState))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_all_tests()
    sys.exit(0 if success else 1)
