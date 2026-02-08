from __future__ import annotations
import pygame
import random
import time
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto

from src.utils.config import GameConfig
from src.game.state import (
    GameState, GamePhase, Player, PlayerType, Region, RegionType,
    Capital, BattleResult, generate_player_name, FortificationLevel
)
from src.game.logic import GameLogic
from src.ui.screen_manager import ScreenManager, ScreenType
from src.trivia.question_loader import QuestionLoader
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
        self.human_answer_value: Optional[int] = None
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

        # Load questions from JSON file
        import os
        self.questions: List[Question] = []
        json_questions_path = 'data/questions.json'
        if os.path.exists(json_questions_path):
            try:
                self.questions = QuestionLoader.load_from_json(json_questions_path)
                print(f"Loaded {len(self.questions)} questions from {json_questions_path}")
            except Exception as e:
                print(f"Warning: Could not load questions from {json_questions_path}: {e}")
                self.questions = []

        # Map manager
        self.map_manager = MapManager()

        # Menu/Setup screen (type hint at module level to avoid circular imports)
        self.menu_screen: Any = None  # Will be initialized in setup_display
        self.game_settings_confirmed = False

        # Turn phase
        self.turn_order: List[int] = []
        self.current_player_index: int = 0
        self.selected_action: Optional[str] = None  # "fortify" or "attack"
        self.available_actions: Dict[str, List[int]] = {"attack": [], "fortify": []}

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
        # Set initial phase to SETUP (menu)
        self.state.current_phase = GamePhase.SETUP
        # Players and regions will be initialized after setup screen is confirmed

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

        # Initialize menu screen
        from src.ui.menu_screen import MenuScreen
        self.menu_screen = MenuScreen(self.screen, self.config)

        # Load sounds
        if self.sound_manager:
            self.sound_manager.load_sounds(self.config.assets_dir)

    def apply_game_settings(self, settings: Dict[str, Any]) -> None:
        """
        Apply settings from the menu screen to the game configuration.

        Args:
            settings: Dictionary with game settings from MenuScreen.get_settings()
        """
        print("Applying game settings...")
        # Update config with menu selections
        self.config.ai_count = settings['ai_count']
        self.config.difficulty = settings['difficulty']
        self.config.selected_categories = settings['selected_categories']
        self.config.category_mode = settings['category_mode']
        self.config.region_count = settings['region_count']
        self.config.turns_per_player = settings['turns_per_player']

        # Store player name
        self.player_name: str = settings.get('player_name', 'Player')

        print(f"Settings applied: {self.config.ai_count} AI, {self.config.difficulty.value} difficulty")
        print(f"Regions: {self.config.region_count}, Turns per player: {self.config.turns_per_player}")
        print(f"Categories: {len(self.config.selected_categories)} selected")
        print(f"Player name: {self.player_name}")

        # Now setup the game with these settings
        self.state.max_turns_per_player = self.config.turns_per_player
        self.setup_players()
        self.setup_regions()
        self.game_settings_confirmed = True

    def setup_players(self) -> None:
        """Initialize all players (human + AI)."""
        # Human player (always player 0)
        player_name = getattr(self, 'player_name', 'Player')
        human_player = Player(
            player_id=0,
            name=player_name,
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

    def _filter_questions(self, categories: Optional[List[str]] = None,
                         question_type: Optional[QuestionType] = None,
                         difficulty: Optional[int] = None) -> List[Question]:
        """
        Filter loaded questions by criteria.

        Args:
            categories: List of categories to include (None = all)
            question_type: Type of question to filter (None = any type)
            difficulty: Difficulty level to filter (None = any difficulty)

        Returns:
            List of matching questions
        """
        filtered = self.questions

        if categories:
            filtered = [q for q in filtered if q.category in categories]

        if question_type:
            filtered = [q for q in filtered if q.question_type == question_type]

        if difficulty:
            filtered = [q for q in filtered if q.difficulty == difficulty]

        return filtered

    def _get_random_question(self, categories: Optional[List[str]] = None,
                            question_type: Optional[QuestionType] = None,
                            difficulty: Optional[int] = None) -> Optional[Question]:
        """
        Get a random question matching criteria.

        Args:
            categories: List of categories to include (None = all categories)
            question_type: Type of question (None = any type)
            difficulty: Difficulty level (None = any difficulty)

        Returns:
            Random question or None if no matches
        """
        filtered = self._filter_questions(categories, question_type, difficulty)

        if not filtered:
            return None

        return random.choice(filtered)

    def _get_multiple_choice_question(self, categories: Optional[List[str]] = None,
                                     difficulty: Optional[int] = None) -> Optional[Question]:
        """
        Get a random multiple choice question.

        Args:
            categories: List of categories to include
            difficulty: Difficulty level

        Returns:
            Multiple choice question or None
        """
        return self._get_random_question(
            categories=categories,
            question_type=QuestionType.MULTIPLE_CHOICE,
            difficulty=difficulty
        )

    def _get_open_question(self, categories: Optional[List[str]] = None,
                          difficulty: Optional[int] = None) -> Optional[Question]:
        """
        Get a random open answer question.

        Args:
            categories: List of categories to include
            difficulty: Difficulty level

        Returns:
            Open answer question or None
        """
        return self._get_random_question(
            categories=categories,
            question_type=QuestionType.OPEN_ANSWER,
            difficulty=difficulty
        )

    def show_setup_screen(self) -> None:
        """Show the setup/menu screen and wait for player to start game."""
        while self.running and not self.game_settings_confirmed:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

                # Handle menu screen events
                if self.menu_screen.handle_event(event):
                    # Check if start button was clicked
                    settings = self.menu_screen.get_settings()
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        # Find which button was clicked
                        for button in self.menu_screen.buttons:
                            if button.rect.collidepoint(event.pos) and button.action == "start":
                                # Apply settings and start game
                                self.apply_game_settings(settings)
                                return
                            elif button.rect.collidepoint(event.pos) and button.action == "endless":
                                # Start endless mode
                                self.player_name = self.menu_screen.player_name
                                self.run_endless_mode()
                                return

            # Update and draw menu
            self.menu_screen.update()
            self.screen.fill(self.menu_screen.colors.background)
            self.menu_screen.draw()
            pygame.display.flip()
            self.clock.tick(self.config.fps)

    def show_game_over_screen(self) -> None:
        """Show the game over screen with final standings and new game button."""
        # Get final standings (sorted by score descending)
        standings = sorted(
            [(pid, player) for pid, player in self.state.players.items()],
            key=lambda x: x[1].score,
            reverse=True
        )

        # Find human player and save their score
        human_player = self.state.players.get(0)
        if human_player:
            from src.utils.game_recorder import GameRecorder
            GameRecorder.save_game(
                username=getattr(self, 'player_name', 'Player'),
                score=human_player.score,
                mode="normal"
            )

        # Find human player's position
        human_position = None
        for position, (player_id, player) in enumerate(standings, 1):
            if player_id == 0:  # Human is always player 0
                human_position = position
                break

        # Show game over screen
        show_new_game = False
        while self.running and not show_new_game:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if new game button was clicked
                    mouse_pos = event.pos
                    new_game_rect = pygame.Rect(
                        self.config.screen_width // 2 - 100,
                        self.config.screen_height - 120,
                        200, 50
                    )
                    if new_game_rect.collidepoint(mouse_pos):
                        show_new_game = True

            # Draw game over screen
            self.screen.fill(self.config.colors.background)

            # Draw title
            title_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["title"])
            title_text = "GAME OVER"
            title_surf = title_font.render(title_text, True, self.config.colors.text_accent)
            title_rect = title_surf.get_rect(center=(self.config.screen_width // 2, 80))
            self.screen.blit(title_surf, title_rect)

            # Draw human player placement
            if human_position:
                placement_map = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}
                placement_text = f"You finished in {placement_map.get(human_position, f'{human_position}th')} place!"
                placement_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["heading"])
                placement_surf = placement_font.render(placement_text, True, self.config.colors.text_primary)
                placement_rect = placement_surf.get_rect(center=(self.config.screen_width // 2, 180))
                self.screen.blit(placement_surf, placement_rect)

            # Draw standings
            standings_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["body"])
            standings_y = 280
            spacing = 50

            for position, (player_id, player) in enumerate(standings, 1):
                standing_text = f"{position}. {player.name} - {player.score} points"
                standing_surf = standings_font.render(standing_text, True, self.config.colors.text_primary)
                standing_rect = standing_surf.get_rect(center=(self.config.screen_width // 2, standings_y + position * spacing))
                self.screen.blit(standing_surf, standing_rect)

            # Draw new game button
            new_game_rect = pygame.Rect(
                self.config.screen_width // 2 - 100,
                self.config.screen_height - 120,
                200, 50
            )
            from src.utils.helpers import draw_button
            draw_button(
                self.screen,
                new_game_rect,
                "New Game",
                pygame.font.SysFont(self.config.font_name, self.config.font_sizes["body"]),
                self.config.colors.button_normal,
                self.config.colors.button_hover,
                self.config.colors.text_primary
            )

            pygame.display.flip()
            self.clock.tick(self.config.fps)

        # Reset game for new game
        if show_new_game:
            self.reset_game()

    def run_endless_mode(self) -> None:
        """Run endless mode: keep asking MC questions until user gets one wrong."""
        score = 0
        question_count = 0
        running = True

        while self.running and running:
            # Get a random multiple choice question
            categories = self.config.get_included_categories()
            question = self._get_multiple_choice_question(categories)

            if not question:
                # No questions available
                print("No questions available for endless mode")
                break

            question_count += 1

            # Show question and get answer
            answering = True
            selected_answer = None

            while self.running and answering:
                # Handle events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                        return

                    # Check for answer click
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mouse_pos = event.pos
                        # Check which option was clicked
                        for i, option in enumerate(question.options):
                            option_rect = pygame.Rect(
                                self.config.screen_width // 2 - 150,  # option_width // 2 = 300 // 2 = 150
                                question_y + (len(lines) + 2) * 25 + i * 50,  # option_y + i * (option_height + 10)
                                300,  # option_width
                                40   # option_height
                            )
                            if option_rect.collidepoint(mouse_pos):
                                selected_answer = option
                                answering = False
                                break

                # Draw endless mode question screen
                self.screen.fill(self.config.colors.background)

                # Draw score and question count at top
                score_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["heading"])
                score_text = f"Score: {score} | Question {question_count}"
                score_surf = score_font.render(score_text, True, self.config.colors.text_accent)
                score_rect = score_surf.get_rect(center=(self.config.screen_width // 2, 50))
                self.screen.blit(score_surf, score_rect)

                # Draw question (this needs to be calculated first to get question_y and lines)
                question_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["body"])
                question_text = question.text
                question_y = 150

                # Wrap question text
                words = question_text.split()
                lines = []
                current_line = []

                for word in words:
                    current_line.append(word)
                    line_text = ' '.join(current_line)
                    if question_font.size(line_text)[0] > self.config.screen_width - 100:
                        if len(current_line) > 1:
                            current_line.pop()
                            lines.append(' '.join(current_line))
                            current_line = [word]
                        else:
                            lines.append(line_text)
                            current_line = []

                if current_line:
                    lines.append(' '.join(current_line))

                for i, line in enumerate(lines):
                    line_surf = question_font.render(line, True, self.config.colors.text_primary)
                    line_rect = line_surf.get_rect(center=(self.config.screen_width // 2, question_y + i * 25))
                    self.screen.blit(line_surf, line_rect)

                # Draw answer options as buttons
                option_y = question_y + (len(lines) + 2) * 25
                option_height = 40
                option_width = 300

                # Get mouse position for hover detection
                mouse_pos = pygame.mouse.get_pos()

                for i, option in enumerate(question.options):
                    option_rect = pygame.Rect(
                        self.config.screen_width // 2 - option_width // 2,
                        option_y + i * (option_height + 10),
                        option_width,
                        option_height
                    )

                    # Check if mouse is over this option
                    is_hovered = option_rect.collidepoint(mouse_pos)

                    # Draw option button
                    from src.utils.helpers import draw_button
                    draw_button(
                        self.screen,
                        option_rect,
                        str(option),
                        pygame.font.SysFont(self.config.font_name, self.config.font_sizes["body"]),
                        self.config.colors.button_hover if is_hovered else self.config.colors.button_normal,
                        self.config.colors.button_hover,
                        self.config.colors.text_primary,
                        is_hovered
                    )

                pygame.display.flip()
                self.clock.tick(self.config.fps)

            if not self.running:
                break

            # Check if answer is correct
            if selected_answer == question.correct_answer:
                score += 1
                print(f"Endless mode: Question {question_count} - CORRECT! (Score: {score})")
            else:
                # Wrong answer - game over
                print(f"Endless mode: Question {question_count} - WRONG! Game over with score {score}")
                running = False

        # Save endless mode score
        from src.utils.game_recorder import GameRecorder
        GameRecorder.save_game(
            username=getattr(self, 'player_name', 'Player'),
            score=score,
            mode="endless"
        )

        # Show endless mode game over screen
        self._show_endless_mode_game_over(score, question_count)

        # Reset game for new game
        self.reset_game()

    def _show_endless_mode_game_over(self, score: int, total_questions: int) -> None:
        """Show the game over screen for endless mode."""
        show_new_game = False

        while self.running and not show_new_game:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    return

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check if new game button was clicked
                    mouse_pos = event.pos
                    new_game_rect = pygame.Rect(
                        self.config.screen_width // 2 - 100,
                        self.config.screen_height - 120,
                        200, 50
                    )
                    if new_game_rect.collidepoint(mouse_pos):
                        show_new_game = True

            # Draw game over screen
            self.screen.fill(self.config.colors.background)

            # Draw title
            title_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["title"])
            title_text = "ENDLESS MODE GAME OVER"
            title_surf = title_font.render(title_text, True, self.config.colors.text_accent)
            title_rect = title_surf.get_rect(center=(self.config.screen_width // 2, 80))
            self.screen.blit(title_surf, title_rect)

            # Draw final score
            score_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["heading"])
            score_text = f"Final Score: {score}"
            score_surf = score_font.render(score_text, True, self.config.colors.text_primary)
            score_rect = score_surf.get_rect(center=(self.config.screen_width // 2, 200))
            self.screen.blit(score_surf, score_rect)

            # Draw questions answered
            questions_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["body"])
            questions_text = f"Questions Answered: {total_questions - 1} (Last one was wrong)"
            questions_surf = questions_font.render(questions_text, True, self.config.colors.text_secondary)
            questions_rect = questions_surf.get_rect(center=(self.config.screen_width // 2, 280))
            self.screen.blit(questions_surf, questions_rect)

            # Draw new game button
            new_game_rect = pygame.Rect(
                self.config.screen_width // 2 - 100,
                self.config.screen_height - 120,
                200, 50
            )
            from src.utils.helpers import draw_button
            draw_button(
                self.screen,
                new_game_rect,
                "Main Menu",
                pygame.font.SysFont(self.config.font_name, self.config.font_sizes["body"]),
                self.config.colors.button_normal,
                self.config.colors.button_hover,
                self.config.colors.text_primary
            )

            pygame.display.flip()
            self.clock.tick(self.config.fps)

    def reset_game(self) -> None:
        """Reset the game to allow a new game to be played."""
        print("\n=== RESETTING GAME ===")

        # Reset game state
        self.state = GameState()

        # Reset settings confirmation
        self.game_settings_confirmed = False

        # Recreate menu screen for setup
        from src.ui.menu_screen import MenuScreen
        self.menu_screen = MenuScreen(self.screen, self.config)

        print("Game reset. Showing setup screen...")

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
        # Get question from loaded questions
        categories = self.config.get_included_categories()
        question = self._get_open_question(categories)

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

        for player_id, _ in self.state.players.items():
            if player_id in self.battle_answers:
                answer = self.battle_answers[player_id]
                answer_time = self.battle_answer_times.get(player_id, float('inf'))
                all_answers.append((player_id, answer, answer_time))

        # Rank by closeness to correct answer, then by speed
        correct_answer = float(self.battle_question.correct_answer)

        def closeness_key(item: Tuple[int, Any, float]) -> Tuple[float, float]:
            _, answer, answer_time = item
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
        self.turn_phase()

    def get_human_answer_for_occupation(self) -> Optional[int]:
        """
        Get human answer for occupation question through UI.

        Returns:
            Human's answer as float, or None if something went wrong
        """
        print("Waiting for human answer...")

        # Set up question screen state
        self.human_answer_value = None
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
                    self.message_text
                )

        pygame.display.flip()

    def draw_open_answer_interface(self) -> None:
        """Draw the open answer question interface."""
        if not self.battle_question:
            return

        # Create a semi-transparent overlay
        overlay = pygame.Surface((self.config.screen_width, self.config.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Semi-transparent black
        self.screen.blit(overlay, (0, 0))

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

        # Draw answer box
        answer_box = pygame.Rect(
            question_bg.centerx - 150,
            y_pos + 30,
            300, 60
        )
        pygame.draw.rect(self.screen, (255, 255, 255), answer_box, border_radius=5)
        pygame.draw.rect(self.screen, self.config.colors.text_primary, answer_box, 2, border_radius=5)

        # Draw current answer
        answer_font = pygame.font.SysFont(self.config.font_name, self.config.font_sizes["heading"])
        if self.human_answer_value is not None:
            answer_text = str(int(self.human_answer_value))  # Force integer display
        else:
            answer_text = "0"

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

                # Pass keyboard events to question screen if it's active and waiting for answer
                elif self.waiting_for_human_answer and self.screen_manager and self.screen_manager.current_screen == ScreenType.QUESTION:
                    if self.screen_manager.question_screen.handle_event(event):
                        # Question screen handled the event (could be numeric input or submission)
                        if self.screen_manager.question_screen.selected_answer is not None:
                            self.human_answer_value = self.screen_manager.question_screen.selected_answer
                            self.waiting_for_human_answer = False
                        return

                # Handle number input for open answer questions (keyboard fallback for occupation phase)
                elif self.waiting_for_human_answer and self.current_question_screen in ["occupation", "battle"]:
                    if pygame.K_0 <= event.key <= pygame.K_9:
                        # Append digit to answer
                        digit = event.key - pygame.K_0
                        if self.human_answer_value is None:
                            self.human_answer_value = digit
                        else:
                            current = str(int(self.human_answer_value))
                            new_value = current + str(digit)
                            self.human_answer_value = int(new_value)

                    elif event.key == pygame.K_BACKSPACE:
                        # Remove last digit
                        if self.human_answer_value is not None:
                            str_val = str(self.human_answer_value)
                            if len(str_val) > 1:
                                self.human_answer_value = int(str_val[:-1])
                            else:
                                self.human_answer_value = 0

                    elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                        # Submit answer
                        if self.human_answer_value is not None:
                            print(f"Answer submitted: {self.human_answer_value}")
                            self.waiting_for_human_answer = False
                        else:
                            # If no answer, default to 0
                            self.human_answer_value = 0
                            self.waiting_for_human_answer = False

                    elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                        # Toggle negative sign
                        if self.human_answer_value is not None:
                            self.human_answer_value = -self.human_answer_value
                        else:
                            self.human_answer_value = 0

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    current_time = time.time()
                    if current_time - self.last_click_time > self.click_cooldown:
                        self.handle_mouse_click(event.pos)
                        self.last_click_time = current_time

    def handle_mouse_click(self, pos: Tuple[int, int]) -> None:
        """Handle mouse click at given position."""
        # If question screen is active, let it handle the click first
        if self.screen_manager and self.screen_manager.current_screen == ScreenType.QUESTION:
            if self.screen_manager.question_screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': pos, 'button': 1})):
                # Question screen handled the event
                if self.screen_manager.question_screen.selected_answer is not None:
                    self.human_answer_value = self.screen_manager.question_screen.selected_answer
                    self.waiting_for_human_answer = False
                return

        # Check if waiting for region selection
        if self.waiting_for_region_selection:
            region_id = self.get_region_at_position(pos)
            if region_id is not None and region_id in self.selectable_region_ids:
                self.handle_turn_region_click(region_id)
            return

        # Check if in turn phase and human's turn
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

    def turn_phase(self) -> None:
        """
        Main turn phase logic where players take turns.

        Flow:
        1. Get turn order based on occupation ranking
        2. While current_turn < total_turns:
           - Get current player
           - Get available actions (attack/fortify regions)
           - If human: highlight available regions, wait for selection
           - If AI: use StrategicAI to determine action
           - Execute action and draw changes
           - Recalculate remaining turns
        3. End turn phase when complete
        """
        print("\n=== STARTING TURN PHASE ===")

        # 1. Get turn order
        self.turn_order = self.state.get_player_turn_order()
        print(f"Turn order: {[self.state.players[pid].name for pid in self.turn_order]}")

        # 2. Calculate total turns available
        alive_players = len([p for p in self.state.players.values() if p.is_alive])
        total_turns = alive_players * self.state.max_turns_per_player
        current_turn = 0  # Current turn counter

        print(f"Total turns available: {total_turns} ({alive_players} players × {self.state.max_turns_per_player} turns)")

        # Main turn loop
        while current_turn < total_turns:
            # Determine current player by round-robin
            player_index = current_turn % len(self.turn_order)
            current_player_id = self.turn_order[player_index]

            # Determine if this is a special round (30% chance)
            self.state.is_special_round = random.random() < 0.15

            # Update game state
            self.state.current_player_id = current_player_id
            self.state.current_phase = GamePhase.TURN
            self.state.current_turn = current_turn + 1  # 1-based for display

            player = self.state.players[current_player_id]

            special_text = " (SPECIAL ROUND - POINTS DOUBLED!)" if self.state.is_special_round else ""
            print(f"\n--- Turn {self.state.current_turn}{special_text} ---")
            print(f"Player {current_player_id} ({player.name})'s turn")

            # Skip dead players
            if not player.is_alive:
                print(f"  Player {current_player_id} is dead, skipping turn")
                current_turn += 1
                continue

            # Get available actions for current player
            available_actions = self.logic.get_available_actions(current_player_id)
            print(f"  Can attack regions: {available_actions['attack']}")
            print(f"  Can fortify regions: {available_actions['fortify']}")

            # Check if player has any actions available
            if not available_actions['attack'] and not available_actions['fortify']:
                print(f"  No available actions, skipping turn")
                current_turn += 1
                continue

            # Execute turn based on player type
            if player.player_type == PlayerType.HUMAN:
                # Human player: wait for UI selection
                action_completed = self._execute_human_turn(current_player_id, available_actions)
            else:
                # AI player: use StrategicAI to determine action
                action_completed = self._execute_ai_turn(current_player_id, available_actions)

            # Only increment if action was completed
            if action_completed:
                current_turn += 1

                # Check if game should end early
                alive_count = len(self.state.get_alive_players())
                if alive_count <= 1:
                    print("\n  Only 0-1 players alive, ending turn phase early")
                    break

        # End of turn phase
        print("\n=== TURN PHASE COMPLETE ===")
        self.end_turn_phase()

    def _execute_human_turn(self, player_id: int, available_actions: Dict[str, List[int]]) -> bool:
        """
        Execute human player's turn.

        Args:
            player_id: ID of human player
            available_actions: Available attack and fortify targets

        Returns:
            True if turn was completed, False otherwise
        """
        print(f"  Waiting for human player {player_id} to choose action...")

        # Highlight available regions
        self._highlight_available_regions(player_id, available_actions)

        # Prepare UI state
        self.waiting_for_region_selection = True
        self.selectable_region_ids = available_actions['attack'] + available_actions['fortify']
        self.current_selection_player = player_id
        self.selected_action = None
        self.selected_region_id = None

        self.message_text = f"{self.state.players[player_id].name}'s turn - Click a highlighted region"
        self.message_timer = time.time()

        # Wait for region selection in game loop
        selection_timeout = time.time() + 60  # 60 second timeout
        while self.waiting_for_region_selection and time.time() < selection_timeout:
            self.handle_events()
            self.update()
            self.draw()
            pygame.time.delay(10)

        # Check if selection was made
        if self.selected_region_id is None or self.selected_action is None:
            print(f"  No selection made, auto-selecting action...")
            # Auto-select an action
            if available_actions['attack']:
                self.selected_region_id = available_actions['attack'][0]
                self.selected_action = "attack"
            elif available_actions['fortify']:
                self.selected_region_id = available_actions['fortify'][0]
                self.selected_action = "fortify"
            else:
                return False

        # Execute the selected action
        success = self._execute_turn_action(player_id, self.selected_region_id, self.selected_action)

        # Clean up
        self._unhighlight_all_regions()
        self.waiting_for_region_selection = False

        return success


    def _highlight_available_regions(self, player_id: int, available_actions: Dict[str, List[int]]) -> None:
        """
        Highlight available regions for human player to select.

        Args:
            player_id: ID of player
            available_actions: Dictionary with 'attack' and 'fortify' region lists
        """
        # Unhighlight all first
        for region in self.state.regions.values():
            region.is_selectable = False

        # Highlight attack targets
        for region_id in available_actions['attack']:
            region = self.state.regions[region_id]
            region.is_selectable = True

        # Highlight fortify targets
        for region_id in available_actions['fortify']:
            region = self.state.regions[region_id]
            region.is_selectable = True

        print(f"  Highlighted {len(available_actions['attack'])} attack and {len(available_actions['fortify'])} fortify targets")

    def _unhighlight_all_regions(self) -> None:
        """Remove highlighting from all regions."""
        for region in self.state.regions.values():
            region.is_selectable = False

    def _execute_ai_turn(self, player_id: int, available_actions: Dict[str, List[int]]) -> bool:
        """
        Execute AI player's turn using StrategicAI methods.

        Args:
            player_id: ID of AI player
            available_actions: Available attack and fortify targets

        Returns:
            True if action was executed
        """
        ai = self.ai_players.get(player_id)
        if not ai:
            print(f"  No AI controller for player {player_id}")
            return True

        print(f"  AI {player_id} thinking...")

        action_type = None
        target_region_id = None
        ai_choice = random.randint(0,1)  # 0 -> Attack; 1 -> Fortify

        # Check for attack opportunities
        if ai_choice == 0 and available_actions['attack']:
            # Get Region objects for available attack targets
            attack_targets = [self.state.regions[rid] for rid in available_actions['attack']]

            # Use StrategicAI to choose best attack target
            chosen_target = ai.choose_attack_target(attack_targets)
            if chosen_target:
                action_type = "attack"
                target_region_id = chosen_target.region_id
                print(f"  AI {player_id} chooses to attack region {target_region_id}")

        # If no attack, try fortify
        if action_type is None and available_actions['fortify']:
            # Get Region objects for available fortify targets
            fortify_targets = [self.state.regions[rid] for rid in available_actions['fortify']]

            # Use StrategicAI to choose best region to fortify
            chosen_target = ai.choose_region_to_fortify(fortify_targets)
            if chosen_target:
                action_type = "fortify"
                target_region_id = chosen_target.region_id
                print(f"  AI {player_id} chooses to fortify region {target_region_id}")

        # If still no action, skip
        if action_type is None or target_region_id is None:
            print(f"  AI {player_id} has no good actions, skipping turn")
            return True

        # Execute the action
        self._execute_turn_action(player_id, target_region_id, action_type)
        return True

    def _execute_turn_action(self, player_id: int, region_id: int, action_type: str) -> bool:
        """
        Execute a turn action (attack or fortify).

        Args:
            player_id: ID of player executing action
            region_id: ID of target region
            action_type: "attack" or "fortify"

        Returns:
            True if action was successful
        """
        print(f"  Executing {action_type} action on region {region_id}...")

        if action_type == "attack":
            # Validate attack
            if not self.logic.can_attack_region(player_id, region_id):
                print(f"  Invalid attack attempt")
                return False

            # Trigger battle
            self._start_turn_battle(player_id, region_id)
            return True

        elif action_type == "fortify":
            # Validate fortify
            if not self.logic.can_fortify_region(player_id, region_id):
                print(f"  Invalid fortify attempt")
                return False

            # Execute fortification
            success = self.logic.fortify_region(player_id, region_id)

            if success:
                print(f"  Player {player_id} fortified region {region_id}")
                # Play sound if available
                if self.sound_manager:
                    self.sound_manager.play_sound("fortify")

                # Draw changes
                self.draw()
                pygame.time.delay(500)

            return success

        return False

    def _start_turn_battle(self, attacker_id: int, region_id: int) -> None:
        """
        Start a battle during turn phase.
        For capital regions: keep attacking until capital is destroyed or attacker loses.
        For normal regions: end turn after one battle.

        Args:
            attacker_id: ID of attacking player
            region_id: ID of region being attacked
        """
        region = self.state.regions[region_id]
        defender_id = region.owner_id

        if defender_id is None:
            print(f"  Error: Region {region_id} has no owner")
            return

        print(f"  Battle: Player {attacker_id} attacking {region.name} (owned by {defender_id})")

        # For capital attacks, loop until capital is destroyed or defender wins
        is_capital = region.region_type == RegionType.CAPITAL

        while True:
            # Set up battle state
            self.state.current_phase = GamePhase.CAPITAL_ATTACK if is_capital else GamePhase.BATTLE
            self.state.current_battle = BattleResult(
                attacker_id=attacker_id,
                defender_id=defender_id,
                region_id=region_id
            )

            # Start battle question flow (blocking)
            self.start_battle_question_flow()

            # If this was a capital attack, check if capital still exists
            if is_capital:
                # Check if the capital region still exists
                if region_id not in self.state.capitals:
                    # Capital was destroyed, turn ends
                    print(f"  Capital destroyed. Turn ends.")
                    break
                # Check if defender is still alive
                if not self.state.players[defender_id].is_alive:
                    # Defender eliminated, turn ends
                    print(f"  Defender eliminated. Turn ends.")
                    break
                # Check the result of the last battle
                if self.state.current_battle.winner_id != attacker_id:
                    # Attacker lost the last battle, turn ends
                    print(f"  Attack repelled. Turn ends.")
                    break
                # Attacker won but capital still has HP - ask another question
                print(f"  Capital damaged but not destroyed. Asking for another attack...")
                continue
            else:
                # Normal region attack - turn ends
                break

    def handle_turn_region_click(self, region_id: int) -> None:
        """Handle region click during turn phase for human player selection."""
        if not self.waiting_for_region_selection:
            return

        region = self.state.regions.get(region_id)
        if not region or not region.is_selectable:
            return

        # Determine action type based on region ownership
        if region.owner_id == self.current_selection_player:
            self.selected_action = "fortify"
        else:
            self.selected_action = "attack"

        self.selected_region_id = region_id
        self.waiting_for_region_selection = False
        print(f"  Human selected region {region_id} for {self.selected_action}")

    def start_battle_question_flow(self) -> Optional[BattleResult]:
        """
        Start the battle question flow.
        Gets answers from players and determines battle outcome.

        Returns:
            BattleResult with battle outcome, or None if no valid answers
        """
        if not self.state.current_battle:
            return None

        attacker_id = self.state.current_battle.attacker_id
        defender_id = self.state.current_battle.defender_id

        print(f"  Starting battle between {attacker_id} and {defender_id}")

        # Get a multiple choice question from loaded questions
        categories = self.config.get_included_categories()
        question = self._get_multiple_choice_question(categories)

        if not question:
            # Fallback question
            question = Question(
                id=0,
                text="What is the capital of France?",
                category="General Knowledge",
                question_type=QuestionType.MULTIPLE_CHOICE,
                correct_answer="Paris",
                options=["Paris", "London", "Berlin", "Madrid"]
            )

        # Store question for display
        self.battle_question = question
        print(f"  Battle question: {question.text}")

        # Get answers from both players
        attacker_answer = None
        defender_answer = None

        attacker = self.state.players[attacker_id]
        defender = self.state.players[defender_id]

        # Get attacker answer
        if attacker.player_type == PlayerType.HUMAN:
            attacker_answer = self._get_human_battle_answer(question)
        else:
            ai = self.ai_players.get(attacker_id)
            if ai:
                think_time = self.config.get_ai_think_time() / 1000.0
                attacker_answer = ai.answer_multiple_choice(question, think_time)

        # Get defender answer
        if defender.player_type == PlayerType.HUMAN:
            defender_answer = self._get_human_battle_answer(question)
        else:
            ai = self.ai_players.get(defender_id)
            if ai:
                think_time = self.config.get_ai_think_time() / 1000.0
                defender_answer = ai.answer_multiple_choice(question, think_time)

        # Resolve the battle
        result = None
        if attacker_answer is not None and defender_answer is not None:
            result = self.logic.resolve_battle(
                attacker_id=attacker_id,
                defender_id=defender_id,
                region_id=self.state.current_battle.region_id,
                question=question,
                attacker_answer=attacker_answer,
                defender_answer=defender_answer
            )

            # Check if tie in MC (both answered correctly)
            if result.winner_id is None:
                print("  Tie in multiple choice! Going to open answer tie-breaker...")
                result = self._resolve_battle_tie_with_open_answer(
                    attacker_id=attacker_id,
                    defender_id=defender_id,
                    region_id=self.state.current_battle.region_id
                )

            # Update current_battle with the result
            self.state.current_battle.winner_id = result.winner_id
            self.state.current_battle.region_captured = result.region_captured
            self.state.current_battle.defender_bonus_awarded = result.defender_bonus_awarded

            # Apply battle result
            self._apply_battle_result(result)

        return result

    def _get_human_battle_answer(self, question: Question) -> Optional[str]:
        """
        Get human player's answer for a battle question.

        Args:
            question: The question to answer

        Returns:
            Player's answer, or None if timeout
        """
        print("  Waiting for human player battle answer...")

        # Show question through screen manager
        if self.screen_manager and question:
            self.screen_manager.show_question(
                question=question,
                time_limit=30  # Default 30 second time limit for battle questions
            )

        # Wait for answer
        start_time = time.time()
        self.waiting_for_human_answer = True
        self.human_answer_value = None
        self.current_question_screen = "battle"

        while self.waiting_for_human_answer:
            elapsed = time.time() - start_time
            if elapsed > 30:  # 30 second timeout
                print("  Time's up for battle question!")
                self.waiting_for_human_answer = False
                break

            self.handle_events()
            self.update()
            self.draw()
            pygame.time.delay(10)

        answer = self.human_answer_value
        self.human_answer_value = None  # Reset for next question
        return answer

    def _resolve_battle_tie_with_open_answer(self, attacker_id: int, defender_id: int,
                                            region_id: int) -> BattleResult:
        """
        Resolve a tie in multiple choice with an open answer question.

        Args:
            attacker_id: ID of attacking player
            defender_id: ID of defending player
            region_id: ID of region being attacked

        Returns:
            BattleResult with winner determined by open answer proximity
        """
        # Get open answer question
        categories = self.config.get_included_categories()
        question = self._get_open_question(categories)

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

        print(f"  Tie-breaker question: {question.text}")

        # Get answers from both players (only these two)
        answers = {}
        answer_times = {}

        attacker = self.state.players[attacker_id]
        defender = self.state.players[defender_id]

        # Attacker's answer
        if attacker.player_type == PlayerType.HUMAN:
            answer = self._get_human_battle_open_answer(question)
        else:
            ai = self.ai_players.get(attacker_id)
            if ai:
                think_time = self.config.get_ai_think_time() / 1000.0
                answer = ai.answer_open_question(question, think_time)
            else:
                answer = None

        if answer is not None:
            answers[attacker_id] = answer
            answer_times[attacker_id] = time.time()

        # Defender's answer
        if defender.player_type == PlayerType.HUMAN:
            answer = self._get_human_battle_open_answer(question)
        else:
            ai = self.ai_players.get(defender_id)
            if ai:
                think_time = self.config.get_ai_think_time() / 1000.0
                answer = ai.answer_open_question(question, think_time)
            else:
                answer = None

        if answer is not None:
            answers[defender_id] = answer
            answer_times[defender_id] = time.time()

        # Resolve with open answer battle logic
        result = self.logic.resolve_open_answer_battle(
            attacker_id=attacker_id,
            defender_id=defender_id,
            region_id=region_id,
            question=question,
            answers=answers,
            answer_times=answer_times
        )

        return result

    def _get_human_battle_open_answer(self, question: Question) -> Optional[float]:
        """
        Get human player's answer for a tie-breaking open answer question.

        Args:
            question: The open answer question

        Returns:
            Player's numeric answer, or None if timeout
        """
        print("  Waiting for human player open answer (tie-breaker)...")

        # Show open answer question
        if self.screen_manager and question:
            self.screen_manager.show_open_question(
                question=question,
                time_limit=30  # 30 second timeout
            )

        # Wait for answer
        start_time = time.time()
        self.waiting_for_human_answer = True
        self.human_answer_value = None
        self.current_question_screen = "battle"

        while self.waiting_for_human_answer:
            elapsed = time.time() - start_time
            if elapsed > 30:  # 30 second timeout
                print("  Time's up for open answer tie-breaker!")
                self.waiting_for_human_answer = False
                return None

            self.handle_events()
            self.update()
            self.draw()
            pygame.time.delay(10)

        return self.human_answer_value

    def _apply_battle_result(self, result: BattleResult) -> None:
        """
        Apply battle result to game state.

        Args:
            result: BattleResult with winner and outcome
        """
        if result.winner_id is None:
            print("  Battle result: TIE - no winner determined")
            return

        winner = self.state.players.get(result.winner_id)
        if winner is None:
            print("  Error: Winner not found")
            return

        region = self.state.regions.get(result.region_id)

        if region is None:
            print("  Error: Region not found")
            return

        print(f"  Battle result: {winner.name} wins!")

        # Check if this is a capital attack
        if self.state.current_phase == GamePhase.CAPITAL_ATTACK:
            # Handle capital attack
            self.logic.execute_capital_attack(result.attacker_id, result.region_id, result)
            return

        # If attacker wins, capture the region
        if result.winner_id == result.attacker_id and result.region_captured:
            print(f"  Capturing region {region.name}...")
            old_owner_id = region.owner_id

            # Update region ownership
            region.owner_id = result.attacker_id
            region.fortification = FortificationLevel.NONE  # Reset fortification

            # Update player regions
            if old_owner_id is not None:
                old_owner = self.state.players[old_owner_id]
                if result.region_id in old_owner.regions_controlled:
                    old_owner.remove_region(result.region_id)

            attacker = self.state.players[result.attacker_id]
            attacker.add_region(result.region_id)

            # Award points (doubled if special round)
            points = self.logic.calculate_region_value(region)
            earned_points = points * 2 if self.state.is_special_round else points
            attacker.score += earned_points

            if self.state.is_special_round:
                print(f"  {attacker.name} gained {earned_points} points (SPECIAL ROUND - doubled!)")
            else:
                print(f"  {attacker.name} gained {earned_points} points")

        # Award defender bonus if they won
        if result.defender_bonus_awarded and result.winner_id == result.defender_id:
            defender = self.state.players[result.defender_id]
            bonus_points = 50  # Fixed defender bonus
            earned_bonus = bonus_points * 2 if self.state.is_special_round else bonus_points
            defender.score += earned_bonus
            if self.state.is_special_round:
                print(f"  {defender.name} earned {earned_bonus} defender bonus points (SPECIAL ROUND - doubled!)")
            else:
                print(f"  {defender.name} earned {earned_bonus} defender bonus points")

    def end_turn_phase(self) -> None:
        """
        End the turn phase and determine game outcome.
        """
        print("\n=== END TURN PHASE ===")

        # Check for winner
        winner = self.logic.check_game_over()

        if winner is not None:
            print(f"\n*** GAME OVER ***")
            print(f"Player {winner} ({self.state.players[winner].name}) wins!")
            self.state.current_phase = GamePhase.GAME_OVER
        else:
            # More rounds could happen, but for now move to game over
            print("Turn phase complete. Game ending...")
            self.state.current_phase = GamePhase.GAME_OVER

    def run(self) -> None:
        """Main game loop."""
        self.running = True

        while self.running:
            # If setup screen not confirmed, show menu
            if not self.game_settings_confirmed:
                self.show_setup_screen()
                continue

            # If game is over, show game over screen
            if self.state.current_phase == GamePhase.GAME_OVER:
                self.show_game_over_screen()
                continue

            # Handle events
            self.handle_events()

            # Update game state
            self.update()

            # Draw everything
            self.draw()

            # Cap the frame rate
            self.clock.tick(self.config.fps)