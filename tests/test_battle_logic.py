import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.game.state import (
    GameState,  Player, PlayerType, Region,
    FortificationLevel
)
from src.game.logic import GameLogic
from src.trivia.question import Question, QuestionType
from src.utils.config import GameConfig


class TestGameLogicBattle(unittest.TestCase):
    """Test battle resolution in GameLogic."""

    def setUp(self) -> None:
        """Set up test game logic."""
        self.state = GameState()
        self.config = GameConfig()
        self.logic = GameLogic(self.state, self.config)

        # Add two players
        self.player1 = Player(
            player_id=0,
            name="Attacker",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.player2 = Player(
            player_id=1,
            name="Defender",
            player_type=PlayerType.AI,
            color=(220, 57, 59)
        )
        self.state.add_player(self.player1)
        self.state.add_player(self.player2)

    def test_resolve_battle_attacker_wrong_defender_correct(self) -> None:
        """Test battle where attacker is wrong and defender is correct."""
        question = Question(
            id=1,
            text="What is 2+2?",
            category="Math",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="4",
            options=["3", "4", "5", "6"]
        )

        result = self.logic.resolve_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            attacker_answer="3",  # Wrong
            defender_answer="4"   # Correct
        )

        assert result.winner_id == 1  # Defender wins
        assert result.attacker_correct is False
        assert result.defender_correct is True
        assert result.defender_bonus_awarded is True

    def test_resolve_battle_attacker_correct_defender_wrong(self) -> None:
        """Test battle where attacker is correct and defender is wrong."""
        question = Question(
            id=1,
            text="What is 2+2?",
            category="Math",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="4",
            options=["3", "4", "5", "6"]
        )

        result = self.logic.resolve_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            attacker_answer="4",  # Correct
            defender_answer="3"   # Wrong
        )

        assert result.winner_id == 0  # Attacker wins
        assert result.attacker_correct is True
        assert result.defender_correct is False
        assert result.region_captured is True

    def test_resolve_battle_both_correct_tie(self) -> None:
        """Test battle where both answer correctly (tie, goes to open answer)."""
        question = Question(
            id=1,
            text="What is 2+2?",
            category="Math",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="4",
            options=["3", "4", "5", "6"]
        )

        result = self.logic.resolve_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            attacker_answer="4",  # Correct
            defender_answer="4"   # Correct
        )

        assert result.winner_id is None  # Tie - will be decided by open answer
        assert result.attacker_correct is True
        assert result.defender_correct is True

    def test_resolve_battle_both_wrong(self) -> None:
        """Test battle where both answer wrong (defender wins)."""
        question = Question(
            id=1,
            text="What is 2+2?",
            category="Math",
            question_type=QuestionType.MULTIPLE_CHOICE,
            correct_answer="4",
            options=["3", "4", "5", "6"]
        )

        result = self.logic.resolve_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            attacker_answer="3",  # Wrong
            defender_answer="5"   # Wrong
        )

        assert result.winner_id == 1  # Defender wins
        assert result.attacker_correct is False
        assert result.defender_correct is False
        assert result.defender_bonus_awarded is True

    def test_resolve_open_answer_attacker_closer(self) -> None:
        """Test open answer battle where attacker's answer is closer."""
        question = Question(
            id=1,
            text="Estimate pi:",
            category="Math",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer=3.14159,
            options=[]
        )

        result = self.logic.resolve_open_answer_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            answers={0: 3.14, 1: 3.0},  # Attacker closer
            answer_times={0: 5.0, 1: 10.0}
        )

        assert result.winner_id == 0  # Attacker wins
        assert result.region_captured is True

    def test_resolve_open_answer_defender_closer(self) -> None:
        """Test open answer battle where defender's answer is closer."""
        question = Question(
            id=1,
            text="Estimate pi:",
            category="Math",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer=3.14159,
            options=[]
        )

        result = self.logic.resolve_open_answer_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            answers={0: 3.0, 1: 3.14},  # Defender closer
            answer_times={0: 5.0, 1: 10.0}
        )

        assert result.winner_id == 1  # Defender wins
        assert result.defender_bonus_awarded is True

    def test_resolve_open_answer_same_closeness_attacker_faster(self) -> None:
        """Test open answer tie-breaker: same closeness, attacker faster."""
        question = Question(
            id=1,
            text="Estimate pi:",
            category="Math",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer=3.14159,
            options=[]
        )

        result = self.logic.resolve_open_answer_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            answers={0: 3.14, 1: 3.14},  # Same closeness
            answer_times={0: 5.0, 1: 10.0}  # Attacker faster
        )

        assert result.winner_id == 0  # Attacker wins (faster)

    def test_resolve_open_answer_ranking(self) -> None:
        """Test that open answer ranking is calculated correctly."""
        question = Question(
            id=1,
            text="Estimate X:",
            category="Math",
            question_type=QuestionType.OPEN_ANSWER,
            correct_answer=100.0,
            options=[]
        )

        result = self.logic.resolve_open_answer_battle(
            attacker_id=0,
            defender_id=1,
            region_id=1,
            question=question,
            answers={0: 99.0, 1: 110.0},  # Attacker closer
            answer_times={0: 5.0, 1: 5.0}
        )

        assert result.open_answer_ranking == [0, 1]
        assert result.open_answer_ranking[0] == 0  # Attacker is first


