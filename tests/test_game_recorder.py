import sys
import os
import unittest
import tempfile
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.game_recorder import GameRecorder


class TestGameRecorder(unittest.TestCase):
    """Test the GameRecorder class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_games.json")

    def tearDown(self) -> None:
        """Clean up test files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_game_creates_file(self) -> None:
        """Test that saving a game creates the file."""
        GameRecorder.save_game("Player1", 100, "normal", self.test_file)

        assert os.path.exists(self.test_file)

    def test_save_game_normal_mode(self) -> None:
        """Test saving a game in normal mode."""
        GameRecorder.save_game("TestPlayer", 250, "normal", self.test_file)

        with open(self.test_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]['username'] == "TestPlayer"
        assert data[0]['score'] == 250
        assert data[0]['mode'] == "normal"

    def test_save_game_endless_mode(self) -> None:
        """Test saving a game in endless mode."""
        GameRecorder.save_game("Player2", 500, "endless", self.test_file)

        with open(self.test_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 1
        assert data[0]['mode'] == "endless"

    def test_save_multiple_games(self) -> None:
        """Test saving multiple games appends correctly."""
        GameRecorder.save_game("Player1", 100, "normal", self.test_file)
        GameRecorder.save_game("Player2", 200, "normal", self.test_file)
        GameRecorder.save_game("Player3", 150, "endless", self.test_file)

        with open(self.test_file, 'r') as f:
            data = json.load(f)

        assert len(data) == 3
        assert data[0]['username'] == "Player1"
        assert data[1]['username'] == "Player2"
        assert data[2]['username'] == "Player3"

    def test_load_all_games_empty_file(self) -> None:
        """Test loading from non-existent file returns empty list."""
        games = GameRecorder.load_all_games(self.test_file)
        assert games == []

    def test_load_all_games(self) -> None:
        """Test loading all games."""
        GameRecorder.save_game("P1", 100, "normal", self.test_file)
        GameRecorder.save_game("P2", 200, "normal", self.test_file)

        games = GameRecorder.load_all_games(self.test_file)

        assert len(games) == 2
        assert games[0]['username'] == "P1"
        assert games[1]['username'] == "P2"

    def test_load_all_games_invalid_json(self) -> None:
        """Test loading from invalid JSON returns empty list."""
        # Write invalid JSON
        with open(self.test_file, 'w') as f:
            f.write("{ invalid }")

        games = GameRecorder.load_all_games(self.test_file)
        assert games == []

    def test_load_all_games_not_list(self) -> None:
        """Test loading when JSON is not a list returns empty list."""
        # Write non-list JSON
        with open(self.test_file, 'w') as f:
            json.dump({"games": []}, f)

        games = GameRecorder.load_all_games(self.test_file)
        assert games == []

    def test_get_top_games_normal_mode(self) -> None:
        """Test getting top games in normal mode."""
        GameRecorder.save_game("P1", 100, "normal", self.test_file)
        GameRecorder.save_game("P2", 500, "normal", self.test_file)
        GameRecorder.save_game("P3", 300, "normal", self.test_file)
        GameRecorder.save_game("P4", 250, "endless", self.test_file)

        top = GameRecorder.get_top_games(count=10, mode="normal", file_path=self.test_file)

        assert len(top) == 3
        assert top[0]['username'] == "P2"  # 500
        assert top[0]['score'] == 500
        assert top[1]['username'] == "P3"  # 300
        assert top[2]['username'] == "P1"  # 100

    def test_get_top_games_endless_mode(self) -> None:
        """Test getting top games in endless mode."""
        GameRecorder.save_game("P1", 100, "normal", self.test_file)
        GameRecorder.save_game("P2", 350, "endless", self.test_file)
        GameRecorder.save_game("P3", 200, "endless", self.test_file)

        top = GameRecorder.get_top_games(count=10, mode="endless", file_path=self.test_file)

        assert len(top) == 2
        assert top[0]['username'] == "P2"
        assert top[0]['score'] == 350
        assert top[1]['username'] == "P3"
        assert top[1]['score'] == 200

    def test_get_top_games_limit(self) -> None:
        """Test that get_top_games limits results."""
        for i in range(15):
            GameRecorder.save_game(f"Player{i}", i * 10, "normal", self.test_file)

        top5 = GameRecorder.get_top_games(count=5, mode="normal", file_path=self.test_file)

        assert len(top5) == 5
        assert top5[0]['score'] == 140  # Highest

    def test_get_top_games_empty(self) -> None:
        """Test getting top games when no games exist."""
        top = GameRecorder.get_top_games(count=10, mode="normal", file_path=self.test_file)
        assert top == []

    def test_get_top_games_wrong_mode(self) -> None:
        """Test getting top games in mode with no games."""
        GameRecorder.save_game("P1", 100, "normal", self.test_file)

        top = GameRecorder.get_top_games(count=10, mode="endless", file_path=self.test_file)
        assert top == []

    def test_clear_games(self) -> None:
        """Test clearing all games."""
        GameRecorder.save_game("P1", 100, "normal", self.test_file)
        GameRecorder.save_game("P2", 200, "normal", self.test_file)

        GameRecorder.clear_games(self.test_file)

        games = GameRecorder.load_all_games(self.test_file)
        assert games == []

    def test_clear_games_nonexistent_file(self) -> None:
        """Test clearing non-existent file doesn't fail."""
        # Should not raise an error
        GameRecorder.clear_games(self.test_file)

    def test_save_game_default_mode(self) -> None:
        """Test that save_game defaults to 'normal' mode."""
        GameRecorder.save_game("Player", 100, file_path=self.test_file)

        with open(self.test_file, 'r') as f:
            data = json.load(f)

        assert data[0]['mode'] == "normal"

    def test_get_top_games_default_mode(self) -> None:
        """Test that get_top_games defaults to 'normal' mode."""
        GameRecorder.save_game("P1", 100, "normal", self.test_file)
        GameRecorder.save_game("P2", 200, "endless", self.test_file)

        # Not specifying mode should get normal
        top = GameRecorder.get_top_games(count=10, file_path=self.test_file)

        assert len(top) == 1
        assert top[0]['username'] == "P1"

    def test_game_record_with_special_characters(self) -> None:
        """Test saving game with special characters in username."""
        GameRecorder.save_game("Müller_123", 100, "normal", self.test_file)

        games = GameRecorder.load_all_games(self.test_file)
        assert games[0]['username'] == "Müller_123"

    def test_large_scores(self) -> None:
        """Test saving and retrieving large scores."""
        GameRecorder.save_game("HighScorer", 1000000, "normal", self.test_file)

        games = GameRecorder.load_all_games(self.test_file)
        assert games[0]['score'] == 1000000


def run_tests() -> None:
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
