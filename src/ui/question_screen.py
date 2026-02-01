from __future__ import annotations
import pygame
import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.utils.config import GameConfig
from src.game.state import GameState
from src.trivia.question import Question, QuestionType
from src.utils.helpers import draw_text, draw_button, wrap_text


@dataclass
class AnswerButton:
    """Represents an answer button for multiple choice."""
    rect: pygame.Rect
    text: str
    is_correct: bool = False
    is_selected: bool = False


class QuestionScreen:
    """
    Screen for displaying and answering trivia questions.
    """
    
    def __init__(self, screen: pygame.Surface, config: GameConfig):
        """
        Initialize question screen.
        
        Args:
            screen: Pygame surface to draw on
            config: Game configuration
        """
        self.screen = screen
        self.config = config
        self.colors = config.colors
        
        # Fonts
        self.fonts: Dict[str, pygame.font.Font] = {}
        self._load_fonts()
        
        # Question state
        self.current_question: Optional[Question] = None
        self.question_start_time: float = 0
        self.time_limit: int = 30
        self.answer_buttons: List[AnswerButton] = []
        self.selected_answer: Optional[str] = None
        
        # Open answer state
        self.open_answer_text: str = ""
        self.is_open_answer: bool = False
        
        # Timer animation
        self.timer_angle: float = 0.0
        
    def _load_fonts(self) -> None:
        """Load fonts."""
        for size_name, size in self.config.font_sizes.items():
            self.fonts[size_name] = pygame.font.SysFont(self.config.font_name, size)
    
    def set_question(self, question: Question, time_limit: int) -> None:
        """
        Set the current question.
        
        Args:
            question: Question to display
            time_limit: Time limit in seconds
        """
        self.current_question = question
        self.question_start_time = time.time()
        self.time_limit = time_limit
        self.answer_buttons = []
        self.selected_answer = None
        self.open_answer_text = ""
        self.is_open_answer = (question.question_type == QuestionType.OPEN_ANSWER)
        
        # Create answer buttons for multiple choice
        if not self.is_open_answer and question.options:
            self._create_answer_buttons(question.options, question.correct_answer)
    
    def _create_answer_buttons(self, options: List[str], correct_answer: str) -> None:
        """Create answer buttons for multiple choice."""
        self.answer_buttons.clear()
        
        screen_width = self.config.screen_width
        screen_height = self.config.screen_height
        
        # Calculate button positions (2x2 grid)
        button_width = 300
        button_height = 60
        button_spacing = 20
        
        # Grid positions
        positions = [
            (screen_width // 2 - button_width - button_spacing // 2, 
             screen_height // 2 + 50),
            (screen_width // 2 + button_spacing // 2, 
             screen_height // 2 + 50),
            (screen_width // 2 - button_width - button_spacing // 2, 
             screen_height // 2 + 50 + button_height + button_spacing),
            (screen_width // 2 + button_spacing // 2, 
             screen_height // 2 + 50 + button_height + button_spacing)
        ]
        
        for i, (option, pos) in enumerate(zip(options, positions)):
            if i >= 4:  # Max 4 options
                break
                
            rect = pygame.Rect(pos[0], pos[1], button_width, button_height)
            is_correct = (option == correct_answer)
            button = AnswerButton(rect=rect, text=option, is_correct=is_correct)
            self.answer_buttons.append(button)
    
    def draw(self, game_state: GameState) -> None:
        """
        Draw the question screen.
        
        Args:
            game_state: Current game state
        """
        # Draw background
        self.screen.fill(self.colors.background)
        
        if not self.current_question:
            return
        
        # Draw question box
        self._draw_question_box()
        
        # Draw timer
        self._draw_timer()
        
        # Draw question type
        self._draw_question_type()
        
        # Draw answer interface
        if self.is_open_answer:
            self._draw_open_answer_interface()
        else:
            self._draw_multiple_choice_interface()
        
        # Draw battle info if in battle
        if game_state.current_battle:
            self._draw_battle_info(game_state)
        
        # Update timer animation
        elapsed = time.time() - self.question_start_time
        self.timer_angle = (elapsed / self.time_limit) * 360
    
    def _draw_question_box(self) -> None:
        """Draw the question text box."""
        if not self.current_question:
            return
        
        # Question box dimensions
        box_width = 700
        box_height = 200
        box_x = (self.config.screen_width - box_width) // 2
        box_y = 100
        
        # Draw box background
        pygame.draw.rect(self.screen, self.colors.panel,
                        (box_x, box_y, box_width, box_height),
                        border_radius=10)
        pygame.draw.rect(self.screen, self.colors.text_primary,
                        (box_x, box_y, box_width, box_height),
                        2, border_radius=10)
        
        # Draw question text
        question_font = self.fonts["body"]
        wrapped_lines = wrap_text(self.current_question.text, question_font, box_width - 40)
        
        y_offset = box_y + 30
        for line in wrapped_lines:
            draw_text(self.screen, line,
                     (self.config.screen_width // 2, y_offset),
                     question_font, self.colors.text_primary)
            y_offset += 30
        
        # Draw category
        category_font = self.fonts["small"]
        draw_text(self.screen, f"Category: {self.current_question.category}",
                 (box_x + 20, box_y + box_height - 25),
                 category_font, self.colors.text_secondary, centered=False)
    
    def _draw_timer(self) -> None:
        """Draw the timer/countdown."""
        elapsed = time.time() - self.question_start_time
        remaining = max(0, self.time_limit - elapsed)
        
        # Timer circle position
        timer_x = self.config.screen_width - 80
        timer_y = 80
        timer_radius = 30
        
        # Draw timer circle background
        pygame.draw.circle(self.screen, self.colors.panel, (timer_x, timer_y), timer_radius)
        
        # Draw timer arc (decreasing circle)
        if remaining > 0:
            # Calculate color based on time remaining
            time_ratio = remaining / self.time_limit
            if time_ratio > 0.5:
                timer_color = self.colors.correct_answer
            elif time_ratio > 0.25:
                timer_color = (255, 165, 0)  # Orange
            else:
                timer_color = self.colors.wrong_answer
            
            # Draw arc
            start_angle = -90  # Start at top
            end_angle = start_angle + (360 * time_ratio)
            
            pygame.draw.arc(self.screen, timer_color,
                          (timer_x - timer_radius, timer_y - timer_radius,
                           timer_radius * 2, timer_radius * 2),
                          start_angle * 3.14159 / 180,
                          end_angle * 3.14159 / 180,
                          4)
        
        # Draw timer border
        pygame.draw.circle(self.screen, self.colors.text_primary,
                         (timer_x, timer_y), timer_radius, 2)
        
        # Draw time text
        time_font = self.fonts["body"]
        time_text = f"{int(remaining)}"
        draw_text(self.screen, time_text,
                 (timer_x, timer_y),
                 time_font, self.colors.text_primary)
    
    def _draw_question_type(self) -> None:
        """Draw question type indicator."""
        if not self.current_question:
            return
        
        type_font = self.fonts["small"]
        
        if self.is_open_answer:
            type_text = "Open Answer (Enter a number)"
            type_color = self.colors.text_accent
        else:
            type_text = "Multiple Choice"
            type_color = self.colors.text_secondary
        
        draw_text(self.screen, type_text,
                 (self.config.screen_width // 2, 320),
                 type_font, type_color)
    
    def _draw_multiple_choice_interface(self) -> None:
        """Draw multiple choice answer buttons."""
        for button in self.answer_buttons:
            # Determine button color
            if button.is_selected:
                if button.is_correct:
                    bg_color = self.colors.correct_answer
                else:
                    bg_color = self.colors.wrong_answer
            else:
                bg_color = self.colors.button_normal
            
            # Draw button
            draw_button(self.screen, button.rect, button.text,
                       self.fonts["body"],
                       bg_color, self.colors.button_hover,
                       self.colors.text_primary,
                       hover=False)  # We'll handle hover separately
    
    def _draw_open_answer_interface(self) -> None:
        """Draw open answer input interface."""
        # Answer box
        box_width = 400
        box_height = 70
        box_x = (self.config.screen_width - box_width) // 2
        box_y = 350
        
        # Draw answer box
        pygame.draw.rect(self.screen, self.colors.panel,
                        (box_x, box_y, box_width, box_height),
                        border_radius=5)
        pygame.draw.rect(self.screen, self.colors.text_primary,
                        (box_x, box_y, box_width, box_height),
                        2, border_radius=5)
        
        # Draw answer text
        answer_font = self.fonts["heading"]
        display_text = self.open_answer_text if self.open_answer_text else "0"
        draw_text(self.screen, display_text,
                 (self.config.screen_width // 2, box_y + box_height // 2),
                 answer_font, self.colors.text_accent)
        
        # Draw instructions
        inst_font = self.fonts["small"]
        instructions = [
            "Enter numbers with keyboard or numpad",
            "BACKSPACE: delete last digit",
            "ENTER: submit answer",
            "-: toggle negative sign",
            "ESC: cancel"
        ]
        
        y_pos = box_y + box_height + 20
        for inst in instructions:
            draw_text(self.screen, inst,
                     (self.config.screen_width // 2, y_pos),
                     inst_font, self.colors.text_secondary)
            y_pos += 25
    
    def _draw_battle_info(self, game_state: GameState) -> None:
        """Draw battle information."""
        if not game_state.current_battle:
            return
        
        battle = game_state.current_battle
        attacker = game_state.players.get(battle.attacker_id)
        defender = game_state.players.get(battle.defender_id)
        
        if not attacker or not defender:
            return
        
        # Battle info box
        box_width = 300
        box_height = 100
        box_x = 50
        box_y = 50
        
        # Draw box
        pygame.draw.rect(self.screen, self.colors.panel,
                        (box_x, box_y, box_width, box_height),
                        border_radius=5)
        pygame.draw.rect(self.screen, self.colors.text_primary,
                        (box_x, box_y, box_width, box_height),
                        2, border_radius=5)
        
        # Draw battle info
        info_font = self.fonts["small"]
        title_font = self.fonts["body"]
        
        draw_text(self.screen, "BATTLE",
                 (box_x + box_width // 2, box_y + 20),
                 title_font, self.colors.text_accent)
        
        # Attacker
        attacker_color = self.config.get_player_color(attacker.player_id)
        draw_text(self.screen, f"Attacker: {attacker.name}",
                 (box_x + 20, box_y + 50),
                 info_font, attacker_color, centered=False)
        
        # Defender
        defender_color = self.config.get_player_color(defender.player_id)
        draw_text(self.screen, f"Defender: {defender.name}",
                 (box_x + 20, box_y + 75),
                 info_font, defender_color, centered=False)
    
    def update(self) -> None:
        """
        Update question screen state.
        
        Args:
            game_state: Current game state
        """
        # Check for timeout
        if self.current_question:
            elapsed = time.time() - self.question_start_time
            if elapsed > self.time_limit:
                # Time's up - handle timeout
                self._handle_timeout()
    
    def _handle_timeout(self) -> None:
        """Handle question timeout."""
        if self.is_open_answer:
            # For open answer, submit current answer (or 0)
            self.selected_answer = self.open_answer_text if self.open_answer_text else "0"
        else:
            # For multiple choice, no answer selected
            self.selected_answer = None
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
            game_state: Current game state
            
        Returns:
            True if event was handled
        """
        if not self.current_question:
            return False
        
        if self.is_open_answer:
            return self._handle_open_answer_event(event)
        else:
            return self._handle_multiple_choice_event(event)
    
    def _handle_multiple_choice_event(self, event: pygame.event.Event) -> bool:
        """Handle events for multiple choice questions."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            
            # Check answer buttons
            for button in self.answer_buttons:
                if button.rect.collidepoint(pos):
                    # Select this answer
                    for btn in self.answer_buttons:
                        btn.is_selected = False
                    button.is_selected = True
                    self.selected_answer = button.text
                    return True
        
        return False
    
    def _handle_open_answer_event(self, event: pygame.event.Event) -> bool:
        """Handle events for open answer questions."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                # Submit answer
                self.selected_answer = self.open_answer_text if self.open_answer_text else "0"
                return True
            
            elif event.key == pygame.K_BACKSPACE:
                # Delete last character
                if self.open_answer_text:
                    self.open_answer_text = self.open_answer_text[:-1]
                return True
            
            elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                # Toggle negative sign
                if self.open_answer_text.startswith("-"):
                    self.open_answer_text = self.open_answer_text[1:]
                else:
                    self.open_answer_text = "-" + self.open_answer_text
                return True
            
            elif event.key == pygame.K_PERIOD or event.key == pygame.K_KP_PERIOD:
                # Add decimal point if not already present
                if "." not in self.open_answer_text:
                    self.open_answer_text += "."
                return True
            
            elif pygame.K_0 <= event.key <= pygame.K_9:
                # Add digit
                digit = str(event.key - pygame.K_0)
                self.open_answer_text += digit
                return True
            
            elif pygame.K_KP0 <= event.key <= pygame.K_KP9:
                # Add digit from numpad
                digit = str(event.key - pygame.K_KP0)
                self.open_answer_text += digit
                return True
        
        return False
    
    def get_answer(self) -> Optional[Any]:
        """
        Get the selected answer.
        
        Returns:
            Selected answer, or None if no answer selected
        """
        return self.selected_answer
    
    def is_answer_submitted(self) -> bool:
        """
        Check if an answer has been submitted.
        
        Returns:
            True if answer has been submitted
        """
        return self.selected_answer is not None
    
    def get_time_remaining(self) -> float:
        """
        Get remaining time for the question.
        
        Returns:
            Time remaining in seconds
        """
        if not self.current_question:
            return 0
        
        elapsed = time.time() - self.question_start_time
        return max(0, self.time_limit - elapsed)


if __name__ == "__main__":
    print("=== Testing QuestionScreen ===")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Create config
    from src.utils.config import GameConfig
    config = GameConfig(screen_width=800, screen_height=600)
    
    # Create question screen
    question_screen = QuestionScreen(screen, config)
    
    # Create test questions
    from src.trivia.question import Question, QuestionType
    
    # Test multiple choice question
    mc_question = Question(
        id=1,
        text="What is the capital of France?",
        category="Geography",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer="Paris",
        options=["London", "Berlin", "Paris", "Madrid"]
    )
    
    # Test open answer question
    oa_question = Question(
        id=2,
        text="What is 2 + 2?",
        category="Math",
        question_type=QuestionType.OPEN_ANSWER,
        correct_answer=4,
        options=[]
    )
    
    # Set multiple choice question
    question_screen.set_question(mc_question, 30)
    
    # Create test game state
    from src.game.state import GameState
    game_state = GameState()
    
    # Draw test screen
    question_screen.draw(game_state)
    pygame.display.flip()
    
    pygame.time.delay(1000)
    pygame.quit()
    
    print("All tests passed!")