from __future__ import annotations
import json
from typing import Any, Dict, List
from pathlib import Path

from src.trivia.question import Question, QuestionType


class QuestionLoader:
    """Loads trivia questions from JSON text files."""

    @staticmethod
    def load_from_json(
            file_path: str
    ) -> List[Question]:
        """
        Load questions from a JSON file.

        Expected format: List of question objects with fields:
        - id: int
        - text: str
        - category: str
        - question_type: "MULTIPLE_CHOICE" or "OPEN_ANSWER"
        - correct_answer: str or number
        - options: list of strings (empty for open answer)
        - difficulty: int 1-5 (optional, defaults to 1)

        Args:
            file_path: Path to JSON file containing questions

        Returns:
            List of Question objects

        Raises:
            FileNotFoundError: If file does not exist
            json.JSONDecodeError: If file is not valid JSON
            ValueError: If question data is invalid
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Questions file not found: {file_path}")

        with open(path, 'r', encoding='utf-8') as f:
            data: Any = json.load(f)

        if not isinstance(data, list):
            raise ValueError("JSON must contain a list of questions")

        questions: List[Question] = []

        for idx, item in enumerate(data):  # type: ignore
            try:
                # Cast item to dict for type safety
                item_dict: Dict[str, Any] = item  # type: ignore

                # Get difficulty, default to 1
                difficulty: int = item_dict.get('difficulty', 1)  # type: ignore

                # Validate difficulty is 1-5
                if not isinstance(difficulty, int) or difficulty < 1 or difficulty > 5:
                    raise ValueError(
                        f"Question {idx}: difficulty must be 1-5, got {difficulty}"
                    )

                question = Question(
                    id=item_dict['id'],  # type: ignore
                    text=item_dict['text'],  # type: ignore
                    category=item_dict['category'],  # type: ignore
                    question_type=QuestionType[item_dict['question_type']],  # type: ignore
                    correct_answer=item_dict['correct_answer'],  # type: ignore
                    options=item_dict.get('options', []),  # type: ignore
                    difficulty=difficulty
                )
                questions.append(question)

            except KeyError as e:
                raise ValueError(
                    f"Question {idx}: Missing required field {e}"
                )
            except (ValueError, TypeError) as e:
                raise ValueError(f"Question {idx}: Invalid data - {e}")

        return questions

    @staticmethod
    def save_to_json(
            questions: List[Question],
            file_path: str
    ) -> None:
        """
        Save questions to a JSON file.

        Args:
            questions: List of Question objects to save
            file_path: Path where JSON file should be created
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = [q.to_dict() for q in questions]

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_from_multiple_files(
            file_paths: List[str]
    ) -> List[Question]:
        """
        Load questions from multiple JSON files.

        Args:
            file_paths: List of paths to JSON files

        Returns:
            Combined list of Question objects from all files
        """
        all_questions: List[Question] = []

        for file_path in file_paths:
            questions = QuestionLoader.load_from_json(file_path)
            all_questions.extend(questions)

        return all_questions


if __name__ == "__main__":
    print("=== Question Loader Test ===")

    # Create a sample questions file for testing
    sample_questions: List[Dict[str, Any]] = [
        {
            "id": 1,
            "text": "What is the capital of France?",
            "category": "Geography",
            "question_type": "MULTIPLE_CHOICE",
            "correct_answer": "Paris",
            "options": ["London", "Berlin", "Paris", "Madrid"],
            "difficulty": 1
        },
        {
            "id": 2,
            "text": "What is the approximate value of pi?",
            "category": "Math",
            "question_type": "OPEN_ANSWER",
            "correct_answer": 3.14159,
            "options": [],
            "difficulty": 3
        }
    ]

    # Save to test file
    test_file = "test_questions.json"
    QuestionLoader.save_to_json(
        [Question(**q) for q in sample_questions],  # type: ignore
        test_file
    )
    print(f"Saved sample questions to {test_file}")

    # Load from test file
    loaded = QuestionLoader.load_from_json(test_file)
    print(f"Loaded {len(loaded)} questions:")
    for q in loaded:
        print(f"  - {q.text} (difficulty: {q.difficulty})")

    print("\nQuestion loader working correctly!")
