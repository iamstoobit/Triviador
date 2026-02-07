from __future__ import annotations
import sqlite3
import json
import random
from typing import List, Optional, Any
from pathlib import Path

from src.trivia.question import Question, QuestionType


class TriviaDatabase:
    """
    Manages trivia questions in an SQLite database.
    Supports both multiple choice and open answer questions.
    """

    def __init__(self, db_path: str = "data/questions.db"):
        """
        Initialize the trivia database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._ensure_database()

    def _ensure_database(self) -> None:
        """Ensure database and tables exist."""
        # Create data directory if it doesn't exist
        Path(self.db_path).parent.mkdir(exist_ok=True)

        self.connect()
        cursor = self.connection.cursor()

        # Create questions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                category TEXT NOT NULL,
                question_type TEXT NOT NULL CHECK(question_type IN ('MULTIPLE_CHOICE', 'OPEN_ANSWER')),
                correct_answer TEXT NOT NULL,
                options_json TEXT,  -- JSON array for multiple choice options
                difficulty INTEGER DEFAULT 1,  -- 1=easy, 2=medium, 3=hard
                times_asked INTEGER DEFAULT 0,
                last_asked TIMESTAMP DEFAULT NULL
            )
        ''')

        # Create categories table for reference
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
        ''')

        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON questions(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_type ON questions(question_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_difficulty ON questions(difficulty)')

        self.connection.commit()

        # Insert default categories if empty
        cursor.execute('SELECT COUNT(*) FROM categories')
        if cursor.fetchone()[0] == 0:
            self._insert_default_categories()

    def _insert_default_categories(self) -> None:
        """Insert default categories into the database."""
        default_categories = [
            ("Geography", "Questions about countries, cities, and physical features"),
            ("History", "Historical events, figures, and timelines"),
            ("Science", "Biology, chemistry, physics, and astronomy"),
            ("Entertainment", "Movies, TV shows, and celebrities"),
            ("Sports", "Athletes, teams, and sporting events"),
            ("Art", "Painters, sculptures, and art history"),
            ("Literature", "Authors, books, and literary terms"),
            ("Technology", "Computers, programming, and inventions"),
            ("Movies", "Film directors, actors, and movie trivia"),
            ("Music", "Musicians, bands, and music theory"),
            ("General Knowledge", "Mixed trivia from various categories"),
            ("Pop Culture", "Current trends, memes, and popular culture")
        ]

        cursor = self.connection.cursor()
        cursor.executemany(
            'INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)',
            default_categories
        )
        self.connection.commit()

    def connect(self) -> None:
        """Connect to the database."""
        if self.connection is None:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Return rows as dicts

    def close(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    def add_question(self, question: Question, difficulty: int = 1) -> int:
        """
        Add a question to the database.

        Args:
            question: Question object to add
            difficulty: 1=easy, 2=medium, 3=hard

        Returns:
            ID of the inserted question
        """
        self.connect()
        cursor = self.connection.cursor()

        # Convert options list to JSON
        options_json = json.dumps(question.options) if question.options else None

        cursor.execute('''
            INSERT INTO questions
            (text, category, question_type, correct_answer, options_json, difficulty)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            question.text,
            question.category,
            question.question_type.name,
            str(question.correct_answer),
            options_json,
            difficulty
        ))

        self.connection.commit()
        return cursor.lastrowid

    def get_question(self, question_id: int) -> Optional[Question]:
        """
        Get a question by ID.

        Args:
            question_id: ID of the question to retrieve

        Returns:
            Question object or None if not found
        """
        self.connect()
        cursor = self.connection.cursor()

        cursor.execute('SELECT * FROM questions WHERE id = ?', (question_id,))
        row = cursor.fetchone()

        if not row:
            return None

        return self._row_to_question(row)

    def get_random_question(self, categories: Optional[List[str]] = None,
                            question_type: Optional[QuestionType] = None,
                            difficulty: Optional[int] = None) -> Optional[Question]:
        """
        Get a random question matching criteria.

        Args:
            categories: List of categories to include (None = all categories)
            question_type: Type of question (None = any type)
            difficulty: 1=easy, 2=medium, 3=hard (None = any difficulty)

        Returns:
            Random question or None if no matches
        """
        self.connect()
        cursor = self.connection.cursor()

        query = 'SELECT * FROM questions WHERE 1=1'
        params = []

        if categories:
            placeholders = ','.join(['?'] * len(categories))
            query += f' AND category IN ({placeholders})'
            params.extend(categories)

        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type.name)

        if difficulty:
            query += ' AND difficulty = ?'
            params.append(difficulty)

        # Get count first
        count_query = f'SELECT COUNT(*) FROM ({query})'
        cursor.execute(count_query, params)
        count = cursor.fetchone()[0]

        if count == 0:
            return None

        # Get random row
        query += ' ORDER BY RANDOM() LIMIT 1'
        cursor.execute(query, params)
        row = cursor.fetchone()

        if not row:
            return None

        # Update usage statistics
        self._record_question_usage(row['id'])

        return self._row_to_question(row)

    def get_multiple_choice_question(self, categories: Optional[List[str]] = None,
                                     difficulty: Optional[int] = None) -> Optional[Question]:
        """
        Get a random multiple choice question.

        Args:
            categories: List of categories to include
            difficulty: 1=easy, 2=medium, 3=hard

        Returns:
            Multiple choice question or None
        """
        return self.get_random_question(
            categories=categories,
            question_type=QuestionType.MULTIPLE_CHOICE,
            difficulty=difficulty
        )

    def get_open_question(self, categories: Optional[List[str]] = None,
                          difficulty: Optional[int] = None) -> Optional[Question]:
        """
        Get a random open answer question.

        Args:
            categories: List of categories to include
            difficulty: 1=easy, 2=medium, 3=hard

        Returns:
            Open answer question or None
        """
        return self.get_random_question(
            categories=categories,
            question_type=QuestionType.OPEN_ANSWER,
            difficulty=difficulty
        )

    def _record_question_usage(self, question_id: int) -> None:
        """Record that a question was asked."""
        cursor = self.connection.cursor()
        cursor.execute('''
            UPDATE questions
            SET times_asked = times_asked + 1,
                last_asked = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (question_id,))
        self.connection.commit()

    def _row_to_question(self, row: sqlite3.Row) -> Question:
        """Convert database row to Question object."""
        # Parse options from JSON
        options = []
        if row['options_json']:
            try:
                options = json.loads(row['options_json'])
            except json.JSONDecodeError:
                options = []

        # Shuffle options for multiple choice questions]
        if row['question_type'] == 'MULTIPLE_CHOICE' and options:
            random.shuffle(options)

        # Parse correct answer based on question type
        question_type = QuestionType[row['question_type']]
        correct_answer = row['correct_answer']

        if question_type == QuestionType.OPEN_ANSWER:
            # Try to convert to number
            try:
                if '.' in correct_answer:
                    correct_answer = float(correct_answer)
                else:
                    correct_answer = int(correct_answer)
            except (ValueError, TypeError):
                # Fallback to float if possible
                try:
                    correct_answer = float(correct_answer)
                except (ValueError, TypeError):
                    correct_answer = 0.0

        return Question(
            id=row['id'],
            text=row['text'],
            category=row['category'],
            question_type=question_type,
            correct_answer=correct_answer,
            options=options
        )

    def get_all_categories(self) -> List[str]:
        """
        Get all unique categories in the database.

        Returns:
            List of category names
        """
        self.connect()
        cursor = self.connection.cursor()

        cursor.execute('SELECT DISTINCT category FROM questions ORDER BY category')
        return [row['category'] for row in cursor.fetchall()]

    def get_question_count(self, category: Optional[str] = None,
                           question_type: Optional[QuestionType] = None) -> int:
        """
        Get count of questions matching criteria.

        Args:
            category: Filter by category (None = all categories)
            question_type: Filter by question type (None = all types)

        Returns:
            Number of questions
        """
        self.connect()
        cursor = self.connection.cursor()

        query = 'SELECT COUNT(*) FROM questions WHERE 1=1'
        params = []

        if category:
            query += ' AND category = ?'
            params.append(category)

        if question_type:
            query += ' AND question_type = ?'
            params.append(question_type.name)

        cursor.execute(query, params)
        return cursor.fetchone()[0]

    def import_from_json(self, json_path: str) -> int:
        """
        Import questions from JSON file.

        Args:
            json_path: Path to JSON file

        Returns:
            Number of questions imported
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = 0
        for item in data:
            question = Question.from_dict(item)
            self.add_question(question)
            count += 1

        return count

    def export_to_json(
            self, json_path: str,
            categories: Optional[List[str]] = None
    ) -> int:
        """
        Export questions to JSON file.

        Args:
            json_path: Path to output JSON file
            categories: Filter by categories (None = all)

        Returns:
            Number of questions exported
        """
        self.connect()
        cursor = self.connection.cursor()

        query = 'SELECT * FROM questions WHERE 1=1'
        params: List[Any] = []

        if categories:
            placeholders = ','.join(['?'] * len(categories))
            query += f' AND category IN ({placeholders})'
            params.extend(categories)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        questions = [self._row_to_question(row).to_dict() for row in rows]

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)

        return len(questions)

    def add_sample_questions(self) -> None:
        """Add sample questions for testing."""
        sample_questions = [
            # Multiple Choice Questions
            Question(
                id=0,  # Will be auto-incremented
                text="What is the capital of France?",
                category="Geography",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Paris",
                options=["London", "Berlin", "Paris", "Madrid"]
            ),
            Question(
                id=0,
                text="Who painted the Mona Lisa?",
                category="Art",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Leonardo da Vinci",
                options=["Vincent van Gogh", "Leonardo da Vinci", "Pablo Picasso", "Michelangelo"]
            ),
            Question(
                id=0,
                text="What is the chemical symbol for gold?",
                category="Science",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Au",
                options=["Ag", "Au", "Fe", "Pb"]
            ),
            Question(
                id=0,
                text="In which year did World War II end?",
                category="History",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="1945",
                options=["1939", "1941", "1945", "1950"]
            ),

            # Open Answer Questions
            Question(
                id=0,
                text="What is the approximate value of π (pi) to two decimal places?",
                category="Science",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=3.14,
                options=[]
            ),
            Question(
                id=0,
                text="How many players are on a soccer team during a match?",
                category="Sports",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=11,
                options=[]
            ),
            Question(
                id=0,
                text="What is the atomic number of carbon?",
                category="Science",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=6,
                options=[]
            ),
            Question(
                id=0,
                text="In what year was the first iPhone released?",
                category="Technology",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=2007,
                options=[]
            ),
            Question(
                id=0,
                text="How many continents are there?",
                category="Geography",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=7,
                options=[]
            ),
            Question(
                id=0,
                text="What is the height of Mount Everest in meters?",
                category="Geography",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=8848,
                options=[]
            )
        ]

        print("Adding sample questions...")
        for question in sample_questions:
            self.add_question(question)
        print(f"Added {len(sample_questions)} sample questions")


