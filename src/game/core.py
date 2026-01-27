from __future__ import annotations
import pygame
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto

from src.utils.config import GameConfig
from src.game.state import (
    GameState, GamePhase, Player, PlayerType, Region, RegionType, 
    Capital, generate_player_name
)
from src.game.logic import GameLogic
from src.ui.screen_manager import ScreenManager
from src.trivia.database import TriviaDatabase
from src.trivia.question import Question, QuestionType
from src.map.map_manager import MapManager
from src.ai.strategic_ai import StrategicAI
from src.ai.difficulty import AIDifficultyManager
from src.utils.sound_manager import SoundManager


class TurnAction(Enum):
    """Possible actions a player can take during their turn."""
    NONE = auto()
    FORTIFY = auto()
    ATTACK = auto()


class Game:
    """
    Main game controller that orchestrates all game components.
    Manages the game loop, state transitions, and player interactions.
    """
    
    def __init__(self, config: GameConfig):
        """
        Initialize the game with given configuration.
        
        Args:
            config: Game configuration settings
        """
        self.config = config
        self.screen = None
        self.clock = pygame.time.Clock()
        self.running = False
        
        # Game components
        self.state = GameState()
        self.state.max_turns_per_player = config.turns_per_player
        
        self.logic = GameLogic(self.state, self.config)
        self.screen_manager = None  # Will be initialized in setup_display
        self.sound_manager = SoundManager()

        # Human answer
        self.waiting_for_human_answer = False
        self.human_answer_value: Optional[float] = None
        self.current_question_screen: Optional[str] = None  # "occupation" or "battle"

        # Region selection state
        self.waiting_for_region_selection = False
        self.selectable_region_ids: List[int] = []
        self.selected_region_id: Optional[int] = None
        self.current_selection_player: Optional[int] = None
        
        #Occupation regions
        self.clickable_occupation_regions = []
        
        # AI system
        self.ai_manager = AIDifficultyManager(config)
        self.ai_players: Dict[int, StrategicAI] = {}
        
        # Trivia database
        self.trivia_db = TriviaDatabase(config.questions_db)
        
        # Map manager
        self.map_manager = MapManager()
        
        # Current turn state
        self.current_action: TurnAction = TurnAction.NONE
        self.last_click_time: float = 0
        self.click_cooldown: float = 0.3  # seconds between clicks
        
        # UI state
        self.message_text: str = ""
        self.message_timer: float = 0
        self.message_duration: float = 2.0  # seconds
        
        # Battle state
        self.battle_question: Optional[Question] = None
        self.battle_answers: Dict[int, Any] = {}  # player_id -> answer
        self.battle_answer_times: Dict[int, float] = {}  # player_id -> time
        self.battle_start_time: float = 0
        
        # Initialize game objects
        self.setup_display()
        self.setup_players()
        self.setup_regions()
        
    def setup_display(self) -> None:
        """Initialize Pygame display and screen manager."""
        if self.config.fullscreen:
            self.screen = pygame.display.set_mode(
                (self.config.screen_width, self.config.screen_height),
                pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.config.screen_width, self.config.screen_height)
            )
        
        pygame.display.set_caption("Triviador")
        
        # Initialize screen manager
        self.screen_manager = ScreenManager(self.screen, self.config)
        
        # Load sounds
        if self.sound_manager:
            self.sound_manager.load_sounds(self.config.assets_dir)
    
    def setup_players(self) -> None:
        """Initialize all players (human + AI)."""
        # Human player (always player 0)
        human_player = Player(
            player_id=0,
            name="You",
            player_type=PlayerType.HUMAN,
            color=self.config.get_player_color(0),
            score=self.config.starting_score
        )
        self.state.add_player(human_player)
        
        # AI players
        total_players = self.config.get_total_players()
        for player_id in range(1, total_players):
            ai_name = generate_player_name(player_id, PlayerType.AI)
            ai_player = Player(
                player_id=player_id,
                name=ai_name,
                player_type=PlayerType.AI,
                color=self.config.get_player_color(player_id),
                score=self.config.starting_score
            )
            self.state.add_player(ai_player)
            
            # Create AI controller
            self.ai_players[player_id] = StrategicAI(
                player_id=player_id,
                config=self.config,
                game_state=self.state,
                ai_manager=self.ai_manager
            )
        
        print(f"Setup {total_players} players (1 human + {self.config.ai_count} AI)")
    
    def setup_regions(self) -> None:
        """Generate and setup all regions on the map."""
        # Generate random regions with map manager
        regions_data = self.map_manager.generate_regions(
            region_count=self.config.region_count,
            screen_width=self.config.screen_width,
            screen_height=self.config.screen_height
        )
        
        for region_data in regions_data:
            region = Region(
                region_id=region_data['id'],
                name=region_data['name'],
                position=region_data['position'],
                adjacent_regions=region_data['adjacent']
            )
            self.state.add_region(region)
        
        print(f"Generated {len(regions_data)} regions")
        
        # Start with spawning phase
        self.state.current_phase = GamePhase.SPAWNING
        self.start_spawning_phase()
    
    def start_spawning_phase(self) -> None:
        """Start the capital spawning phase."""
        available_regions = list(self.state.regions.keys())
        players_to_spawn = [pid for pid in self.state.players.keys()]
        
        # Shuffle players for random spawn order
        random.shuffle(players_to_spawn)
        
        spawned_capitals: List[int] = []
        
        for player_id in players_to_spawn:
            # Filter regions that are far enough from existing capitals
            candidate_regions = [
                rid for rid in available_regions
                if all(
                    self.logic.calculate_distance(
                        self.state.regions[rid].position,
                        self.state.regions[other_rid].position
                    ) >= self.config.min_capital_distance * 50  # Scale factor
                    for other_rid in spawned_capitals
                )
            ]
            
            if not candidate_regions:
                # Fallback: any available region
                candidate_regions = available_regions
            
            if candidate_regions:
                capital_region_id = random.choice(candidate_regions)
                self.place_capital(player_id, capital_region_id)
                spawned_capitals.append(capital_region_id)
                available_regions.remove(capital_region_id)
        
        # Move to occupation phase
        self.state.current_phase = GamePhase.OCCUPYING
        self.occupation_phase()
    
    def place_capital(self, player_id: int, region_id: int) -> None:
        """Place a capital for a player in a region."""
        region = self.state.regions[region_id]
        region.region_type = RegionType.CAPITAL
        region.owner_id = player_id
        region.point_value = self.config.capital_points
        region.original_owner = player_id
        
        # Add to player's controlled regions
        player = self.state.players[player_id]
        player.add_region(region_id)
        player.capital_region_id = region_id
        
        # Create capital object
        capital = Capital(
            region_id=region_id,
            owner_id=player_id
        )
        self.state.capitals[region_id] = capital
        
        print(f"Player {player.name} capital placed in {region.name}")
    
    def ask_occupation_question(self) -> None:
        """Ask an open answer question for occupation phase."""
        # Get question from database
        categories = self.config.get_included_categories()
        question = self.trivia_db.get_open_question(categories)
        
        if not question:
            # Fallback question
            question = Question(
                id=0,
                text="What is 42?",
                category="General Knowledge",
                question_type=QuestionType.OPEN_ANSWER,
                correct_answer=42,
                options=[]
            )
        
        self.battle_question = question
        self.battle_answers = {}
        self.battle_answer_times = {}
        self.battle_start_time = time.time()
        
        # Get answers from all players
        for player_id, player in self.state.players.items():
            if player.player_type == PlayerType.HUMAN:
                # Human will answer through UI
                continue
            
            # AI answers
            think_time = self.config.get_ai_think_time() / 1000.0
            answer = self.ai_players[player_id].answer_open_question(
                question, 
                think_time
            )
            self.battle_answers[player_id] = answer
            self.battle_answer_times[player_id] = time.time()
        
        print(f"Occupation question: {question.text}")
    
    def process_occupation_ranking(self) -> List[int]:
        """Process results of occupation question and rank players."""
        if not self.battle_question:
            return []
        
        # Collect all answers
        all_answers: List[Tuple[int, Any, float]] = []  # (player_id, answer, time)
        
        for player_id, player in self.state.players.items():
            if player_id in self.battle_answers:
                answer = self.battle_answers[player_id]
                answer_time = self.battle_answer_times.get(player_id, float('inf'))
                all_answers.append((player_id, answer, answer_time))
        
        # Rank by closeness to correct answer, then by speed
        correct_answer = float(self.battle_question.correct_answer)
        
        def closeness_key(item: Tuple[int, Any, float]) -> Tuple[float, float]:
            player_id, answer, answer_time = item
            try:
                diff = abs(float(answer) - correct_answer)
            except (ValueError, TypeError):
                diff = float('inf')
            return (diff, answer_time)
        
        sorted_answers = sorted(all_answers, key=closeness_key)
        
        # Extract player IDs in ranking order
        ranking = [item[0] for item in sorted_answers]
        
        print(f"Occupation ranking: {ranking}")
        return ranking
    
    def occupation_phase(self) -> None:
        """Occupation phase."""
        # Get all unoccupied regions
        unoccupied_regions: List[int] = [
            rid for rid, region in self.state.regions.items()
            if region.owner_id is None
        ]
        
        while unoccupied_regions:
            # Ask question
            self.ask_occupation_question()

            # Get human answer through UI
            human_answer = self.get_human_answer_for_occupation()
            
            # Record human answer
            if human_answer is not None:
                self.battle_answers[0] = human_answer
                self.battle_answer_times[0] = time.time()
            
            # Get ranking for asked question
            ranking = self.process_occupation_ranking()
            if not ranking:
                ranking = list(self.state.players.keys())  # Fallback
            
            self.state.occupation_ranking = ranking

            # First place takes region
            first_player_id = ranking[0]
            if self.take_occupation_region(first_player_id, unoccupied_regions):
                unoccupied_regions = [rid for rid in unoccupied_regions 
                                    if self.state.regions[rid].owner_id is None]
            
            # First place takes another region (if exists)
            if len(unoccupied_regions) > 0:
                if self.take_occupation_region(first_player_id, unoccupied_regions):
                    unoccupied_regions = [rid for rid in unoccupied_regions 
                                        if self.state.regions[rid].owner_id is None]
            
            # Second place takes region (if exists)
            if len(unoccupied_regions) > 0:
                second_player_id = ranking[1]
                if self.take_occupation_region(second_player_id, unoccupied_regions):
                    unoccupied_regions = [rid for rid in unoccupied_regions 
                                        if self.state.regions[rid].owner_id is None]
        
        # Switch phase
        self.start_game_turns()

    def get_human_answer_for_occupation(self) -> Optional[float]:
        """
        Get human answer for occupation question through UI.
        
        Returns:
            Human's answer as float, or None if something went wrong
        """
        print("Waiting for human answer...")

        # Set up question screen state
        self.waiting_for_human_answer = True
        self.current_question_screen = "occupation"
        
        # Show the question screen
        if self.screen_manager and self.battle_question:
            # Display the question
            self.screen_manager.show_open_question(
                question=self.battle_question,
                time_limit=self.config.open_answer_time
            )
            
        # Wait for answer in the game loop
        start_time = time.time()
        while self.waiting_for_human_answer:
            # Handle events
            self.handle_events()
            
            # Check for timeout
            elapsed = time.time() - start_time
            if elapsed > self.config.open_answer_time:
                print("Time's up for occupation question!")
                self.waiting_for_human_answer = False
                return None
            
            # Update and draw
            self.update()
            self.draw()
            
            # Small delay to prevent CPU overuse
            pygame.time.delay(10)
        
        # Return the collected answer
        return self.human_answer_value
    
    def take_occupation_region(self, player_id: int, available_region_ids: List[int]) -> bool:
        """
        Have a player take a region during occupation phase.
        
        Args:
            player_id: ID of player taking the region
            available_region_ids: List of unoccupied region IDs
            
        Returns:
            True if region was taken, False otherwise
        """
        if not available_region_ids:
            return False
        
        player = self.state.players.get(player_id)
        if not player:
            print(f"Error: Player {player_id} not found")
            return False
        
        # Get available regions as Region objects
        available_regions = [self.state.regions[rid] for rid in available_region_ids]
        
        # Get adjacent regions for this player
        adjacent_regions, any_regions = self.state.get_available_regions_for_occupation(player_id)
        
        # Determine clickable regions (adjacent first, then any)
        if adjacent_regions:
            # Filter to only include available regions
            clickable_regions = [r for r in adjacent_regions if r.region_id in available_region_ids]
        else:
            clickable_regions = [r for r in any_regions if r.region_id in available_region_ids]
        
        # Fallback if no clickable regions found
        if not clickable_regions:
            clickable_regions = available_regions
        
        if player.player_type == PlayerType.HUMAN:
            # Human player chooses through UI
            region_id = self.get_human_region_choice(player_id, clickable_regions)
            if region_id is None:
                print("Human didn't choose a region, selecting randomly")
                chosen_region = random.choice(clickable_regions)
                region_id = chosen_region.region_id
        else:
            # AI player chooses automatically
            ai = self.ai_players.get(player_id)
            if ai and hasattr(ai, 'choose_occupation_region'):
                chosen_region = ai.choose_occupation_region(clickable_regions)
            else:
                # Simple AI: choose closest to capital or random
                if player.capital_region_id and player.capital_region_id in self.state.regions:
                    capital_pos = self.state.regions[player.capital_region_id].position
                    chosen_region = min(clickable_regions,
                                       key=lambda r: self.logic.calculate_distance(r.position, capital_pos))
                else:
                    chosen_region = random.choice(clickable_regions)
            region_id = chosen_region.region_id
        
        # Occupy the region
        return self.occupy_region_for_player(player_id, region_id)

    def get_human_region_choice(self, player_id:int, available_regions: List[Region]) -> Optional[int]:
        """
        Get human player's choice of region through UI.
        
        Args:
            available_regions: List of Region objects the player can choose from
            
        Returns:
            Chosen region ID, or None if cancelled
        """
        
        # Set up UI state for region selection
        self.waiting_for_region_selection = True
        self.selectable_region_ids = [r.region_id for r in available_regions]
        self.current_selection_player = player_id

        # Highlight available regions
        for region in available_regions:
            region.is_selectable = True

        # Show selection prompt
        self.message_text = f"Choose a region to occupy! ({len(available_regions)} available)"
        self.message_timer = time.time()

        # Wait for click in game loop
        while self.waiting_for_region_selection:
            # Handle events
            self.handle_events()
            
            # Check if user pressed ESC to cancel
            keys = pygame.key.get_pressed()
            if keys[pygame.K_ESCAPE]:
                print("Region selection cancelled by ESC")
                self.waiting_for_region_selection = False
                return None
            
            # Update and draw
            self.update()
            self.draw()
            
            # Small delay
            pygame.time.delay(10)
        
        # Clean up highlighting
        for region in available_regions:
            region.is_selectable = False
        
        # Return the selected region ID
        return self.selected_region_id

    def occupy_region_for_player(self, player_id: int, region_id: int) -> bool:
        """Occupy a region for a player during occupation phase."""
        if region_id not in self.state.regions:
            print(f"Error: Region {region_id} not found")
            return False
        
        region = self.state.regions[region_id]
        player = self.state.players.get(player_id)
        
        if not player:
            print(f"Error: Player {player_id} not found")
            return False
        
        if region.owner_id is not None:
            print(f"Error: Region {region_id} already occupied by player {region.owner_id}")
            return False
        
        # Occupy the region
        region.owner_id = player_id
        region.original_owner = player_id
        region.point_value = self.config.initial_region_points  # 500 points
        player.add_region(region_id)
        
        # Update player score
        player.score += region.point_value
        
        print(f"Player {player.name} occupied {region.name} (+{region.point_value} points)")
        
        # Play sound
        if self.sound_manager:
            self.sound_manager.play_sound("occupy")
        
        return True
    
    def draw(self) -> None:
        """Draw the game."""
        self.screen.fill(self.config.colors.background)
        
        # Draw through screen manager
        if self.screen_manager:
            self.screen_manager.draw(self.state)
            
            # Draw question screen if active
            if self.waiting_for_human_answer and self.battle_question:
                if self.current_question_screen == "occupation":
                    # Draw open answer question interface
                    self.draw_open_answer_interface()
            
            # Draw message if any
            if self.message_text:
                self.screen_manager.draw_message(
                    self.message_text,
                    (self.config.screen_width // 2, 50)
                )
        
        pygame.display.flip()

    def draw_open_answer_interface(self) -> None:
        """Draw the open answer question interface."""
        if not self.battle_question:
            return
        
        # Draw question background
        question_bg = pygame.Rect(
            self.config.screen_width // 2 - 300,
            self.config.screen_height // 2 - 200,
            600, 400
        )
        pygame.draw.rect(self.screen, self.config.colors.panel, question_bg, border_radius=10)
        pygame.draw.rect(self.screen, self.config.colors.text_primary, question_bg, 2, border_radius=10)
        
        # Draw question text
        font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["body"])
        question_lines = self.wrap_text(self.battle_question.text, font, 550)
        
        y_pos = question_bg.y + 20
        for line in question_lines:
            text_surf = font.render(line, True, self.config.colors.text_primary)
            text_rect = text_surf.get_rect(center=(question_bg.centerx, y_pos))
            self.screen.blit(text_surf, text_rect)
            y_pos += 30
        
        # Draw current answer
        answer_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["heading"])
        answer_text = str(self.human_answer_value) if self.human_answer_value is not None else ""
        answer_surf = answer_font.render(answer_text, True, self.config.colors.text_accent)
        answer_rect = answer_surf.get_rect(center=(question_bg.centerx, y_pos + 50))
        self.screen.blit(answer_surf, answer_rect)
        
        # Draw instructions
        inst_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["small"])
        instructions = [
            "Enter numbers with keyboard or numpad",
            "BACKSPACE: delete last digit",
            "ENTER: submit answer",
            "-: toggle negative sign",
            "ESC: cancel"
        ]
        
        y_pos = question_bg.bottom - 80
        for inst in instructions:
            inst_surf = inst_font.render(inst, True, self.config.colors.text_secondary)
            inst_rect = inst_surf.get_rect(midleft=(question_bg.x + 20, y_pos))
            self.screen.blit(inst_surf, inst_rect)
            y_pos += 25

    def update(self) -> None:
        """Update game state."""
        current_time = time.time()
        
        # Update message timer
        if self.message_timer > 0 and current_time - self.message_timer > self.message_duration:
            self.message_text = ""
            self.message_timer = 0
        
        # Update screen manager if it exists
        if self.screen_manager:
            self.screen_manager.update(self.state)
    
    def wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = ' '.join(current_line)
            test_width = font.size(test_line)[0]
            
            if test_width > max_width:
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines

    def handle_events(self) -> None:
        """Handle Pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    
                # Handle number input for open answer questions
                elif self.waiting_for_human_answer and self.current_question_screen == "occupation":
                    if pygame.K_0 <= event.key <= pygame.K_9:
                        # Append digit to answer
                        digit = event.key - pygame.K_0
                        current = str(self.human_answer_value) if self.human_answer_value is not None else ""
                        new_value = current + str(digit)
                        try:
                            self.human_answer_value = float(new_value)
                        except ValueError:
                            pass
                    
                    elif event.key == pygame.K_BACKSPACE:
                        # Remove last digit
                        if self.human_answer_value is not None:
                            str_val = str(int(self.human_answer_value))
                            if len(str_val) > 1:
                                self.human_answer_value = float(str_val[:-1])
                            else:
                                self.human_answer_value = 0.0
                    
                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # Submit answer
                        if self.human_answer_value is not None:
                            self.waiting_for_human_answer = False
                    
                    elif event.key == pygame.K_PERIOD or event.key == pygame.K_KP_PERIOD:
                        # Add decimal point
                        if self.human_answer_value is not None:
                            str_val = str(self.human_answer_value)
                            if '.' not in str_val:
                                self.human_answer_value = float(str_val + ".")
                    
                    elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                        # Toggle negative sign
                        if self.human_answer_value is not None:
                            self.human_answer_value = -self.human_answer_value
                        else:
                            self.human_answer_value = 0.0
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    current_time = time.time()
                    if current_time - self.last_click_time > self.click_cooldown:
                        self.handle_mouse_click(event.pos)
                        self.last_click_time = current_time

    def handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        """Handle mouse click at given position."""
        # Check if waiting for region selection
        if self.waiting_for_region_selection:
            region_id = self.get_region_at_position(pos)
            if region_id is not None and region_id in self.selectable_region_ids:
                self.selected_region_id = region_id
                self.waiting_for_region_selection = False
                print(f"Region {region_id} selected")
            return
        
        # Check if in turn phase and human's turn (for later)
        if (self.state.current_phase == GamePhase.TURN and 
            self.state.current_player_id == 0):
            region_id = self.get_region_at_position(pos)
            if region_id is not None:
                self.handle_turn_region_click(region_id)

    def get_region_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """Get region ID at mouse position, or None if no region."""
        # Simple implementation - check distance to region centers
        for region in self.state.regions.values():
            region_pos = region.position
            # Assuming position is (x, y) tuple
            distance = ((pos[0] - region_pos[0]) ** 2 + (pos[1] - region_pos[1]) ** 2) ** 0.5
            if distance < 30:  # Click radius - adjust based on your region size
                return region.region_id
        return None
    
    def handle_turn_region_click(self, region_id: int) -> None:
        """Handle region click during turn phase (for later implementation)."""
        print(f"Region {region_id} clicked during turn phase")
        # This will be implemented when we add the turn phase logic
        # For now, just log it

    def start_game_turns(self) -> None:
        """Start the main turn phase after occupation is complete."""
        print("Starting turn phase")
        
        # Set game phase
        self.state.current_phase = GamePhase.TURN
        
        # Determine turn order based on score (lowest first)
        turn_order = self.state.get_player_turn_order()
        
        if not turn_order:
            print("Error: No alive players!")
            return
        
        # Set first player
        self.state.current_player_id = turn_order[0]
        self.state.current_turn = 1
        
        # Reset all capital regeneration counters
        for capital in self.state.capitals.values():
            capital.turns_since_last_attack = 0
        
        print(f"Turn order: {turn_order}")
        print(f"Player {self.state.current_player_id}'s turn")

    def run(self) -> None:
        """Main game loop."""
        self.running = True
        
        while self.running:
            # Handle events
            self.handle_events()
            
            # Update game state
            self.update()
            
            # Draw everything
            self.draw()
            
            # Cap the frame rate
            self.clock.tick(self.config.fps)