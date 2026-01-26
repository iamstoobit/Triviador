"""
src/utils/config.py - Game configuration
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Tuple, List
import random
import json
import os
from enum import Enum


class Difficulty(Enum):
    """Game difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class CategorySelectionMode(Enum):
    """How categories are selected."""
    INCLUDE = "include"  # Only selected categories are included
    EXCLUDE = "exclude"  # Selected categories are excluded


@dataclass
class ColorScheme:
    """Color scheme for the game UI."""
    
    # Background colors
    background: Tuple[int, int, int] = (240, 240, 245)
    panel: Tuple[int, int, int] = (255, 255, 255)
    card: Tuple[int, int, int] = (250, 250, 252)
    
    # Text colors
    text_primary: Tuple[int, int, int] = (33, 33, 33)
    text_secondary: Tuple[int, int, int] = (117, 117, 117)
    text_accent: Tuple[int, int, int] = (25, 118, 210)
    
    # Player colors (max 4 players total: 1 human + 3 AI)
    player_colors: List[Tuple[int, int, int]] = field(default_factory=lambda: [
        (25, 118, 210),    # Blue - Human player (always player 0)
        (220, 57, 59),     # Red - AI 1
        (51, 153, 51),     # Green - AI 2
        (153, 51, 153),    # Purple - AI 3
    ])
    
    # UI elements
    button_normal: Tuple[int, int, int] = (25, 118, 210)
    button_hover: Tuple[int, int, int] = (21, 101, 192)
    button_pressed: Tuple[int, int, int] = (13, 71, 161)
    button_disabled: Tuple[int, int, int] = (200, 200, 200)
    
    # Game colors
    territory_neutral: Tuple[int, int, int] = (200, 200, 210)
    territory_border: Tuple[int, int, int] = (150, 150, 160)
    territory_human: Tuple[int, int, int] = (25, 118, 210)     # Matches player 1
    territory_ai1: Tuple[int, int, int] = (220, 57, 59)        # AI 1
    territory_ai2: Tuple[int, int, int] = (51, 153, 51)        # AI 2
    territory_ai3: Tuple[int, int, int] = (153, 51, 153)       # AI 3
    highlight: Tuple[int, int, int] = (255, 235, 59)
    selected: Tuple[int, int, int] = (255, 193, 7)  # Amber for selected region
    correct_answer: Tuple[int, int, int] = (76, 175, 80)
    wrong_answer: Tuple[int, int, int] = (244, 67, 54)
    capital_highlight: Tuple[int, int, int] = (255, 215, 0)  # Gold for capitals
    
    # Map visualization
    region_border: Tuple[int, int, int] = (100, 100, 120)
    region_text: Tuple[int, int, int] = (33, 33, 33)
    region_points_bg: Tuple[int, int, int, int] = (255, 255, 255, 180)