class TestGameLogicValidation(unittest.TestCase):
    """Test validation functions in GameLogic."""

    def setUp(self) -> None:
        """Set up test game logic."""
        self.state = GameState()
        self.config = GameConfig()
        self.logic = GameLogic(self.state, self.config)

        # Add player
        self.player = Player(
            player_id=0,
            name="Player",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.state.add_player(self.player)

    def test_can_attack_adjacent_region_owned_by_other(self) -> None:
        """Test attacking adjacent region owned by other player."""
        player2 = Player(
            player_id=1,
            name="Other",
            player_type=PlayerType.AI,
            color=(220, 57, 59)
        )
        self.state.add_player(player2)

        # Create owned region for player 1
        region1 = Region(
            region_id=1,
            name="My Region",
            position=(0, 0),
            owner_id=0,
            adjacent_regions=[2]
        )

        # Create owned region for player 2 (adjacent)
        region2 = Region(
            region_id=2,
            name="Enemy Region",
            position=(100, 0),
            owner_id=1,
            adjacent_regions=[1]
        )

        self.state.regions[1] = region1
        self.state.regions[2] = region2

        # Add region to player's controlled regions
        self.state.players[0].add_region(1)

        can_attack = self.logic.can_attack_region(0, 2)
        assert can_attack is True

    def test_cannot_attack_non_adjacent_region(self) -> None:
        """Test cannot attack non-adjacent region."""
        player2 = Player(
            player_id=1,
            name="Other",
            player_type=PlayerType.AI,
            color=(220, 57, 59)
        )
        self.state.add_player(player2)

        # Create regions
        region1 = Region(region_id=1, name="My", position=(0, 0), owner_id=0, adjacent_regions=[])
        region2 = Region(region_id=2, name="Enemy", position=(500, 0), owner_id=1, adjacent_regions=[])

        self.state.regions[1] = region1
        self.state.regions[2] = region2

        can_attack = self.logic.can_attack_region(0, 2)
        assert can_attack is False

    def test_cannot_attack_unowned_region(self) -> None:
        """Test cannot attack unowned region."""
        region = Region(region_id=1, name="Empty", position=(0, 0), adjacent_regions=[])
        self.state.regions[1] = region

        can_attack = self.logic.can_attack_region(0, 1)
        assert can_attack is False

    def test_can_fortify_own_unfortified_region(self) -> None:
        """Test can fortify own unfortified region."""
        region = Region(
            region_id=1,
            name="My Region",
            position=(0, 0),
            owner_id=0
        )
        self.state.regions[1] = region

        can_fortify = self.logic.can_fortify_region(0, 1)
        assert can_fortify is True

    def test_cannot_fortify_already_fortified_region(self) -> None:
        """Test cannot fortify already fortified region."""
        region = Region(
            region_id=1,
            name="Fortress",
            position=(0, 0),
            owner_id=0,
            fortification=FortificationLevel.FORTIFIED
        )
        self.state.regions[1] = region

        can_fortify = self.logic.can_fortify_region(0, 1)
        assert can_fortify is False

    def test_cannot_fortify_other_player_region(self) -> None:
        """Test cannot fortify other player's region."""
        region = Region(
            region_id=1,
            name="Enemy",
            position=(0, 0),
            owner_id=1
        )
        self.state.regions[1] = region

        can_fortify = self.logic.can_fortify_region(0, 1)
        assert can_fortify is False


class TestGameLogicCalculations(unittest.TestCase):
    """Test calculation functions in GameLogic."""

    def setUp(self) -> None:
        """Set up test game logic."""
        self.state = GameState()
        self.config = GameConfig()
        self.logic = GameLogic(self.state, self.config)

    def test_calculate_distance_three_four_five_triangle(self) -> None:
        """Test distance calculation with 3-4-5 triangle."""
        distance = self.logic.calculate_distance((0, 0), (3, 4))
        assert abs(distance - 5.0) < 0.001

    def test_calculate_distance_zero(self) -> None:
        """Test distance between same point is zero."""
        distance = self.logic.calculate_distance((5, 5), (5, 5))
        assert abs(distance - 0.0) < 0.001

    def test_calculate_distance_negative_coordinates(self) -> None:
        """Test distance with negative coordinates."""
        distance = self.logic.calculate_distance((-3, -4), (0, 0))
        assert abs(distance - 5.0) < 0.001

    def test_calculate_distance_large_numbers(self) -> None:
        """Test distance with large numbers."""
        distance = self.logic.calculate_distance((0, 0), (300, 400))
        assert abs(distance - 500.0) < 0.001


def run_tests() -> None:
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
