import sys
import os

# Add src to path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.trivia.database import TriviaDatabase
from src.trivia.question import Question, QuestionType

def populate_database():
    """Populate the database with sample questions."""
    db = TriviaDatabase()
    
    # Clear existing questions (optional - comment out to keep existing questions)
    # db.clear_all_questions()
    
    questions_to_add = [
        # GEOGRAPHY - Easy
        Question(
            id=1,
            text="What is the capital of France?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Paris",
            options=["Paris", "London", "Berlin", "Madrid"]
        ),
        Question(
            id=2,
            text="Which continent is the largest by area?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Asia",
            options=["Asia", "Africa", "Europe", "North America"]
        ),
        Question(
            id=3,
            text="What is the capital of Japan?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Tokyo",
            options=["Kyoto", "Osaka", "Tokyo", "Hiroshima"]
        ),
        Question(
            id=4,
            text="Which country has the most islands?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Sweden",
            options=["Norway", "Finland", "Sweden", "Denmark"]
        ),
        Question(
            id=5,
            text="What is the longest river in Africa?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Nile River",
            options=["Congo River", "Nile River", "Zambezi River", "Niger River"]
        ),
        
        # GEOGRAPHY - Medium
        Question(
            id=6,
            text="What is the capital of Kazakhstan?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Nur-Sultan",
            options=["Almaty", "Karaganda", "Nur-Sultan", "Aktobe"]
        ),
        Question(
            id=7,
            text="Which mountain range contains Mount Kilimanjaro?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Eastern Arc Mountains",
            options=["Atlas Mountains", "East African Rift", "Eastern Arc Mountains", "Rwenzori Mountains"]
        ),
        Question(
            id=8,
            text="In what year was the Panama Canal completed?",
            category="Geography",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="1914",
            options=[]
        ),
        
        # GEOGRAPHY - Hard
        Question(
            id=9,
            text="What is the capital of Djibouti?",
            category="Geography",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Djibouti City",
            options=["Arta", "Tadjoura", "Djibouti City", "Dikhil"]
        ),
        Question(
            id=10,
            text="How many countries are in South America?",
            category="Geography",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="12",
            options=[]
        ),
        
        # HISTORY - Easy
        Question(
            id=11,
            text="In what year did World War II end?",
            category="History",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="1945",
            options=["1943", "1944", "1945", "1946"]
        ),
        Question(
            id=12,
            text="Who was the first President of the United States?",
            category="History",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="George Washington",
            options=["Thomas Jefferson", "George Washington", "John Adams", "James Madison"]
        ),
        Question(
            id=13,
            text="In what year did the Titanic sink?",
            category="History",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="1912",
            options=["1910", "1911", "1912", "1913"]
        ),
        Question(
            id=14,
            text="Who wrote the Declaration of Independence?",
            category="History",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Thomas Jefferson",
            options=["Benjamin Franklin", "John Adams", "Thomas Jefferson", "James Madison"]
        ),
        
        # HISTORY - Medium
        Question(
            id=15,
            text="In what year did the American Civil War begin?",
            category="History",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="1861",
            options=["1859", "1860", "1861", "1862"]
        ),
        Question(
            id=16,
            text="Who was Julius Caesar's successor?",
            category="History",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Augustus",
            options=["Pompey", "Augustus", "Mark Antony", "Brutus"]
        ),
        Question(
            id=17,
            text="In what year did the Berlin Wall fall?",
            category="History",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="1989",
            options=[]
        ),
        
        # HISTORY - Hard
        Question(
            id=18,
            text="In what year was the Magna Carta signed?",
            category="History",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="1215",
            options=["1165", "1215", "1265", "1315"]
        ),
        Question(
            id=19,
            text="How many years did the Hundred Years' War last?",
            category="History",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="116",
            options=[]
        ),
        
        # SCIENCE - Easy
        Question(
            id=20,
            text="What is the chemical symbol for gold?",
            category="Science",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Au",
            options=["Go", "Gd", "Au", "Ag"]
        ),
        Question(
            id=21,
            text="How many bones are in the human body?",
            category="Science",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="206",
            options=["186", "196", "206", "216"]
        ),
        Question(
            id=22,
            text="What is the speed of light?",
            category="Science",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="300,000 km/s",
            options=["150,000 km/s", "250,000 km/s", "300,000 km/s", "400,000 km/s"]
        ),
        Question(
            id=23,
            text="What gas do plants absorb from the atmosphere?",
            category="Science",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Carbon dioxide",
            options=["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"]
        ),
        
        # SCIENCE - Medium
        Question(
            id=24,
            text="What is the atomic number of Carbon?",
            category="Science",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="6",
            options=["4", "5", "6", "7"]
        ),
        Question(
            id=25,
            text="How many planets are in our solar system?",
            category="Science",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="8",
            options=[]
        ),
        Question(
            id=26,
            text="In what year was DNA structure discovered?",
            category="Science",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="1953",
            options=["1950", "1952", "1953", "1955"]
        ),
        
        # SCIENCE - Hard
        Question(
            id=27,
            text="What is the name of the smallest unit of life?",
            category="Science",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Cell",
            options=["Atom", "Molecule", "Organism", "Cell"]
        ),
        Question(
            id=28,
            text="How long does it take for light from the Sun to reach Earth in minutes?",
            category="Science",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="8.3",
            options=[]
        ),
        
        # LITERATURE - Easy
        Question(
            id=29,
            text="Who wrote 'Romeo and Juliet'?",
            category="Literature",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="William Shakespeare",
            options=["Jane Austen", "William Shakespeare", "Charles Dickens", "Mark Twain"]
        ),
        Question(
            id=30,
            text="Who wrote 'Pride and Prejudice'?",
            category="Literature",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Jane Austen",
            options=["Jane Austen", "Charlotte Brontë", "Emily Dickinson", "George Eliot"]
        ),
        Question(
            id=31,
            text="What is the first Harry Potter book called?",
            category="Literature",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Harry Potter and the Philosopher's Stone",
            options=["Harry Potter and the Chamber of Secrets", "Harry Potter and the Philosopher's Stone", "Harry Potter and the Prisoner of Azkaban", "Harry Potter and the Goblet of Fire"]
        ),
        
        # LITERATURE - Medium
        Question(
            id=32,
            text="Who wrote 'The Great Gatsby'?",
            category="Literature",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="F. Scott Fitzgerald",
            options=["Ernest Hemingway", "F. Scott Fitzgerald", "John Steinbeck", "William Faulkner"]
        ),
        Question(
            id=33,
            text="In what year was 'The Lord of the Rings' first published?",
            category="Literature",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="1954",
            options=[]
        ),
        
        # SPORTS - Easy
        Question(
            id=34,
            text="How many players are on a basketball team on the court?",
            category="Sports",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="5",
            options=["3", "4", "5", "6"]
        ),
        Question(
            id=35,
            text="In tennis, what is a score of zero called?",
            category="Sports",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Love",
            options=["Nil", "Love", "Zero", "Blank"]
        ),
        Question(
            id=36,
            text="How many innings are in a baseball game?",
            category="Sports",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="9",
            options=["7", "8", "9", "10"]
        ),
        
        # SPORTS - Medium
        Question(
            id=37,
            text="How many stripes are on an American football field between the goal lines?",
            category="Sports",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="9",
            options=[]
        ),
        Question(
            id=38,
            text="What is the maximum break in snooker?",
            category="Sports",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="147",
            options=["140", "145", "147", "150"]
        ),
        
        # GENERAL KNOWLEDGE - Easy
        Question(
            id=39,
            text="How many continents are there?",
            category="General Knowledge",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="7",
            options=["5", "6", "7", "8"]
        ),
        Question(
            id=40,
            text="What is the smallest country in the world?",
            category="General Knowledge",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Vatican City",
            options=["Monaco", "Liechtenstein", "Vatican City", "San Marino"]
        ),
        
        # GENERAL KNOWLEDGE - Medium
        Question(
            id=41,
            text="How many strings does a standard violin have?",
            category="General Knowledge",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="4",
            options=["3", "4", "5", "6"]
        ),
        Question(
            id=42,
            text="In what year did the Eiffel Tower open?",
            category="General Knowledge",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="1889",
            options=[]
        ),
        
        # GENERAL KNOWLEDGE - Hard
        Question(
            id=43,
            text="What is the most spoken language in the world by native speakers?",
            category="General Knowledge",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="Mandarin Chinese",
            options=["English", "Spanish", "Mandarin Chinese", "Hindi"]
        ),
        Question(
            id=44,
            text="How many strings does a standard guitar have?",
            category="General Knowledge",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer="6",
            options=[]
        ),
    ]
    
    # Add questions to database
    added_count = 0
    for question in questions_to_add:
        try:
            # Check if question already exists to avoid duplicates
            existing = db.connection.execute(
                "SELECT id FROM questions WHERE text = ?",
                (question.text,)
            ).fetchone()
            
            if not existing:
                db.add_question(question, difficulty=get_difficulty_for_question(question.id))
                added_count += 1
                print(f"✓ Added: {question.text[:60]}...")
            else:
                print(f"⊘ Skipped (already exists): {question.text[:60]}...")
        except Exception as e:
            print(f"✗ Error adding question: {e}")
    
    print(f"\n✓ Successfully added {added_count} questions to the database!")
    
    # Verify
    total = db.connection.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
    print(f"Total questions in database: {total}")


def get_difficulty_for_question(question_id: int) -> int:
    """Map question ID to difficulty level (1=Easy, 2=Medium, 3=Hard)."""
    # Easy: 1-5, 11-14, 20-23, 29-31, 34-36, 39-40
    # Medium: 6-8, 15-17, 24-26, 32-33, 37-38, 41-42
    # Hard: 9-10, 18-19, 27-28, 43-44
    
    if question_id in [1, 2, 3, 4, 5, 11, 12, 13, 14, 20, 21, 22, 23, 29, 30, 31, 34, 35, 36, 39, 40]:
        return 1  # Easy
    elif question_id in [6, 7, 8, 15, 16, 17, 24, 25, 26, 32, 33, 37, 38, 41, 42]:
        return 2  # Medium
    else:  # 9, 10, 18, 19, 27, 28, 43, 44
        return 3  # Hard


if __name__ == "__main__":
    print("Populating Trivia Database with Sample Questions...")
    print("=" * 60)
    populate_database()
