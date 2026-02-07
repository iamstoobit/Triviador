import sys
import os
import tempfile
import unittest
from typing import Any

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.trivia.question import Question, QuestionType
from src.trivia.database import TriviaDatabase


class TestQuestion(unittest.TestCase):
    """Test the Question dataclass."""

    def test_mc_question_creation(self) -> None:
        """Test creating a valid multiple choice question."""
        q = Question(
            id=1,
            text="What is 2 + 2?",
            category="Math",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="4",
            options=["3", "4", "5", "6"]
        )
        self.assertEqual(q.text, "What is 2 + 2?")
        self.assertEqual(q.correct_answer, "4")
        self.assertTrue(q.is_multiple_choice())
        self.assertFalse(q.is_open_answer())

    def test_open_answer_question_creation(self) -> None:
        """Test creating a valid open answer question."""
        q = Question(
            id=2,
            text="What is the radius of Earth in km?",
            category="Science",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer=6371,
            options=[]
        )
        self.assertEqual(q.text, "What is the radius of Earth in km?")
        self.assertEqual(q.correct_answer, 6371)
        self.assertTrue(q.is_open_answer())
        self.assertFalse(q.is_multiple_choice())

    def test_mc_question_invalid_answer_not_in_options(self) -> None:
        """Test that MC question raises error if correct answer not in options."""
        with self.assertRaises(ValueError):
            Question(
                id=3,
                text="Test question?",
                category="Test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="NotInOptions",
                options=["A", "B", "C"]
            )

    def test_mc_question_invalid_no_options(self) -> None:
        """Test that MC question raises error if no options provided."""
        with self.assertRaises(ValueError):
            Question(
                id=4,
                text="Test question?",
                category="Test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="A",
                options=[]
            )

    def test_open_answer_invalid_non_numeric(self) -> None:
        """Test that open answer question requires numeric answer."""
        with self.assertRaises(ValueError):
            Question(
                id=5,
                text="Test question?",
                category="Test",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer="not_a_number",
                options=[]
            )

    def test_question_to_dict(self) -> None:
        """Test converting question to dictionary."""
        q = Question(
            id=6,
            text="What is Python?",
            category="Technology",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="A programming language",
            options=["A rock", "A snake", "A programming language", "Dinner"]
        )
        d = q.to_dict()
        self.assertEqual(d['id'], 6)
        self.assertEqual(d['text'], "What is Python?")
        self.assertEqual(d['question_type'], "MULTIPLE_CHOICE")

    def test_question_from_dict(self) -> None:
        """Test creating question from dictionary."""
        data: dict[str, Any] = {
            'id': 7,
            'text': "Test question",
            'category': "Test",
            'question_type': "MULTIPLE_CHOICE",
            'correct_answer': "B",
            'options': ["A", "B", "C"]
        }
        q = Question.from_dict(data)
        self.assertEqual(q.id, 7)
        self.assertEqual(q.text, "Test question")
        self.assertEqual(q.question_type, QuestionType.MULTIPLE_CHOICE)