if __name__ == "__main__":
    print("=== Testing TriviaDatabase ===")

    # Use in-memory database for testing
    db = TriviaDatabase(":memory:")

    # Add sample questions
    db.add_sample_questions()

    # Test getting categories
    categories = db.get_all_categories()
    print(f"Categories: {categories}")

    # Test getting random questions
    mc_question = db.get_multiple_choice_question()
    if mc_question:
        print(f"\nRandom MC Question: {mc_question.text}")
        print(f"Options: {mc_question.options}")
        print(f"Correct: {mc_question.correct_answer}")

    oa_question = db.get_open_question()
    if oa_question:
        print(f"\nRandom OA Question: {oa_question.text}")
        print(f"Correct: {oa_question.correct_answer}")

    # Test filtered questions
    geo_questions = db.get_open_question(categories=["Geography"])
    if geo_questions:
        print(f"\nGeography OA Question: {geo_questions.text}")

    # Test counts
    total = db.get_question_count()
    geo_count = db.get_question_count(category="Geography")
    mc_count = db.get_question_count(question_type=QuestionType.MULTIPLE_CHOICE)

    print(f"\nStatistics:")
    print(f"Total questions: {total}")
    print(f"Geography questions: {geo_count}")
    print(f"Multiple choice questions: {mc_count}")

    db.close()
    print("\nAll tests passed!")
