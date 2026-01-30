from __future__ import annotations
import math
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum

from src.utils.config import GameConfig
from src.game.state import (
    GameState, GamePhase, Player, Region, RegionType, BattleResult
)
from src.trivia.question import Question, QuestionType


class BattleOutcome(Enum):
    """Possible outcomes of a battle."""
    ATTACKER_WINS = "attacker_wins"
    DEFENDER_WINS = "defender_wins"
    TIE_MC_CORRECT = "tie_mc_correct"  # Both answered MC correctly → go to OA
    TIE_MC_WRONG = "tie_mc_wrong"      # Both answered MC wrong → defender wins


class GameLogic:
    """
    Handles game rules, calculations, and battle resolution.
    """
    
    def __init__(self, game_state: GameState, config: GameConfig):
        """
        Initialize game logic.
        
        Args:
            game_state: Current game state
            config: Game configuration
        """
        self.state = game_state
        self.config = config
    
    def calculate_distance(self, pos1: Tuple[float, float], 
                          pos2: Tuple[float, float]) -> float:
        """
        Calculate Euclidean distance between two points.
        
        Args:
            pos1: First position (x, y)
            pos2: Second position (x, y)
            
        Returns:
            Distance
        """
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    
    def can_attack_region(self, attacker_id: int, region_id: int) -> bool:
        """
        Check if a player can attack a specific region.
        
        Args:
            attacker_id: ID of attacking player
            region_id: ID of region to attack
            
        Returns:
            True if attack is valid
        """
        if region_id not in self.state.regions:
            return False
        
        region = self.state.regions[region_id]
        
        # Check: Region must be owned by someone else
        if region.owner_id is None or region.owner_id == attacker_id:
            return False
        
        # Check: Attacker must have at least one adjacent region
        attacker_regions = self.state.get_player_regions(attacker_id)
        for attacker_region in attacker_regions:
            if region.is_adjacent_to(attacker_region.region_id):
                return True
        
        return False
    
    def can_fortify_region(self, player_id: int, region_id: int) -> bool:
        """
        Check if a player can fortify a specific region.
        
        Args:
            player_id: ID of player
            region_id: ID of region to fortify
            
        Returns:
            True if fortification is valid
        """
        if region_id not in self.state.regions:
            return False
        
        region = self.state.regions[region_id]
        
        # Check: Region must be owned by player
        if region.owner_id != player_id:
            return False
        
        # Check: Region must not already be fortified
        if region.is_fortified():
            return False
        
        # Check: Region must not be a capital (capitals have special rules)
        if region.region_type == RegionType.CAPITAL:
            # Capitals can only be fortified if they've been captured
            if region_id in self.state.capitals:
                capital = self.state.capitals[region_id]
                if capital.owner_id == player_id and capital.current_hp == 1:
                    # Captured capital with 1 HP can be fortified
                    return True
                return False
        
        return True
    
    def resolve_battle(self, attacker_id: int, defender_id: int, 
                      region_id: int, question: Question,
                      attacker_answer: Any, defender_answer: Any,
                      attacker_time: float, defender_time: float) -> BattleResult:
        """
        Resolve a battle between attacker and defender.
        
        Args:
            attacker_id: ID of attacking player
            defender_id: ID of defending player
            region_id: ID of region being attacked
            question: The multiple choice question asked
            attacker_answer: Attacker's answer
            defender_answer: Defender's answer
            attacker_time: Time attacker took to answer
            defender_time: Time defender took to answer
            
        Returns:
            BattleResult with outcome
        """
        result = BattleResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            region_id=region_id
        )
        
        # Determine if answers are correct
        attacker_correct = (attacker_answer == question.correct_answer)
        defender_correct = (defender_answer == question.correct_answer)
        
        result.attacker_correct = attacker_correct
        result.defender_correct = defender_correct
        
        # Apply battle rules (Rule 8 + clarifications)
        if not attacker_correct:
            # Attacker wrong → defender wins
            result.winner_id = defender_id
            result.defender_bonus_awarded = True
            
        elif attacker_correct and not defender_correct:
            # Attacker correct, defender wrong → attacker wins
            result.winner_id = attacker_id
            result.region_captured = True
            
        else:  # Both correct
            # Tie in MC → go to open answer question (handled separately)
            result.winner_id = None  # Will be determined by OA question
            
        return result
    
    def resolve_open_answer_battle(self, attacker_id: int, defender_id: int,
                                  region_id: int, question: Question,
                                  answers: Dict[int, float],
                                  answer_times: Dict[int, float]) -> BattleResult:
        """
        Resolve open answer portion of a battle.
        
        Args:
            attacker_id: ID of attacking player
            defender_id: ID of defending player
            region_id: ID of region being attacked
            question: The open answer question
            answers: Dict of player_id -> answer
            answer_times: Dict of player_id -> answer time
            
        Returns:
            BattleResult with winner determined by closeness
        """
        result = BattleResult(
            attacker_id=attacker_id,
            defender_id=defender_id,
            region_id=region_id
        )
        
        correct_answer = float(question.correct_answer)
        
        # Calculate closeness for both players
        player_closeness: List[Tuple[int, float, float]] = []  # (player_id, closeness, time)
        
        for player_id in [attacker_id, defender_id]:
            if player_id in answers:
                answer = answers[player_id]
                try:
                    closeness = abs(float(answer) - correct_answer)
                except (ValueError, TypeError):
                    closeness = float('inf')
                
                time = answer_times.get(player_id, float('inf'))
                player_closeness.append((player_id, closeness, time))
        
        # Sort by closeness (lower is better), then by time (lower is better)
        player_closeness.sort(key=lambda x: (x[1], x[2]))
        
        # Extract ranking
        ranking = [player_id for player_id, _, _ in player_closeness]
        result.open_answer_ranking = ranking
        
        if ranking:
            result.winner_id = ranking[0]
            
            if result.winner_id == attacker_id:
                result.region_captured = True
            else:
                result.defender_bonus_awarded = True
        
        return result
    
    def execute_battle_result(self, battle_result: BattleResult) -> None:
        """
        Execute the consequences of a battle result.
        
        Args:
            battle_result: Result of a battle
        """
        if battle_result.winner_id is None:
            return
        
        region = self.state.regions.get(battle_result.region_id)
        if not region:
            return
        
        attacker = self.state.players.get(battle_result.attacker_id)
        defender = self.state.players.get(battle_result.defender_id)
        
        if not attacker or not defender:
            return
        
        if battle_result.winner_id == battle_result.defender_id:
            # Defender wins
            if battle_result.defender_bonus_awarded:
                defender.score += self.config.defense_bonus
                print(f"Player {defender.name} defended successfully! +{self.config.defense_bonus} points")
        
        else:  # Attacker wins
            # Capture the region
            old_owner_id = region.owner_id
            
            # Remove from defender
            if old_owner_id is not None:
                old_owner = self.state.players.get(old_owner_id)
                if old_owner:
                    old_owner.remove_region(region.region_id)
            
            # Add to attacker
            region.change_owner(battle_result.attacker_id, via_capital_capture=False)
            region.remove_fortification()  # Fortification is destroyed on capture
            attacker.add_region(region.region_id)
            
            # Update scores
            attacker.score += region.point_value
            if old_owner_id is not None:
                old_owner = self.state.players[old_owner_id]
                old_owner.score -= region.point_value
            
            battle_result.region_captured = True
            
            print(f"Player {attacker.name} captured {region.name}! +{region.point_value} points")
    
    def execute_capital_attack(self, attacker_id: int, capital_region_id: int,
                              battle_result: BattleResult) -> bool:
        """
        Execute a capital attack and handle capital capture.
        
        Args:
            attacker_id: ID of attacking player
            capital_region_id: ID of capital region
            battle_result: Result of the battle
            
        Returns:
            True if capital was destroyed, False otherwise
        """
        if capital_region_id not in self.state.capitals:
            return False
        
        capital = self.state.capitals[capital_region_id]
        region = self.state.regions.get(capital_region_id)
        
        if not region:
            return False
        
        attacker = self.state.players.get(attacker_id)
        defender = self.state.players.get(capital.owner_id)
        
        if not attacker or not defender:
            return False
        
        if battle_result.winner_id == attacker_id:
            # Attacker hits the capital
            capital_destroyed = capital.take_damage()
            
            if capital_destroyed:
                # Capital captured!
                print(f"Player {attacker.name} captured {defender.name}'s capital!")
                
                # Eliminate defender and transfer territories
                self.state.eliminate_player(capital.owner_id, attacker_id)
                
                # The capital region becomes a normal region
                region.region_type = RegionType.NORMAL
                region.point_value = self.config.capital_points  # Keep capital value
                region.has_been_captured = True
                
                # Remove capital object (it's now a normal region)
                del self.state.capitals[capital_region_id]
                
                return True
            else:
                print(f"Player {attacker.name} damaged {defender.name}'s capital! "
                      f"HP: {capital.current_hp}/{capital.max_hp}")
                return False
        
        elif battle_result.winner_id == capital.owner_id and battle_result.defender_bonus_awarded:
            # Successful defense
            defender.score += self.config.defense_bonus
            capital.register_attack()  # Reset regeneration
            print(f"Player {defender.name} defended their capital! +{self.config.defense_bonus} points")
        
        return False
    
    def fortify_region(self, player_id: int, region_id: int) -> bool:
        """
        Fortify a region for a player.
        
        Args:
            player_id: ID of player
            region_id: ID of region to fortify
            
        Returns:
            True if fortification succeeded
        """
        if not self.can_fortify_region(player_id, region_id):
            return False
        
        region = self.state.regions[region_id]
        
        # Special handling for captured capitals
        if region.region_type == RegionType.CAPITAL and region_id in self.state.capitals:
            capital = self.state.capitals[region_id]
            if capital.current_hp == 1:
                # Captured capital gets fortified (HP increases to 2)
                capital.current_hp = 2
                capital.max_hp = 2
                print(f"Player {self.state.players[player_id].name} fortified captured capital {region.name}")
                return True
        
        # Normal region fortification
        if region.fortify():
            print(f"Player {self.state.players[player_id].name} fortified {region.name}")
            return True
        
        return False
    
    def update_capital_regeneration(self) -> None:
        """
        Update capital HP regeneration for all capitals.
        Called at the end of each turn.
        """
        for capital in self.state.capitals.values():
            capital.increment_turn_counter()
            
            # Check if regeneration conditions are met
            if (capital.turns_since_last_attack >= self.config.capital_hp_regeneration_turns and
                capital.current_hp < capital.max_hp and
                not capital.is_destroyed):
                
                capital.regenerate()
                if capital.current_hp > 0:
                    region = self.state.regions.get(capital.region_id)
                    if region:
                        print(f"Capital {region.name} regenerated to {capital.current_hp}/{capital.max_hp} HP")
    
    def check_game_over(self) -> Optional[int]:
        """
        Check if the game is over.
        
        Returns:
            Winning player ID, or None if game is not over
        """
        alive_players = self.state.get_alive_players()
        
        # Game ends when only one player remains
        if len(alive_players) == 1:
            return alive_players[0].player_id
        
        # Game ends when maximum turns reached
        if (self.state.current_phase == GamePhase.TURN and
            self.state.current_turn > self.state.max_turns_per_player * len(alive_players)):
            
            # Player with highest score wins
            highest_score = -1
            winner_id = None
            
            for player in alive_players:
                if player.score > highest_score:
                    highest_score = player.score
                    winner_id = player.player_id
            
            return winner_id
        
        return None
    
    def get_available_actions(self, player_id: int) -> Dict[str, List[int]]:
        """
        Get available actions for a player during their turn.
        
        Args:
            player_id: ID of player
            
        Returns:
            Dictionary with 'attack' and 'fortify' lists of region IDs
        """
        player = self.state.players.get(player_id)
        if not player or not player.is_alive:
            return {'attack': [], 'fortify': []}
        
        attack_targets: List[int] = []
        fortify_targets: List[int] = []
        
        # Get all enemy regions adjacent to player's regions
        for player_region in self.state.get_player_regions(player_id):
            for adj_id in player_region.adjacent_regions:
                if adj_id in self.state.regions:
                    adj_region = self.state.regions[adj_id]
                    if (adj_region.owner_id is not None and 
                        adj_region.owner_id != player_id and
                        adj_id not in attack_targets):
                        
                        attack_targets.append(adj_id)
        
        # Get all player regions that can be fortified
        for player_region in self.state.get_player_regions(player_id):
            if self.can_fortify_region(player_id, player_region.region_id):
                fortify_targets.append(player_region.region_id)
        
        return {
            'attack': attack_targets,
            'fortify': fortify_targets
        }
    
    def calculate_region_value(self, region: Region, 
                              via_capital_capture: bool = False) -> int:
        """
        Calculate point value of a region based on capture method.
        
        Args:
            region: The region
            via_capital_capture: Whether captured through capital capture
            
        Returns:
            Point value
        """
        if via_capital_capture:
            # Keep current value when captured via capital
            return region.point_value
        elif region.has_been_captured:
            # Already captured before → 800 points
            return self.config.captured_region_points
        else:
            # First capture → 500 points, becomes 800 after
            return self.config.initial_region_points
    
    def validate_game_state(self) -> List[str]:
        """
        Validate game state for consistency.
        
        Returns:
            List of error messages, empty if valid
        """
        errors: List[str] = []
        
        # Check player-region consistency
        for player_id, player in self.state.players.items():
            for region_id in player.regions_controlled:
                if region_id not in self.state.regions:
                    errors.append(f"Player {player_id} controls non-existent region {region_id}")
                else:
                    region = self.state.regions[region_id]
                    if region.owner_id != player_id:
                        errors.append(f"Region {region_id} owner mismatch: "
                                     f"region.owner={region.owner_id}, player={player_id}")
        
        # Check capital consistency
        for region_id, capital in self.state.capitals.items():
            if region_id not in self.state.regions:
                errors.append(f"Capital for non-existent region {region_id}")
            else:
                region = self.state.regions[region_id]
                if region.region_type != RegionType.CAPITAL:
                    errors.append(f"Region {region_id} has capital object but is not CAPITAL type")
                if region.owner_id != capital.owner_id:
                    errors.append(f"Capital {region_id} owner mismatch: "
                                 f"region.owner={region.owner_id}, capital.owner={capital.owner_id}")
        
        # Check adjacency symmetry
        for region_id, region in self.state.regions.items():
            for adj_id in region.adjacent_regions:
                if adj_id not in self.state.regions:
                    errors.append(f"Region {region_id} adjacent to non-existent region {adj_id}")
                else:
                    adj_region = self.state.regions[adj_id]
                    if region_id not in adj_region.adjacent_regions:
                        errors.append(f"Adjacency not symmetric: {region_id}->{adj_id} but not {adj_id}->{region_id}")
        
        return errors


