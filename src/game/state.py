from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum, auto
import json
from datetime import datetime


class PlayerType(Enum):
    """Type of player."""
    HUMAN = auto()
    AI = auto()


class RegionType(Enum):
    """Type of region."""
    NORMAL = auto()
    CAPITAL = auto()


class FortificationLevel(Enum):
    """Fortification levels for regions."""
    NONE = auto()
    FORTIFIED = auto()


class GamePhase(Enum):
    """Current phase of the game."""
    SETUP = auto()        # Game setup, choosing settings
    SPAWNING = auto()     # Placing capitals
    OCCUPYING = auto()    # Initial region occupation
    BATTLE = auto()       # Battle phase (questions)
    TURN = auto()         # Player's turn (fortify/attack)
    CAPITAL_ATTACK = auto()  # Special phase for attacking capitals
    GAME_OVER = auto()    # Game ended


@dataclass
class Player:
    """
    Represents a player in the game.
    Player 0 is always human, players 1+ are AI.
    """

    player_id: int  # 0 for human, 1+ for AI
    name: str
    player_type: PlayerType
    color: Tuple[int, int, int]
    score: int = 1000  # Starting score
    is_alive: bool = True
    regions_controlled: List[int] = field(default_factory=list[int])  # Region IDs
    capital_region_id: Optional[int] = None
    turns_played: int = 0

    def add_region(self, region_id: int) -> None:
        """Add a region to player's control."""
        if region_id not in self.regions_controlled:
            self.regions_controlled.append(region_id)

    def remove_region(self, region_id: int) -> bool:
        """
        Remove a region from player's control.

        Returns:
            True if region was removed, False if not found
        """
        if region_id in self.regions_controlled:
            self.regions_controlled.remove(region_id)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert player to serializable dictionary."""
        return {
            'player_id': self.player_id,
            'name': self.name,
            'player_type': self.player_type.name,
            'color': list(self.color),
            'score': self.score,
            'is_alive': self.is_alive,
            'regions_controlled': self.regions_controlled.copy(),
            'capital_region_id': self.capital_region_id,
            'turns_played': self.turns_played
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Player:
        """Create player from dictionary."""
        return cls(
            player_id=data['player_id'],
            name=data['name'],
            player_type=PlayerType[data['player_type']],
            color=tuple(data['color']),
            score=data['score'],
            is_alive=data['is_alive'],
            regions_controlled=data['regions_controlled'],
            capital_region_id=data['capital_region_id'],
            turns_played=data['turns_played']
        )


@dataclass
class Capital:
    """
    Represents a capital region with special rules.
    Capitals have HP and regeneration mechanics.
    """

    region_id: int
    owner_id: int
    current_hp: int = 3
    max_hp: int = 3
    turns_since_last_attack: int = 0  # For HP regeneration
    is_destroyed: bool = False

    def take_damage(self) -> bool:
        """
        Capital takes 1 damage.

        Returns:
            True if capital is destroyed (HP reaches 0), False otherwise
        """
        if self.current_hp > 0:
            self.current_hp -= 1
            self.register_attack()  # Reset regeneration counter

            if self.current_hp <= 0:
                self.is_destroyed = True
                return True
        return False

    def register_attack(self) -> None:
        """
        Register that the capital was attacked.

        Args:
            was_damaging: Whether the attack caused damage
        """
        self.turns_since_last_attack = 0  # Reset regeneration counter

    def regenerate(self) -> None:
        """Regenerate 1 HP if conditions are met."""
        if (not self.is_destroyed and
            self.turns_since_last_attack >= 3 and
            self.current_hp < self.max_hp
            ):
            self.current_hp += 1
            self.turns_since_last_attack = 0  # Reset after regeneration

    def increment_turn_counter(self) -> None:
        """Increment counter for HP regeneration."""
        if not self.is_destroyed:
            self.turns_since_last_attack += 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert capital to serializable dictionary."""
        return {
            'region_id': self.region_id,
            'owner_id': self.owner_id,
            'current_hp': self.current_hp,
            'max_hp': self.max_hp,
            'turns_since_last_attack': self.turns_since_last_attack,
            'is_destroyed': self.is_destroyed,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Capital:
        """Create capital from dictionary."""
        return cls(
            region_id=data['region_id'],
            owner_id=data['owner_id'],
            current_hp=data['current_hp'],
            max_hp=data['max_hp'],
            turns_since_last_attack=data['turns_since_last_attack'],
            is_destroyed=data['is_destroyed'],
        )


@dataclass
class Region:
    """
    Represents a territory/region on the map.
    """

    region_id: int
    name: str
    position: Tuple[float, float]  # (x, y) coordinates for display
    owner_id: Optional[int] = None  # None = neutral/unoccupied
    region_type: RegionType = RegionType.NORMAL
    fortification: FortificationLevel = FortificationLevel.NONE
    adjacent_regions: List[int] = field(default_factory=list[int])  # IDs of adjacent regions
    point_value: int = 500  # Current point value
    has_been_captured: bool = False  # Whether captured in battle before
    original_owner: Optional[int] = None  # First owner (for point tracking)
    is_selectable: bool = False  # For UI highlighting during selection

    def __post_init__(self) -> None:
        """Validate region data after initialization."""
        if self.original_owner is None and self.owner_id is not None:
            self.original_owner = self.owner_id

    def fortify(self) -> bool:
        """
        Fortify the region.

        Returns:
            True if fortification succeeded, False if already fortified
        """
        if self.fortification == FortificationLevel.NONE:
            self.fortification = FortificationLevel.FORTIFIED
            return True
        return False

    def remove_fortification(self) -> None:
        """Remove fortification (when region is captured)."""
        self.fortification = FortificationLevel.NONE

    def is_fortified(self) -> bool:
        """Check if region is fortified."""
        return self.fortification == FortificationLevel.FORTIFIED

    def change_owner(self, new_owner_id: int, via_capital_capture: bool = False) -> None:
        """
        Change ownership of region.

        Args:
            new_owner_id: New owner's player ID
            via_capital_capture: Whether this is due to capital capture (affects point value)
        """
        self.owner_id = new_owner_id

        # Update point value based on capture method
        if not via_capital_capture and not self.has_been_captured:
            # First battle capture - increase to 800 points
            self.point_value = 800
            self.has_been_captured = True
        # If via_capital_capture, keep current point value

    def is_adjacent_to(self, other_region_id: int) -> bool:
        """Check if this region is adjacent to another region."""
        return other_region_id in self.adjacent_regions

    def to_dict(self) -> Dict[str, Any]:
        """Convert region to serializable dictionary."""
        return {
            'region_id': self.region_id,
            'name': self.name,
            'position': list(self.position),
            'owner_id': self.owner_id,
            'region_type': self.region_type.name,
            'fortification': self.fortification.name,
            'adjacent_regions': self.adjacent_regions.copy(),
            'point_value': self.point_value,
            'has_been_captured': self.has_been_captured,
            'original_owner': self.original_owner,
            'is_selectable': self.is_selectable
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Region:
        """Create region from dictionary."""
        return cls(
            region_id=data['region_id'],
            name=data['name'],
            position=tuple(data['position']),
            owner_id=data['owner_id'],
            region_type=RegionType[data['region_type']],
            fortification=FortificationLevel[data['fortification']],
            adjacent_regions=data['adjacent_regions'],
            point_value=data['point_value'],
            has_been_captured=data['has_been_captured'],
            original_owner=data['original_owner'],
            is_selectable=data['is_selectable']
        )


@dataclass
class BattleResult:
    """Represents the result of a battle."""

    attacker_id: int
    defender_id: int
    region_id: int
    attacker_correct: Optional[bool] = None
    defender_correct: Optional[bool] = None
    open_answer_ranking: Optional[List[int]] = None  # Player IDs in order of closeness
    winner_id: Optional[int] = None
    defender_bonus_awarded: bool = False
    region_captured: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert battle result to serializable dictionary."""
        return {
            'attacker_id': self.attacker_id,
            'defender_id': self.defender_id,
            'region_id': self.region_id,
            'attacker_correct': self.attacker_correct,
            'defender_correct': self.defender_correct,
            'open_answer_ranking': self.open_answer_ranking,
            'winner_id': self.winner_id,
            'defender_bonus_awarded': self.defender_bonus_awarded,
            'region_captured': self.region_captured,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BattleResult:
        """Create battle result from dictionary."""
        return cls(**data)


@dataclass
class GameState:
    """
    Main game state container.
    Tracks all game objects and current state.
    """

    # Core game objects
    players: Dict[int, Player] = field(default_factory=dict[int, Player])
    regions: Dict[int, Region] = field(default_factory=dict[int, Region])
    capitals: Dict[int, Capital] = field(default_factory=dict[int, Capital])  # key: region_id

    # Game state
    current_phase: GamePhase = GamePhase.SETUP
    current_player_id: Optional[int] = None
    current_turn: int = 0
    max_turns_per_player: int = 10
    selected_region_id: Optional[int] = None  # For UI selection
    is_special_round: bool = False  # Double points earned this turn (region points unchanged)

    # Battle state
    current_battle: Optional[BattleResult] = None
    battle_phase: int = 0  # 0 = first MC, 1 = OA if needed

    # Occupation phase
    occupation_ranking: List[int] = field(default_factory=list[int])  # Player IDs in order
    occupation_regions_remaining: List[int] = field(default_factory=list[int])  # Region IDs available

    # Game history
    battle_history: List[BattleResult] = field(default_factory=list[BattleResult])
    turn_history: List[Dict[str, Any]] = field(default_factory=list[dict[str, Any]])

    # Metadata
    game_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d_%H%M%S"))
    created_at: datetime = field(default_factory=datetime.now)
    config_hash: str = ""  # Hash of game config for validation

    def __post_init__(self) -> None:
        """Initialize derived structures."""
        # Ensure capitals dict stays in sync
        self._sync_capitals()

    def _sync_capitals(self) -> None:
        """Ensure capitals dict is consistent with regions."""
        # Remove capitals for regions that don't exist or aren't capitals
        region_ids_to_remove: List[int] = []
        for region_id, _ in self.capitals.items():
            if (region_id not in self.regions or
                self.regions[region_id].region_type != RegionType.CAPITAL):
                region_ids_to_remove.append(region_id)

        for region_id in region_ids_to_remove:
            del self.capitals[region_id]

    def add_player(self, player: Player) -> None:
        """Add a player to the game."""
        self.players[player.player_id] = player

    def add_region(self, region: Region) -> None:
        """Add a region to the game."""
        self.regions[region.region_id] = region

        # If it's a capital, create corresponding Capital object
        if region.region_type == RegionType.CAPITAL and region.owner_id is not None:
            capital = Capital(
                region_id=region.region_id,
                owner_id=region.owner_id
            )
            self.capitals[region.region_id] = capital

    def get_player_regions(self, player_id: int) -> List[Region]:
        """Get all regions controlled by a player."""
        player = self.players.get(player_id)
        if not player:
            return []

        regions_list: List[Region] = []
        for region_id in player.regions_controlled:
            if region_id in self.regions:
                regions_list.append(self.regions[region_id])
        return regions_list

    def get_adjacent_enemy_regions(self, player_id: int) -> List[Region]:
        """
        Get enemy regions adjacent to player's controlled regions.

        Args:
            player_id: Player to check for

        Returns:
            List of enemy regions that are adjacent to player's regions
        """
        player_regions = self.get_player_regions(player_id)
        adjacent_enemy_regions: List[Region] = []
        visited_region_ids: set[int] = set()

        for player_region in player_regions:
            for adjacent_id in player_region.adjacent_regions:
                if (adjacent_id in visited_region_ids or  # Already visited
                    adjacent_id not in self.regions):  # Region does not exist
                    continue

                adjacent_region = self.regions[adjacent_id]
                if (adjacent_region.owner_id is not None and
                    adjacent_region.owner_id != player_id):
                    adjacent_enemy_regions.append(adjacent_region)
                    visited_region_ids.add(adjacent_id)

        return adjacent_enemy_regions

    def get_available_regions_for_occupation(
            self, player_id: int) -> Tuple[List[Region], List[Region]]:
        """
        Get regions available for a player to occupy during occupation phase.
        Prioritizes adjacent regions, then any unoccupied region.

        Args:
            player_id: Player trying to occupy

        Returns:
            List of available regions, adjacent ones first
        """
        player = self.players.get(player_id)
        if not player:
            return [], []

        # Get all unoccupied regions
        unoccupied_regions: List[Region] = []
        for region in self.regions.values():
            if region.owner_id is None:
                unoccupied_regions.append(region)

        if not player.regions_controlled:
            # Player has no regions yet (initial occupation) - return all
            return [], unoccupied_regions

        # Separate into adjacent and non-adjacent
        adjacent_regions: List[Region] = []
        non_adjacent_regions: List[Region] = []

        player_region_ids = set(player.regions_controlled)

        for region in unoccupied_regions:
            is_adjacent = False
            for player_region_id in player_region_ids:
                if region.is_adjacent_to(player_region_id):
                    is_adjacent = True
                    break

            if is_adjacent:
                adjacent_regions.append(region)
            else:
                non_adjacent_regions.append(region)


        # Return adjacent first, then non-adjacent
        return adjacent_regions, non_adjacent_regions

    def eliminate_player(self, eliminated_id: int, conqueror_id: int) -> None:
        """
        Eliminate a player who lost their capital.

        Args:
            eliminated_id: Player being eliminated
            conqueror_id: Player who captured the capital
        """
        eliminated = self.players.get(eliminated_id)
        conqueror = self.players.get(conqueror_id)

        if not eliminated or not conqueror:
            return

        # Mark player as dead
        eliminated.is_alive = False

        # Transfer regions
        for region_id in eliminated.regions_controlled:
            if region_id in self.regions:
                region = self.regions[region_id]
                # Capture via capital - keep current point value
                region.change_owner(conqueror_id, via_capital_capture=True)
                conqueror.add_region(region_id)

        # Clear player's regions
        eliminated.regions_controlled.clear()

        # Transfer score
        conqueror.score += eliminated.score
        eliminated.score = 0

        # Update capital owner if this player had one
        for capital in self.capitals.values():
            if capital.owner_id == eliminated_id:
                capital.owner_id = conqueror_id

    def get_alive_players(self) -> List[Player]:
        """Get all alive players."""
        return [p for p in self.players.values() if p.is_alive]

    def get_player_turn_order(self) -> List[int]:
        """
        Get player turn order based on score at the end of the occupation phase.
        Lowest score goes first.

        Returns:
            List of player IDs in turn order
        """
        alive_players = self.get_alive_players()
        # Sort by score ascending (lowest first), then by player ID for tiebreaker
        sorted_players = sorted(
            alive_players,
            key=lambda p: (p.score, p.player_id)
        )
        return [p.player_id for p in sorted_players]

    def to_dict(self) -> Dict[str, Any]:
        """Convert game state to serializable dictionary."""
        return {
            'players': {pid: p.to_dict() for pid, p in self.players.items()},
            'regions': {rid: r.to_dict() for rid, r in self.regions.items()},
            'capitals': {rid: c.to_dict() for rid, c in self.capitals.items()},
            'current_phase': self.current_phase.name,
            'current_player_id': self.current_player_id,
            'current_turn': self.current_turn,
            'max_turns_per_player': self.max_turns_per_player,
            'selected_region_id': self.selected_region_id,
            'current_battle': self.current_battle.to_dict() if self.current_battle else None,
            'battle_phase': self.battle_phase,
            'occupation_ranking': self.occupation_ranking.copy(),
            'occupation_regions_remaining': self.occupation_regions_remaining.copy(),
            'battle_history': [b.to_dict() for b in self.battle_history],
            'turn_history': self.turn_history.copy(),
            'game_id': self.game_id,
            'created_at': self.created_at.isoformat(),
            'config_hash': self.config_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> GameState:
        """Create game state from dictionary."""
        state = cls()

        # Recreate players
        for pid, p_data in data['players'].items():
            state.players[int(pid)] = Player.from_dict(p_data)

        # Recreate regions
        for rid, r_data in data['regions'].items():
            state.regions[int(rid)] = Region.from_dict(r_data)

        # Recreate capitals
        for rid, c_data in data['capitals'].items():
            state.capitals[int(rid)] = Capital.from_dict(c_data)

        # Set other attributes
        state.current_phase = GamePhase[data['current_phase']]
        state.current_player_id = data['current_player_id']
        state.current_turn = data['current_turn']
        state.max_turns_per_player = data['max_turns_per_player']
        state.selected_region_id = data['selected_region_id']

        if data['current_battle']:
            state.current_battle = BattleResult.from_dict(data['current_battle'])

        state.battle_phase = data['battle_phase']
        state.occupation_ranking = data['occupation_ranking']
        state.occupation_regions_remaining = data['occupation_regions_remaining']

        state.battle_history = [
            BattleResult.from_dict(b) for b in data['battle_history']
        ]

        state.turn_history = data['turn_history']
        state.game_id = data['game_id']
        state.created_at = datetime.fromisoformat(data['created_at'])
        state.config_hash = data['config_hash']

        return state

    def save(self, filepath: str) -> None:
        """Save game state to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, filepath: str) -> GameState:
        """Load game state from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return cls.from_dict(data)


# Helper functions
def generate_player_name(player_id: int, player_type: PlayerType) -> str:
    """Generate a name for a player."""
    if player_type == PlayerType.HUMAN:
        return "You"
    else:
        ai_names = ["Alex", "Sam", "Jordan", "Taylor", "Casey", "Morgan"]
        return f"{ai_names[player_id % len(ai_names)]} (AI)"


def calculate_distance(pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
    """Calculate Euclidean distance between two points."""
    return ((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2) ** 0.5


if __name__ == "__main__":
    print("=== Testing Game State Classes ===")

    player = Player(
        player_id=0,
        name="Test Player",
        player_type=PlayerType.HUMAN,
        color=(25, 118, 210)
    )
    print(f"Created player: {player.name} with {len(player.regions_controlled)} regions")

    region = Region(
        region_id=1,
        name="Test Region",
        position=(100.0, 100.0),
        owner_id=0
    )
    print(f"Created region: {region.name}")

    capital = Capital(region_id=1, owner_id=0)
    print(f"Created capital with {capital.current_hp}/{capital.max_hp} HP")

    # Test attack registration
    capital.register_attack()
    print(f"Capital attacked, regeneration counter: {capital.turns_since_last_attack}")

    game_state = GameState()
    game_state.add_player(player)
    game_state.add_region(region)

    print(f"Game state created with {len(game_state.players)} player")
    print("All classes working correctly!")