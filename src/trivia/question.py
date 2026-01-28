"""
src/trivia/question.py - Question data model
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Any
from enum import Enum, auto


class QuestionType(Enum):
    """Type of trivia question."""
    MULTIPLE_CHOICE = auto()
    OPEN_ANSWER = auto()


@dataclass
class Question:
    """
    Represents a trivia question.
    """
    
    id: int
    text: str
    category: str
    question_type: QuestionType
    correct_answer: Any  # String for MC, number for Open Answer
    options: List[str]  # Empty for Open Answer
    
    def __post_init__(self) -> None:
        """Validate question data."""
        if self.question_type == QuestionType.MULTIPLE_CHOICE:
            if not self.options:
                raise ValueError("Multiple choice questions must have options")
            if self.correct_answer not in self.options:
                raise ValueError(f"Correct answer '{self.correct_answer}' not in options: {self.options}")
        elif self.question_type == QuestionType.OPEN_ANSWER:
            # For open answer, correct_answer should be numeric
            try:
                float(self.correct_answer)
            except (ValueError, TypeError):
                raise ValueError(f"Open answer questions must have numeric answers. Got: {self.correct_answer}")
    
    def to_dict(self) -> dict:
        """Convert question to dictionary for serialization."""
        return {
            'id': self.id,
            'text': self.text,
            'category': self.category,
            'question_type': self.question_type.name,
            'correct_answer': self.correct_answer,
            'options': self.options.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Question:
        """Create question from dictionary."""
        return cls(
            id=data['id'],
            text=data['text'],
            category=data['category'],
            question_type=QuestionType[data['question_type']],
            correct_answer=data['correct_answer'],
            options=data['options']
        )
    
    def is_multiple_choice(self) -> bool:
        """Check if question is multiple choice."""
        return self.question_type == QuestionType.MULTIPLE_CHOICE
    
    def is_open_answer(self) -> bool:
        """Check if question is open answer."""
        return self.question_type == QuestionType.OPEN_ANSWER


# Helper function for creating test questions
def create_test_question() -> Question:
    """Create a test question for development."""
    return Question(
        id=999,
        text="What is the capital of France?",
        category="Geography",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer="Paris",
        options=["London", "Berlin", "Paris", "Madrid"]
    )


if __name__ == "__main__":
    print("=== Testing Question Class ===")
    
    # Test multiple choice question
    mc_question = Question(
        id=1,
        text="What is 2 + 2?",
        category="Math",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer="4",
        options=["3", "4", "5", "6"]
    )
    print(f"MC Question: {mc_question.text}")
    print(f"Correct: {mc_question.correct_answer}")
    print(f"Options: {mc_question.options}")
    
    # Test open answer question
    oa_question = Question(
        id=2,
        text="What is the approximate value of π?",
        category="Math",
        question_type=QuestionType.OPEN_ANSWER,
        correct_answer=3.14159,
        options=[]
    )
    print(f"\nOA Question: {oa_question.text}")
    print(f"Correct: {oa_question.correct_answer}")
    
    # Test serialization
    mc_dict = mc_question.to_dict()
    print(f"\nMC Question dict: {mc_dict}")
    
    restored = Question.from_dict(mc_dict)
    print(f"Restored question text: {restored.text}")
    
    print("\nAll tests passed!")