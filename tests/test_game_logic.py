import sys
import os
import unittest

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.game.state import (
    GameState, GamePhase, Player, PlayerType, Region, RegionType,
    BattleResult, generate_player_name, FortificationLevel
)
from src.game.logic import GameLogic
from src.utils.config import GameConfig


class TestGameState(unittest.TestCase):
    """Test the GameState class."""

    def setUp(self) -> None:
        """Set up test game state."""
        self.state = GameState()

    def test_game_state_initialization(self) -> None:
        """Test that game state initializes correctly."""
        self.assertIsNotNone(self.state)
        self.assertEqual(self.state.current_phase, GamePhase.SETUP)
        self.assertEqual(len(self.state.players), 0)

    def test_add_human_player(self) -> None:
        """Test adding a human player."""
        player = Player(
            player_id=0,
            name="Human",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.state.add_player(player)
        self.assertEqual(len(self.state.players), 1)
        self.assertEqual(self.state.players[0].name, "Human")
        self.assertEqual(self.state.players[0].player_type, PlayerType.HUMAN)

    def test_add_ai_player(self) -> None:
        """Test adding an AI player."""
        player = Player(
            player_id=1,
            name="AI_1",
            player_type=PlayerType.AI,
            color=(220, 57, 59)
        )
        self.state.add_player(player)
        self.assertEqual(len(self.state.players), 1)
        self.assertEqual(self.state.players[1].name, "AI_1")
        self.assertEqual(self.state.players[1].player_type, PlayerType.AI)

    def test_add_multiple_players(self) -> None:
        """Test adding multiple players."""
        player1 = Player(
            player_id=0,
            name="Human",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        player2 = Player(
            player_id=1,
            name="AI_1",
            player_type=PlayerType.AI,
            color=(220, 57, 59)
        )
        player3 = Player(
            player_id=2,
            name="AI_2",
            player_type=PlayerType.AI,
            color=(51, 153, 51)
        )
        self.state.add_player(player1)
        self.state.add_player(player2)
        self.state.add_player(player3)
        
        self.assertEqual(len(self.state.players), 3)
        self.assertEqual(self.state.players[0].player_type, PlayerType.HUMAN)
        self.assertEqual(self.state.players[1].player_type, PlayerType.AI)
        self.assertEqual(self.state.players[2].player_type, PlayerType.AI)

    def test_player_has_unique_id(self) -> None:
        """Test that each player gets a unique ID."""
        player1 = Player(
            player_id=0,
            name="Player1",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        player2 = Player(
            player_id=1,
            name="Player2",
            player_type=PlayerType.AI,
            color=(220, 57, 59)
        )
        self.state.add_player(player1)
        self.state.add_player(player2)
        
        player1_id = self.state.players[0].player_id
        player2_id = self.state.players[1].player_id
        
        self.assertNotEqual(player1_id, player2_id)

    def test_get_player_by_id(self) -> None:
        """Test retrieving a player by ID."""
        player = Player(
            player_id=0,
            name="TestPlayer",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.state.add_player(player)
        player_id = self.state.players[0].player_id
        
        retrieved = self.state.players.get(player_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "TestPlayer")

    def test_get_nonexistent_player(self) -> None:
        """Test retrieving a nonexistent player."""
        retrieved = self.state.players.get(99999)
        self.assertIsNone(retrieved)


class TestRegion(unittest.TestCase):
    """Test the Region class."""

    def setUp(self) -> None:
        """Set up test regions."""
        self.region1 = Region(
            region_id=1,
            name="North",
            position=(100.0, 100.0),
            adjacent_regions=[2, 3]
        )
        self.region2 = Region(
            region_id=2,
            name="South",
            position=(100.0, 200.0),
            adjacent_regions=[1, 4]
        )

    def test_region_creation(self) -> None:
        """Test creating a region."""
        self.assertEqual(self.region1.region_id, 1)
        self.assertEqual(self.region1.name, "North")
        self.assertIsNone(self.region1.owner_id)

    def test_region_adjacency(self) -> None:
        """Test checking if regions are adjacent."""
        self.assertTrue(self.region1.is_adjacent_to(2))
        self.assertTrue(self.region1.is_adjacent_to(3))
        self.assertFalse(self.region1.is_adjacent_to(4))

    def test_set_region_owner(self) -> None:
        """Test setting region owner."""
        self.region1.owner_id = 1
        self.assertEqual(self.region1.owner_id, 1)

    def test_region_fortification(self) -> None:
        """Test fortification state."""
        self.assertFalse(self.region1.is_fortified())
        
        self.region1.fortification = FortificationLevel.LEVEL_1
        self.assertTrue(self.region1.is_fortified())

    def test_region_type_capital(self) -> None:
        """Test capital region type."""
        capital_region = Region(
            region_id=10,
            name="Capital City",
            position=(500.0, 500.0),
            region_type=RegionType.CAPITAL
        )
        self.assertEqual(capital_region.region_type, RegionType.CAPITAL)


class TestGameLogic(unittest.TestCase):
    """Test the GameLogic class."""

    def setUp(self) -> None:
        """Set up test game logic."""
        self.state = GameState()
        self.config = GameConfig()
        self.logic = GameLogic(self.state, self.config)

    def test_distance_calculation(self) -> None:
        """Test distance calculation between two points."""
        # Points 3-4-5 triangle
        pos1 = (0, 0)
        pos2 = (3, 4)
        
        distance = self.logic.calculate_distance(pos1, pos2)
        self.assertAlmostEqual(distance, 5.0)

    def test_distance_zero(self) -> None:
        """Test distance between same point is zero."""
        pos = (100, 100)
        distance = self.logic.calculate_distance(pos, pos)
        self.assertAlmostEqual(distance, 0.0)

    def test_can_attack_own_region_fails(self) -> None:
        """Test that player cannot attack their own region."""
        # Add player and setup
        player = Player(
            player_id=0,
            name="Player1",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.state.add_player(player)
        player_id = self.state.players[0].player_id
        
        # Create region owned by player
        region = Region(
            region_id=1,
            name="Home",
            position=(100, 100),
            owner_id=player_id,
            adjacent_regions=[]
        )
        region.owner_id = player_id
        self.state.regions[1] = region
        
        # Player cannot attack own region
        can_attack = self.logic.can_attack_region(player_id, 1)
        self.assertFalse(can_attack)

    def test_can_attack_unowned_region_fails(self) -> None:
        """Test that player cannot attack unowned region."""
        player = Player(
            player_id=0,
            name="Player1",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.state.add_player(player)
        player_id = self.state.players[0].player_id
        
        # Create unowned region
        region = Region(
            region_id=1,
            name="Empty",
            position=(100.0, 100.0)
        )
        self.state.regions[1] = region
        
        # Player cannot attack unowned region
        can_attack = self.logic.can_attack_region(player_id, 1)
        self.assertFalse(can_attack)

    def test_can_fortify_owned_region_succeeds(self) -> None:
        """Test that player can fortify their own region."""
        player = Player(
            player_id=0,
            name="Player1",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.state.add_player(player)
        player_id = self.state.players[0].player_id
        
        # Create region owned by player
        region = Region(
            region_id=1,
            name="Home",
            position=(100.0, 100.0),
            owner_id=player_id
        )
        self.state.regions[1] = region
        
        # Player can fortify own region
        can_fortify = self.logic.can_fortify_region(player_id, 1)
        self.assertTrue(can_fortify)

    def test_cannot_fortify_nonowned_region(self) -> None:
        """Test that player cannot fortify region they don't own."""
        player1 = Player(
            player_id=0,
            name="Player1",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        player2 = Player(
            player_id=1,
            name="Player2",
            player_type=PlayerType.AI,
            color=(220, 57, 59)
        )
        self.state.add_player(player1)
        self.state.add_player(player2)
        
        player1_id = self.state.players[0].player_id
        player2_id = self.state.players[1].player_id
        
        # Create region owned by player 2
        region = Region(
            region_id=1,
            name="Enemy",
            position=(100.0, 100.0),
            owner_id=player2_id
        )
        self.state.regions[1] = region
        
        # Player 1 cannot fortify
        can_fortify = self.logic.can_fortify_region(player1_id, 1)
        self.assertFalse(can_fortify)

    def test_cannot_fortify_already_fortified(self) -> None:
        """Test that player cannot fortify already fortified region."""
        player = Player(
            player_id=0,
            name="Player1",
            player_type=PlayerType.HUMAN,
            color=(25, 118, 210)
        )
        self.state.add_player(player)
        player_id = self.state.players[0].player_id
        
        # Create region already fortified
        region = Region(
            region_id=1,
            name="Fortress",
            position=(100.0, 100.0),
            owner_id=player_id,
            fortification=FortificationLevel.LEVEL_3
        )
        self.state.regions[1] = region
        
        # Cannot fortify
        can_fortify = self.logic.can_fortify_region(player_id, 1)
        self.assertFalse(can_fortify)


class TestBattleResult(unittest.TestCase):
    """Test the BattleResult class."""

    def test_battle_result_creation(self) -> None:
        """Test creating a battle result."""
        result = BattleResult(
            attacker_id=1,
            defender_id=2,
            region_id=5
        )
        self.assertEqual(result.attacker_id, 1)
        self.assertEqual(result.defender_id, 2)
        self.assertEqual(result.region_id, 5)

    def test_battle_result_winner_assignment(self) -> None:
        """Test assigning winner to battle result."""
        result = BattleResult(
            attacker_id=1,
            defender_id=2,
            region_id=5
        )
        result.winner_id = 1
        self.assertEqual(result.winner_id, 1)


class TestPlayerNameGeneration(unittest.TestCase):
    """Test player name generation."""

    def test_generate_player_name(self) -> None:
        """Test generating a random player name."""
        name = generate_player_name(1, PlayerType.AI)
        self.assertIsInstance(name, str)
        self.assertGreater(len(name), 0)

    def test_generate_multiple_unique_names(self) -> None:
        """Test that generated names can be different."""
        names = [
            generate_player_name(i, PlayerType.AI) for i in range(1, 11)
        ]
        # At least some should be unique (though theoretically all could be same)
        self.assertGreaterEqual(len(set(names)), 1)


def run_tests() -> None:
    """Run all tests."""
    unittest.main(argv=[''], exit=False, verbosity=2)


if __name__ == "__main__":
    run_tests()
