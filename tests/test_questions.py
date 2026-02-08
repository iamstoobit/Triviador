import sys
import os
import unittest
import tempfile
import json

from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.trivia.question import Question, QuestionType
from src.trivia.question_loader import QuestionLoader


class TestQuestion(unittest.TestCase):
    """Test the Question class."""

    def test_question_creation_mc(self) -> None:
        """Test creating a multiple choice question."""
        question = Question(
            id=1,
            text="What is 2 + 2?",
            category="Math",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="4",
            options=["3", "4", "5", "6"]
        )
        assert question.id == 1
        assert question.text == "What is 2 + 2?"
        assert question.is_multiple_choice() is True
        assert question.is_open_answer() is False
        assert question.difficulty == 1

    def test_question_creation_open_answer(self) -> None:
        """Test creating an open answer question."""
        question = Question(
            id=2,
            text="What is pi approximately?",
            category="Math",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer=3.14159,
            options=[],
            difficulty=3
        )
        assert question.id == 2
        assert question.is_open_answer() is True
        assert question.is_multiple_choice() is False
        assert question.difficulty == 3

    def test_question_difficulty_default(self) -> None:
        """Test that difficulty defaults to 1."""
        question = Question(
            id=1,
            text="Test?",
            category="Test",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="A",
            options=["A", "B"]
        )
        assert question.difficulty == 1

    def test_question_difficulty_range(self) -> None:
        """Test that difficulty can be set 1-5."""
        for diff in [1, 2, 3, 4, 5]:
            question = Question(
                id=1,
                text="Test?",
                category="Test",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=42,
                options=[],
                difficulty=diff
            )
            assert question.difficulty == diff

    def test_question_invalid_mc_no_options(self) -> None:
        """Test that MC question without options raises error."""
        with self.assertRaises(ValueError):
            Question(
                id=1,
                text="Test?",
                category="Test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="A",
                options=[]
            )

    def test_question_invalid_mc_answer_not_in_options(self) -> None:
        """Test that correct answer must be in options."""
        with self.assertRaises(ValueError):
            Question(
                id=1,
                text="Test?",
                category="Test",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Z",
                options=["A", "B", "C"]
            )

    def test_question_invalid_oa_non_numeric(self) -> None:
        """Test that open answer requires numeric answer."""
        with self.assertRaises(ValueError):
            Question(
                id=1,
                text="Test?",
                category="Test",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer="not a number",
                options=[]
            )

    def test_question_to_dict(self) -> None:
        """Test converting question to dictionary."""
        question = Question(
            id=5,
            text="Question text",
            category="Category",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Answer",
            options=["Answer", "Wrong1", "Wrong2"],
            difficulty=3
        )
        data = question.to_dict()

        assert data['id'] == 5
        assert data['text'] == "Question text"
        assert data['category'] == "Category"
        assert data['question_type'] == "MULTIPLE_CHOICE"
        assert data['correct_answer'] == "Answer"
        assert data['options'] == ["Answer", "Wrong1", "Wrong2"]
        assert data['difficulty'] == 3

    def test_question_from_dict(self) -> None:
        """Test creating question from dictionary."""
        data: dict[str, Any] = {
            'id': 10,
            'text': "What?",
            'category': "Science",
            'question_type': "OPEN_ANSWER",
            'correct_answer': 99.9,
            'options': [],
            'difficulty': 4
        }
        question = Question.from_dict(data)

        assert question.id == 10
        assert question.text == "What?"
        assert question.category == "Science"
        assert question.question_type == QuestionType.OPEN_ANSWER
        assert question.correct_answer == 99.9
        assert question.difficulty == 4

    def test_question_from_dict_default_difficulty(self) -> None:
        """Test that from_dict defaults difficulty to 1."""
        data: dict[str, Any] = {
            'id': 1,
            'text': "Test?",
            'category': "Test",
            'question_type': "MULTIPLE_CHOICE",
            'correct_answer': "A",
            'options': ["A", "B"]
        }
        question = Question.from_dict(data)
        assert question.difficulty == 1


