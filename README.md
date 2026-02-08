# Triviador

A trivia-based strategy game built with Python and Pygame. Conquer territories by answering trivia questions correctly.

## Installation

### Requirements
- Python 3.8 or higher

### Setup

1. Clone or download the repository
2. Open a terminal in the project directory
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Run the Game

```
python main.py
```

## How to Play

- **Custom name**: choose your name from the setup screen
- **Configure game settings**: AI opponents, difficulty, categories, regions, and turns
- **"Start Game"**: begin classic mode with standard Triviador rules
- **"Endless Mode"**: survival style with endless questions until first mistake
- **Special rounds** - points earned are doubled
- **Leaderboards** - separate rankings for classic and endless modes

## Game Modes

- **Classic Mode**: Turn-based territory conquest with strategic gameplay
- **Endless Mode**: Answer questions until you get one wrong

## Adding Questions

### Edit the Question File

1. Open `data/questions.json`
2. Add your question at the end of the list (before the closing `]`)
3. Use the templates below

### Multiple Choice Question Template

```json
{
  "id": 21,
  "text": "What is the capital of France?",
  "category": "Geography",
  "question_type": "MULTIPLE_CHOICE",
  "correct_answer": "Paris",
  "options": ["London", "Berlin", "Paris", "Madrid"],
  "difficulty": 2
}
```

### Open Answer Question Template

```json
{
  "id": 22,
  "text": "What is the approximate value of pi?",
  "category": "Math",
  "question_type": "OPEN_ANSWER",
  "correct_answer": 3.14159,
  "options": [],
  "difficulty": 3
}
```

### Field Descriptions

- **id**: Unique question number (increment from previous)
- **text**: The question text
- **category**: Question category (e.g., Geography, Math, History)
- **question_type**: Either `"MULTIPLE_CHOICE"` or `"OPEN_ANSWER"`
- **correct_answer**: String for MC questions, number for open answer
- **options**: List of 4 answer choices for MC questions (empty list for open answer)
- **difficulty**: Number from 1 (easiest) to 5 (hardest)

### Important Notes

- Make sure each question has a unique `id`
- For multiple choice, the `correct_answer` must be one of the options
- Add a comma after each question (except the last one)
- Keep the entire list within the outer brackets `[]`