class TestTriviaDatabase(unittest.TestCase):
    """Test the TriviaDatabase class."""

    def setUp(self) -> None:
        """Set up test database."""
        # Create a temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_questions.db")
        self.db = TriviaDatabase(self.db_path)

    def tearDown(self) -> None:
        """Clean up test database."""
        self.db.close()
        # Clean up temporary files
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_database_initialization(self) -> None:
        """Test that database initializes with proper tables."""
        cursor = self.db.connection.cursor()
        
        # Check questions table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='questions'"
        )
        self.assertIsNotNone(cursor.fetchone())
        
        # Check categories table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='categories'"
        )
        self.assertIsNotNone(cursor.fetchone())

    def test_default_categories_loaded(self) -> None:
        """Test that default categories are loaded."""
        cursor = self.db.connection.cursor()
        cursor.execute('SELECT COUNT(*) FROM categories')
        count = cursor.fetchone()[0]
        self.assertGreater(count, 0)

    def test_add_multiple_choice_question(self) -> None:
        """Test adding a multiple choice question."""
        q = Question(
            id=1,
            text="Test question?",
            category="Test",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="B",
            options=["A", "B", "C", "D"]
        )
        question_id = self.db.add_question(q, difficulty=1)
        self.assertIsNotNone(question_id)
        
        # Retrieve it back
        retrieved: Question = self.db.get_question(question_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.text, q.text)
        self.assertEqual(retrieved.correct_answer, q.correct_answer)

    def test_add_open_answer_question(self) -> None:
        """Test adding an open answer question."""
        q = Question(
            id=2,
            text="What is 2+2?",
            category="Math",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer=4,
            options=[]
        )
        question_id = self.db.add_question(q, difficulty=1)
        self.assertIsNotNone(question_id)
        
        # Retrieve it back
        retrieved = self.db.get_question(question_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.text, q.text)

    def test_get_multiple_choice_question(self) -> None:
        """Test retrieving multiple choice questions."""
        # Add multiple MC questions
        for i in range(5):
            q = Question(
                id=i,
                text=f"MC Question {i}?",
                category="Test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="A",
                options=["A", "B", "C", "D"]
            )
            self.db.add_question(q, difficulty=1)
        
        # Get a random MC question
        retrieved = self.db.get_multiple_choice_question()
        self.assertIsNotNone(retrieved)
        self.assertTrue(retrieved.is_multiple_choice())

    def test_get_open_answer_question(self) -> None:
        """Test retrieving open answer questions."""
        # Add multiple open answer questions
        for i in range(5):
            q = Question(
                id=100 + i,
                text=f"Open Question {i}?",
                category="Science",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=42.0,
                options=[]
            )
            self.db.add_question(q, difficulty=2)
        
        # Get a random open answer question
        retrieved = self.db.get_open_question(difficulty=2)
        self.assertIsNotNone(retrieved)
        self.assertTrue(retrieved.is_open_answer())

    def test_filter_by_category(self) -> None:
        """Test filtering questions by category."""
        # Add questions with different categories
        categories = ["Geography", "History", "Science"]
        for i, category in enumerate(categories):
            for j in range(2):
                q = Question(
                    id=200 + i * 2 + j,
                    text=f"{category} question {j}?",
                    category=category,
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    correct_answer="A",
                    options=["A", "B", "C", "D"]
                )
                self.db.add_question(q, difficulty=1)
        
        # Get a question only from Geography
        retrieved = self.db.get_multiple_choice_question(
            categories=["Geography"]
        )
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.category, "Geography")

    def test_filter_by_difficulty(self) -> None:
        """Test filtering questions by difficulty."""
        # Add questions with different difficulties
        for diff in [1, 2, 3]:
            q = Question(
                id=300 + diff,
                text=f"Difficulty {diff} question?",
                category="Test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="A",
                options=["A", "B", "C", "D"]
            )
            self.db.add_question(q, difficulty=diff)
        
        # Get a difficulty 3 question
        retrieved = self.db.get_multiple_choice_question(difficulty=3)
        self.assertIsNotNone(retrieved)
        # Should have difficulty matching or default behavior

    def test_get_nonexistent_question(self) -> None:
        """Test retrieving a question that doesn't exist."""
        retrieved = self.db.get_question(999999)
        self.assertIsNone(retrieved)


class TestQuestionTypeEnum(unittest.TestCase):
    """Test the QuestionType enum."""

    def test_multiple_choice_enum(self) -> None:
        """Test MULTIPLE_CHOICE enum value."""
        self.assertEqual(QuestionType.MULTIPLE_CHOICE.name, "MULTIPLE_CHOICE")

    def test_open_answer_enum(self) -> None:
        """Test OPEN_ANSWER enum value."""
        self.assertEqual(QuestionType.OPEN_ANSWER.name, "OPEN_ANSWER")

    def test_enum_iteration(self) -> None:
        """Test iterating through enum values."""
        types = list(QuestionType)
        self.assertEqual(len(types), 2)
        self.assertIn(QuestionType.MULTIPLE_CHOICE, types)
        self.assertIn(QuestionType.OPEN_ANSWER, types)


def run_tests() -> None:
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