class TestQuestionLoader(unittest.TestCase):
    """Test the QuestionLoader class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_load_from_json_valid(self) -> None:
        """Test loading valid questions from JSON."""
        test_file = os.path.join(self.temp_dir, "test.json")

        questions_data: list[dict[str, Any]] = [
            {
                "id": 1,
                "text": "What is 2+2?",
                "category": "Math",
                "question_type": "MULTIPLE_CHOICE",
                "correct_answer": "4",
                "options": ["3", "4", "5"],
                "difficulty": 1
            },
            {
                "id": 2,
                "text": "Estimate pi:",
                "category": "Math",
                "question_type": "OPEN_ANSWER",
                "correct_answer": 3.14159,
                "options": [],
                "difficulty": 2
            }
        ]

        with open(test_file, 'w') as f:
            json.dump(questions_data, f)

        questions = QuestionLoader.load_from_json(test_file)

        assert len(questions) == 2
        assert questions[0].id == 1
        assert questions[0].text == "What is 2+2?"
        assert questions[0].difficulty == 1
        assert questions[1].id == 2
        assert questions[1].difficulty == 2

    def test_load_from_json_file_not_found(self) -> None:
        """Test that FileNotFoundError is raised for missing file."""
        with self.assertRaises(FileNotFoundError):
            QuestionLoader.load_from_json("/nonexistent/file.json")

    def test_load_from_json_invalid_json(self) -> None:
        """Test that JSONDecodeError is raised for invalid JSON."""
        test_file = os.path.join(self.temp_dir, "invalid.json")

        with open(test_file, 'w') as f:
            f.write("{ invalid json }")

        with self.assertRaises(json.JSONDecodeError):
            QuestionLoader.load_from_json(test_file)

    def test_load_from_json_not_list(self) -> None:
        """Test that ValueError is raised if JSON is not a list."""
        test_file = os.path.join(self.temp_dir, "notlist.json")

        with open(test_file, 'w') as f:
            json.dump({"questions": []}, f)

        with self.assertRaises(ValueError):
            QuestionLoader.load_from_json(test_file)

    def test_load_from_json_missing_field(self) -> None:
        """Test that ValueError is raised for missing required field."""
        test_file = os.path.join(self.temp_dir, "missing.json")

        questions_data: list[dict[str, Any]] = [
            {
                "id": 1,
                "text": "What?",
                "question_type": "MULTIPLE_CHOICE",
                "correct_answer": "A",
                "options": ["A", "B"]
            }
        ]

        with open(test_file, 'w') as f:
            json.dump(questions_data, f)

        with self.assertRaises(ValueError):
            QuestionLoader.load_from_json(test_file)

    def test_load_from_json_invalid_difficulty(self) -> None:
        """Test that ValueError is raised for invalid difficulty."""
        test_file = os.path.join(self.temp_dir, "baddifficulty.json")

        questions_data: list[dict[str, Any]] = [
            {
                "id": 1,
                "text": "What?",
                "category": "Test",
                "question_type": "MULTIPLE_CHOICE",
                "correct_answer": "A",
                "options": ["A", "B"],
                "difficulty": 10  # Invalid: must be 1-5
            }
        ]

        with open(test_file, 'w') as f:
            json.dump(questions_data, f)

        with self.assertRaises(ValueError):
            QuestionLoader.load_from_json(test_file)

    def test_save_to_json(self) -> None:
        """Test saving questions to JSON."""
        test_file = os.path.join(self.temp_dir, "save_test.json")

        questions = [
            Question(
                id=1,
                text="Q1?",
                category="Cat1",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="A",
                options=["A", "B"],
                difficulty=2
            ),
            Question(
                id=2,
                text="Q2?",
                category="Cat2",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=42,
                options=[],
                difficulty=4
            )
        ]

        QuestionLoader.save_to_json(questions, test_file)

        # Verify file exists and can be loaded
        assert os.path.exists(test_file)

        loaded = QuestionLoader.load_from_json(test_file)
        assert len(loaded) == 2
        assert loaded[0].id == 1
        assert loaded[0].difficulty == 2
        assert loaded[1].id == 2
        assert loaded[1].difficulty == 4

    def test_load_from_multiple_files(self) -> None:
        """Test loading questions from multiple files."""
        file1 = os.path.join(self.temp_dir, "file1.json")
        file2 = os.path.join(self.temp_dir, "file2.json")

        data1: list[dict[str, Any]] = [
            {
                "id": 1,
                "text": "Q1?",
                "category": "Cat",
                "question_type": "MULTIPLE_CHOICE",
                "correct_answer": "A",
                "options": ["A", "B"],
                "difficulty": 1
            }
        ]

        data2: list[dict[str, Any]] = [
            {
                "id": 2,
                "text": "Q2?",
                "category": "Cat",
                "question_type": "OPEN_ANSWER",
                "correct_answer": 3.14,
                "options": [],
                "difficulty": 3
            }
        ]

        with open(file1, 'w') as f:
            json.dump(data1, f)

        with open(file2, 'w') as f:
            json.dump(data2, f)

        questions = QuestionLoader.load_from_multiple_files([file1, file2])

        assert len(questions) == 2
        assert questions[0].id == 1
        assert questions[1].id == 2


def run_tests() -> None:
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