if __name__ == "__main__":
    print("=== Testing GameLogic ===")
    
    from src.utils.config import GameConfig, Difficulty
    from src.game.state import GameState, Player, PlayerType, Region
    from src.trivia.question import Question, QuestionType
    
    # Create test configuration
    config = GameConfig()
    config.difficulty = Difficulty.MEDIUM
    
    # Create test game state
    state = GameState()
    
    # Add test players
    player1 = Player(
        player_id=0,
        name="Test Player 1",
        player_type=PlayerType.HUMAN,
        color=(255, 0, 0),
        score=1000
    )
    player2 = Player(
        player_id=1,
        name="Test Player 2",
        player_type=PlayerType.AI,
        color=(0, 0, 255),
        score=1000
    )
    state.add_player(player1)
    state.add_player(player2)
    
    # Add test regions
    region1 = Region(
        region_id=1,
        name="Region 1",
        position=(100, 100),
        owner_id=0
    )
    region2 = Region(
        region_id=2,
        name="Region 2",
        position=(200, 100),
        owner_id=1
    )
    region1.adjacent_regions = [2]
    region2.adjacent_regions = [1]
    
    state.add_region(region1)
    state.add_region(region2)
    
    # Create game logic
    logic = GameLogic(state, config)
    
    # Test distance calculation
    dist = logic.calculate_distance((0, 0), (3, 4))
    print(f"Distance (0,0) to (3,4): {dist}")
    assert abs(dist - 5.0) < 0.001, "Distance calculation wrong"
    
    # Test attack validation
    can_attack = logic.can_attack_region(0, 2)
    print(f"Player 0 can attack Region 2: {can_attack}")
    assert can_attack, "Should be able to attack adjacent region"
    
    can_attack_self = logic.can_attack_region(0, 1)
    print(f"Player 0 can attack own Region 1: {can_attack_self}")
    assert not can_attack_self, "Should not be able to attack own region"
    
    # Test battle resolution
    test_question = Question(
        id=1,
        text="Test question",
        category="Test",
        question_type=QuestionType.MULTIPLE_CHOICE,
        correct_answer="Correct",
        options=["Correct", "Wrong1", "Wrong2", "Wrong3"]
    )
    
    # Test: Attacker wrong → defender wins
    result1 = logic.resolve_battle(
        attacker_id=0,
        defender_id=1,
        region_id=2,
        question=test_question,
        attacker_answer="Wrong1",
        defender_answer="Wrong2",
        attacker_time=1.0,
        defender_time=2.0
    )
    print(f"\nBattle 1 - Attacker wrong: winner={result1.winner_id}")
    assert result1.winner_id == 1, "Defender should win when attacker is wrong"
    
    # Test: Attacker correct, defender wrong → attacker wins
    result2 = logic.resolve_battle(
        attacker_id=0,
        defender_id=1,
        region_id=2,
        question=test_question,
        attacker_answer="Correct",
        defender_answer="Wrong1",
        attacker_time=1.0,
        defender_time=2.0
    )
    print(f"Battle 2 - Attacker correct, defender wrong: winner={result2.winner_id}")
    assert result2.winner_id == 0, "Attacker should win when correct and defender wrong"
    
    # Test: Both correct → tie (no winner yet)
    result3 = logic.resolve_battle(
        attacker_id=0,
        defender_id=1,
        region_id=2,
        question=test_question,
        attacker_answer="Correct",
        defender_answer="Correct",
        attacker_time=1.0,
        defender_time=2.0
    )
    print(f"Battle 3 - Both correct: winner={result3.winner_id}")
    assert result3.winner_id is None, "Should be tie when both correct"
    
    print("\nAll tests passed!")