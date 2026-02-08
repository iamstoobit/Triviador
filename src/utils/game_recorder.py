from __future__ import annotations
import json
from typing import List, Dict, Any
from pathlib import Path
from dataclasses import dataclass


@dataclass
class GameRecord:
    """Represents a single game record."""
    username: str
    score: int
    mode: str = "normal"  # "normal" or "endless"


class GameRecorder:
    """Handles saving and loading game records from a text file."""

    DEFAULT_GAMES_FILE = 'data/games.json'

    @staticmethod
    def save_game(username: str, score: int, mode: str = "normal", file_path: str = DEFAULT_GAMES_FILE) -> None:
        """
        Save a game record.

        Args:
            username: Player's username
            score: Final score achieved
            mode: Game mode ("normal" or "endless")
            file_path: Path to save games file
        """
        path = Path(file_path)

        # Create directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing games
        games = GameRecorder.load_all_games(file_path)

        # Add new game
        games.append({'username': username, 'score': score, 'mode': mode})

        # Save to file
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(games, f, indent=2, ensure_ascii=False)

    @staticmethod
    def load_all_games(file_path: str = DEFAULT_GAMES_FILE) -> List[Dict[str, Any]]:
        """
        Load all game records.

        Args:
            file_path: Path to games file

        Returns:
            List of game records (dictionaries with 'username' and 'score')
        """
        path = Path(file_path)

        if not path.exists():
            return []

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if not isinstance(data, list):
                    return []
                return data
        except (json.JSONDecodeError, IOError):
            return []

    @staticmethod
    def get_top_games(count: int = 10, mode: str = "normal", file_path: str = DEFAULT_GAMES_FILE) -> List[Dict[str, Any]]:
        """
        Get the top games by score for a specific mode.

        Args:
            count: Number of top games to return (default 10)
            mode: Game mode to filter by ("normal" or "endless")
            file_path: Path to games file

        Returns:
            List of top game records sorted by score descending
        """
        games = GameRecorder.load_all_games(file_path)

        # Filter by mode
        filtered_games = [g for g in games if g.get('mode', 'normal') == mode]

        # Sort by score descending
        sorted_games = sorted(filtered_games, key=lambda g: g['score'], reverse=True)

        return sorted_games[:count]

    @staticmethod
    def clear_games(file_path: str = DEFAULT_GAMES_FILE) -> None:
        """
        Clear all game records.

        Args:
            file_path: Path to games file
        """
        path = Path(file_path)

        if path.exists():
            with open(path, 'w', encoding='utf-8') as f:
                json.dump([], f)