@dataclass
class GameConfig:
    """
    Main game configuration matching all clarified rules.
    """
    
    # ===== WINDOW SETTINGS =====
    screen_width: int = 1280
    screen_height: int = 720
    fullscreen: bool = False
    fps: int = 60
    
    # ===== PLAYER SETTINGS =====
    ai_count: int = 2  # Number of AI opponents
    
    # ===== DIFFICULTY =====
    difficulty: Difficulty = Difficulty.MEDIUM
    
    # ===== CATEGORIES =====
    available_categories: List[str] = field(default_factory=lambda: [
        "Geography", "History", "Science", "Entertainment", 
        "Sports", "Art", "Literature", "Technology", "Movies",
        "Music", "General Knowledge", "Pop Culture"
    ])

    selected_categories: List[str] = field(default_factory=lambda: [
        "Geography", "History", "Science", "Entertainment"
    ])

    category_mode: CategorySelectionMode = CategorySelectionMode.INCLUDE
    
    # ===== MAP SETTINGS =====
    min_regions: int = 16
    max_regions: int = 32
    region_count: int = 24  # Default middle ground
    min_capital_distance: int = 2  # Capitals cannot spawn adjacent
    
    # ===== TURN SETTINGS =====
    min_turns_per_player: int = 5
    max_turns_per_player: int = 20
    turns_per_player: int = 10  # Default middle ground
    
    # ===== POINT VALUES =====
    capital_points: int = 1000  # Capital value
    initial_region_points: int = 500  # Uncaptured regions
    captured_region_points: int = 800  # After battle capture
    
    # ===== BATTLE SETTINGS =====
    defense_bonus: int = 300  # Points for successful defense
    
    # ===== CAPITAL SETTINGS =====
    capital_max_hp: int = 3  # Takes 3 hits to capture (Rule 3)
    capital_hp_regeneration_turns: int = 3  # Regenerate 1 HP after 3 consecutive turns not attacked
    
    # ===== FORTIFICATION SETTINGS =====
    max_fortification_level: int = 1  # Can only fortify once
    
    # ===== INITIAL SETTINGS =====
    starting_score: int = 1000  # Each player starts with capital points
    
    # ===== AI SETTINGS =====
    ai_trivia_accuracy: Dict[Difficulty, float] = field(default_factory=lambda: {
        Difficulty.EASY: 0.4,    # 40% correct
        Difficulty.MEDIUM: 0.65, # 65% correct
        Difficulty.HARD: 0.85,   # 85% correct
    })

    ai_open_answer_accuracy: Dict[Difficulty, float] = field(default_factory=lambda: {
        Difficulty.EASY: 0.45,    # 45% within 10% of correct answer
        Difficulty.MEDIUM: 0.6,  # 60% within 10% of correct answer
        Difficulty.HARD: 0.85,    # 85% within 10% of correct answer
    })
    
    ai_think_time_ranges: Dict[Difficulty, Tuple[int, int]] = field(default_factory=lambda: {
        Difficulty.EASY: (3000, 5000),    # 3-5 seconds
        Difficulty.MEDIUM: (2000, 4000),  # 2-4 seconds
        Difficulty.HARD: (1000, 3000),    # 1-3 seconds
    })
    
    # ===== QUESTION TIMING =====
    multiple_choice_time: int = 30  # seconds for multiple choice questions
    open_answer_time: int = 45  # seconds for open answer questions
    
    # ===== UI SETTINGS =====
    colors: ColorScheme = field(default_factory=ColorScheme)
    font_name: str = "Arial"
    font_sizes: Dict[str, int] = field(default_factory=lambda: {
        "title": 48,
        "heading": 32,
        "subheading": 24,
        "body": 18,
        "small": 14,
        "tiny": 12,
    })
    
    # ===== PATHS =====
    data_dir: str = "data"
    assets_dir: str = "assets"
    config_dir: str = "config"
    questions_db: str = "questions.db"
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        # Validate AI count
        self.ai_count = max(1, min(self.ai_count, 3))
        
        # Validate region count
        self.region_count = max(self.min_regions, min(self.region_count, self.max_regions))
        
        # Validate turns per player
        self.turns_per_player = max(self.min_turns_per_player, 
                                   min(self.turns_per_player, self.max_turns_per_player))
        
        # Validate capital distance
        self.min_capital_distance = max(1, self.min_capital_distance)
        
        # Ensure total players doesn't exceed available colors
        total_players = 1 + self.ai_count
        if total_players > len(self.colors.player_colors):
            raise ValueError(f"Maximum {len(self.colors.player_colors)} players supported")
        
        # Ensure categories are subset of available
        for cat in self.selected_categories:
            if cat not in self.available_categories:
                raise ValueError(f"Category '{cat}' not in available categories")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(os.path.join(self.assets_dir, "images"), exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
    
    def get_included_categories(self) -> List[str]:
        """
        Get list of included categories based on selection mode.
        
        Returns:
            List of category names that should be included in questions
        """
        if self.category_mode == CategorySelectionMode.INCLUDE:
            return self.selected_categories.copy()
        else:  # EXCLUDE mode
            return [cat for cat in self.available_categories 
                   if cat not in self.selected_categories]
    
    def get_total_players(self) -> int:
        """
        Get total number of players (human + AI).
        
        Returns:
            Total player count
        """
        return 1 + self.ai_count
    
    def get_player_color(self, player_id: int) -> Tuple[int, int, int]:
        """
        Get color for a player by ID.
        
        Args:
            player_id: 0 = human, 1+ = AI
            
        Returns:
            RGB tuple for the player's color
        """
        if 0 <= player_id < len(self.colors.player_colors):
            return self.colors.player_colors[player_id]
        return self.colors.player_colors[0]
    
    def get_ai_accuracy(self, question_type: str = "multiple_choice") -> float:
        """
        Get AI accuracy based on current difficulty and question type.
        
        Args:
            question_type: "multiple_choice" or "open_answer"
            
        Returns:
            Accuracy percentage (0.0 to 1.0)
        """
        if question_type == "open_answer":
            return self.ai_open_answer_accuracy.get(self.difficulty, 0.5)
        return self.ai_trivia_accuracy.get(self.difficulty, 0.65)
    
    def get_ai_think_time(self) -> int:
        """
        Get AI think time in milliseconds based on difficulty.
        
        Returns:
            Think time in milliseconds
        """
        time_range = self.ai_think_time_ranges.get(self.difficulty, (1500, 2500))
        return random.randint(time_range[0], time_range[1])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        return {
            'ai_count': self.ai_count,
            'difficulty': self.difficulty.value,
            'selected_categories': self.selected_categories,
            'category_mode': self.category_mode.value,
            'region_count': self.region_count,
            'turns_per_player': self.turns_per_player,
            'screen_width': self.screen_width,
            'screen_height': self.screen_height,
            'fullscreen': self.fullscreen,
            'fps': self.fps,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameConfig:
        """Create configuration from dictionary."""
        config = cls()
        
        # Update from data
        if 'ai_count' in data:
            config.ai_count = data['ai_count']
        if 'difficulty' in data:
            config.difficulty = Difficulty(data['difficulty'])
        if 'selected_categories' in data:
            config.selected_categories = data['selected_categories']
        if 'category_mode' in data:
            config.category_mode = CategorySelectionMode(data['category_mode'])
        if 'region_count' in data:
            config.region_count = data['region_count']
        if 'turns_per_player' in data:
            config.turns_per_player = data['turns_per_player']
        if 'screen_width' in data:
            config.screen_width = data['screen_width']
        if 'screen_height' in data:
            config.screen_height = data['screen_height']
        if 'fullscreen' in data:
            config.fullscreen = data['fullscreen']
        if 'fps' in data:
            config.fps = data['fps']
        
        config.__post_init__()  # Re-validate
        return config
    
    def save(self, filename: str = "game_settings.json") -> None:
        """Save configuration to file."""
        filepath = os.path.join(self.config_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, filename: str = "game_settings.json") -> "GameConfig":
        """Load configuration from file."""
        filepath = os.path.join(cls().config_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return cls.from_dict(data)
        return cls()


if __name__ == "__main__":
    # Test the final configuration
    config = GameConfig()
    print("=== FINAL Game Configuration ===")
    print(f"Total players: {config.get_total_players()} (1 human + {config.ai_count} AI)")
    print(f"Difficulty: {config.difficulty.value}")
    print(f"Category mode: {config.category_mode.value}")
    print(f"Included categories: {', '.join(config.get_included_categories())}")
    print(f"Regions: {config.region_count} (capitals min distance: {config.min_capital_distance})")
    print(f"Turns per player: {config.turns_per_player}")
    print(f"Starting score: {config.starting_score}")
    print(f"Capital: {config.capital_points} pts, {config.capital_max_hp} HP")
    print(f"Region points: {config.initial_region_points} (initial), {config.captured_region_points} (battle capture)")
    print(f"Defense bonus: {config.defense_bonus} pts")
    print(f"AI accuracy: {config.get_ai_accuracy()*100:.1f}% (MC), {config.get_ai_accuracy('open_answer')*100:.1f}% (OA)")
    
    # Save default config
    config.save()
    print(f"\nDefault configuration saved to: {config.config_dir}/game_settings.json")