from __future__ import annotations
import pygame
from typing import Dict, Optional, Tuple
from enum import Enum, auto
import time

from src.ui.menu_screen import MenuScreen
from src.ui.game_screen import GameScreen
from src.ui.question_screen import QuestionScreen
from src.ui.map_screen import MapScreen

from src.utils.config import GameConfig
from src.game.state import GameState, GamePhase
from src.trivia.question import Question


class ScreenType(Enum):
    """Types of screens in the game."""
    MENU = auto()
    GAME = auto()
    QUESTION = auto()
    MAP = auto()
    PAUSE = auto()


class ScreenManager:
    """
    Manages all game screens and handles drawing.
    """
    
    def __init__(self, screen: pygame.Surface, config: GameConfig):
        """
        Initialize screen manager.
        
        Args:
            screen: Pygame surface to draw on
            config: Game configuration
        """
        self.screen = screen
        self.config = config
        self.colors = config.colors
        self.current_screen: ScreenType = ScreenType.GAME
        
        # Fonts
        self._load_fonts()
        
        self.menu_screen = MenuScreen(screen, config)
        self.game_screen = GameScreen(screen, config)
        self.question_screen = QuestionScreen(screen, config)
        self.map_screen = MapScreen(screen, config)
        
        # UI state
        self.current_message: str = ""
        self.message_timer: float = 0
        self.message_duration: float = 2.0
        
    def _load_fonts(self) -> None:
        """Load fonts for the game."""
        self.fonts: Dict[str, pygame.font.Font] = {}
        
        try:
            # Try to load the configured font
            for size_name, size in self.config.font_sizes.items():
                self.fonts[size_name] = pygame.font.SysFont(self.config.font_name, size)
        except Exception:
            # Fallback to default font
            print(f"Warning: Could not load font '{self.config.font_name}', using default")
            for size_name, size in self.config.font_sizes.items():
                self.fonts[size_name] = pygame.font.Font(None, size)
    
    def draw(self, game_state: GameState) -> None:
        """
        Draw the current screen based on game state.
        
        Args:
            game_state: Current game state
        """
        # Clear screen
        self.screen.fill(self.colors.background)
        
        # Draw based on current screen
        if self.current_screen == ScreenType.MENU:
            self.menu_screen.draw()
        elif self.current_screen == ScreenType.GAME:
            self.game_screen.draw(game_state)
        elif self.current_screen == ScreenType.QUESTION:
            self.question_screen.draw(game_state)
        elif self.current_screen == ScreenType.MAP:
            self.map_screen.draw(game_state)
        
        # Draw message if any
        if self.current_message:
            self._draw_message(self.current_message)
    
    def update(self, game_state: GameState) -> None:
        """
        Update screen state.
        
        Args:
            game_state: Current game state
        """
        # Update message timer
        current_time = time.time()
        if self.current_message and current_time - self.message_timer > self.message_duration:
            self.current_message = ""
        
        # Update current screen based on game phase
        self._update_screen_type(game_state)
        
        # Update screen components
        if self.current_screen == ScreenType.MENU:
            self.menu_screen.update()
        elif self.current_screen == ScreenType.GAME:
            self.game_screen.update(game_state)
        elif self.current_screen == ScreenType.QUESTION:
            self.question_screen.update()
        elif self.current_screen == ScreenType.MAP:
            self.map_screen.update(game_state)
    
    def _update_screen_type(self, game_state: GameState) -> None:
        """Update current screen type based on game state."""
        if game_state.current_phase == GamePhase.SETUP:
            self.current_screen = ScreenType.MENU
        elif game_state.current_phase in [GamePhase.SPAWNING, GamePhase.OCCUPYING, GamePhase.TURN]:
            self.current_screen = ScreenType.GAME
        elif game_state.current_phase == GamePhase.BATTLE:
            self.current_screen = ScreenType.QUESTION
        elif game_state.current_phase == GamePhase.CAPITAL_ATTACK:
            self.current_screen = ScreenType.QUESTION
        elif game_state.current_phase == GamePhase.GAME_OVER:
            self.current_screen = ScreenType.GAME
    
    def show_message(self, message: str, duration: float = 2.0) -> None:
        """
        Show a temporary message on screen.
        
        Args:
            message: Message to display
            duration: How long to show the message (seconds)
        """
    
        self.current_message = message
        self.message_timer = time.time()
        self.message_duration = duration
    
    def draw_message(self, message: str) -> None:
        """Draw a message on screen."""
        font = self.fonts["body"]
        
        # Create message background
        text_surface = font.render(message, True, self.colors.text_primary)
        text_rect = text_surface.get_rect(center=(self.config.screen_width // 2, 50))
        
        # Draw background
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, self.colors.panel, bg_rect, border_radius=5)
        pygame.draw.rect(self.screen, self.colors.text_accent, bg_rect, 2, border_radius=5)
        
        # Draw text
        self.screen.blit(text_surface, text_rect)
    
    def show_question(self, question: Question, time_limit: int) -> None:
        """
        Show a question screen.
        
        Args:
            question: Question to display
            time_limit: Time limit in seconds
        """
        self.question_screen.set_question(question, time_limit)
        self.current_screen = ScreenType.QUESTION
    
    def show_open_question(self, question: Question, time_limit: int) -> None:
        """
        Show an open answer question screen.
        
        Args:
            question: Question to display
            time_limit: Time limit in seconds
        """
        self.question_screen.set_question(question, time_limit)
        self.current_screen = ScreenType.QUESTION
    
    def show_map(self) -> None:
        """Show the map screen."""
        self.current_screen = ScreenType.MAP
    
    def show_game(self) -> None:
        """Show the game screen."""
        self.current_screen = ScreenType.GAME
    
    def show_menu(self) -> None:
        """Show the menu screen."""
        self.current_screen = ScreenType.MENU
    
    def handle_event(self, event: pygame.event.Event, game_state: GameState) -> bool:
        """
        Handle a pygame event.
        
        Args:
            event: Pygame event
            game_state: Current game state
            
        Returns:
            True if event was handled, False otherwise
        """
        if self.current_screen == ScreenType.MENU:
            return self.menu_screen.handle_event(event)
        elif self.current_screen == ScreenType.GAME:
            return self.game_screen.handle_event(event, game_state)
        elif self.current_screen == ScreenType.QUESTION:
            return self.question_screen.handle_event(event, game_state)
        elif self.current_screen == ScreenType.MAP:
            return self.map_screen.handle_event(event, game_state)
        
        return False
    
    def get_region_at_position(self, pos: Tuple[int, int], 
                              game_state: GameState) -> Optional[int]:
        """
        Get region ID at mouse position.
        
        Args:
            pos: Mouse position (x, y)
            game_state: Current game state
            
        Returns:
            Region ID or None if no region at position
        """
        if self.current_screen == ScreenType.GAME:
            return self.game_screen.get_region_at_position(pos, game_state)
        elif self.current_screen == ScreenType.MAP:
            return self.map_screen.get_region_at_position(pos, game_state)
        
        return None


if __name__ == "__main__":
    print("=== Testing ScreenManager ===")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Create config
    from src.utils.config import GameConfig
    config = GameConfig(screen_width=800, screen_height=600)
    
    # Create screen manager
    manager = ScreenManager(screen, config)
    
    # Test message display
    manager.show_message("Test message")
    print("Screen manager created successfully")
    
    pygame.quit()
    print("All tests passed!")