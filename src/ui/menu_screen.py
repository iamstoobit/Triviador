from __future__ import annotations
import pygame
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from src.utils.config import GameConfig, Difficulty, CategorySelectionMode
from src.utils.helpers import draw_text, draw_button


@dataclass
class MenuButton:
    """Represents a menu button."""
    rect: pygame.Rect
    text: str
    action: str
    hover: bool = False


class MenuScreen:
    """
    Main menu screen for game setup.
    """

    def __init__(self, screen: pygame.Surface, config: GameConfig):
        """
        Initialize menu screen.

        Args:
            screen: Pygame surface to draw on
            config: Game configuration
        """
        self.screen = screen
        self.config = config
        self.colors = config.colors

        # Fonts
        self.fonts: Dict[str, pygame.font.Font] = {}
        self._load_fonts()

        # Menu state
        self.buttons: List[MenuButton] = []
        self.sliders: Dict[str, pygame.Rect] = {}
        self.dropdowns: Dict[str, Dict] = {}

        # Game settings (defaults)
        self.player_name: str = "Player"
        self.selected_ai_count: int = 2
        self.selected_difficulty: Difficulty = Difficulty.MEDIUM
        self.selected_categories: List[str] = config.selected_categories.copy()
        self.category_mode: CategorySelectionMode = CategorySelectionMode.INCLUDE
        self.selected_region_count: int = config.region_count
        self.selected_turns: int = config.turns_per_player

        # UI state
        self.show_category_selection: bool = False
        self.is_dragging_slider: Optional[str] = None
        self.name_input_active: bool = False  # Is player entering name
        self.name_input_rect: Optional[pygame.Rect] = None

        # Game records display
        self.game_records: List[Dict] = []
        self.records_scroll_offset: int = 0
        self.records_mode: str = "normal"  # "normal" or "endless"
        self._load_game_records()

        # Initialize UI
        self._create_ui()

    def _load_fonts(self) -> None:
        """Load fonts."""
        for size_name, size in self.config.font_sizes.items():
            self.fonts[size_name] = pygame.font.SysFont(self.config.font_name, size)

    def _load_game_records(self) -> None:
        """Load top 10 game records for the current mode."""
        try:
            from src.utils.game_recorder import GameRecorder
            self.game_records = GameRecorder.get_top_games(count=10, mode=self.records_mode)
        except Exception as e:
            print(f"Warning: Could not load game records: {e}")
            self.game_records = []

    def _create_ui(self) -> None:
        """Create menu UI elements."""
        screen_width = self.config.screen_width
        screen_height = self.config.screen_height

        # Clear existing UI
        self.buttons.clear()
        self.sliders.clear()
        self.dropdowns.clear()

        # Player Name input
        self.name_input_rect = pygame.Rect(screen_width // 2 - 150, 170, 300, 35)

        # Endless mode button
        endless_rect = pygame.Rect(20, 20, 120, 40)
        self.buttons.append(MenuButton(endless_rect, "Endless Mode", "endless"))

        # Start Game button (below Endless)
        start_rect = pygame.Rect(20, 70, 120, 40)
        self.buttons.append(MenuButton(start_rect, "Start Game", "start"))

        # Settings buttons
        settings_y = 230
        button_spacing = 70

        # AI Count
        ai_rect = pygame.Rect(screen_width // 2 - 200, settings_y, 400, 40)
        self.buttons.append(MenuButton(ai_rect, f"AI Opponents: {self.selected_ai_count}", "toggle_ai"))

        # Difficulty
        diff_rect = pygame.Rect(screen_width // 2 - 200, settings_y + button_spacing, 400, 40)
        self.buttons.append(MenuButton(diff_rect, f"Difficulty: {self.selected_difficulty.value}", "toggle_difficulty"))

        # Categories
        cat_rect = pygame.Rect(screen_width // 2 - 200, settings_y + button_spacing * 2, 400, 40)
        cat_text = f"Categories: {self.category_mode.value.capitalize()} {len(self.selected_categories)}"
        self.buttons.append(MenuButton(cat_rect, cat_text, "toggle_categories"))

        # Region Count slider
        region_text_rect = pygame.Rect(screen_width // 2 - 200, settings_y + button_spacing * 3, 180, 40)
        self.buttons.append(MenuButton(region_text_rect, f"Regions: {self.selected_region_count}", "region_slider"))

        region_slider_rect = pygame.Rect(screen_width // 2 - 10, settings_y + button_spacing * 3 + 15, 210, 10)
        self.sliders["regions"] = region_slider_rect

        # Turns slider
        turns_text_rect = pygame.Rect(screen_width // 2 - 200, settings_y + button_spacing * 4, 180, 40)
        self.buttons.append(MenuButton(turns_text_rect, f"Turns: {self.selected_turns}", "turns_slider"))

        turns_slider_rect = pygame.Rect(screen_width // 2 - 10, settings_y + button_spacing * 4 + 15, 210, 10)
        self.sliders["turns"] = turns_slider_rect

    def draw(self) -> None:
        """Draw the menu screen."""
        # Draw background
        self.screen.fill(self.colors.background)

        # Draw title
        self._draw_title()

        # Draw player name input
        self._draw_name_input()

        # Draw buttons
        self._draw_buttons()

        # Draw sliders
        self._draw_sliders()

        # Draw game records at bottom
        self._draw_game_records()

        # Draw category selection if open
        if self.show_category_selection:
            self._draw_category_selection()

    def _draw_title(self) -> None:
        """Draw menu title."""
        title_font = self.fonts["title"]
        subtitle_font = self.fonts["subheading"]

        draw_text(self.screen, "TRIVIADOR",
                 (self.config.screen_width // 2, 80),
                 title_font, self.colors.text_accent)

        draw_text(self.screen, "Trivia Conquest Game",
                 (self.config.screen_width // 2, 120),
                 subtitle_font, self.colors.text_secondary)

    def _draw_name_input(self) -> None:
        """Draw player name input field."""
        if not self.name_input_rect:
            return

        # Draw label
        label_font = self.fonts["body"]
        draw_text(
            self.screen,
            "Enter Your Name:",
            (self.config.screen_width // 2, 145),
            label_font,
            self.colors.text_primary
        )

        # Draw input box background
        pygame.draw.rect(
            self.screen,
            (255, 255, 255),
            self.name_input_rect,
            border_radius=5
        )

        # Draw border
        border_color = (
            self.colors.text_accent
            if self.name_input_active
            else self.colors.text_primary
        )
        pygame.draw.rect(
            self.screen,
            border_color,
            self.name_input_rect,
            2,
            border_radius=5
        )

        # Draw text
        text_font = self.fonts["body"]
        display_text = self.player_name if self.player_name else "Enter name..."
        text_color = (
            self.colors.text_primary
            if self.player_name
            else self.colors.text_secondary
        )
        draw_text(
            self.screen,
            display_text,
            (self.name_input_rect.x + 10, self.name_input_rect.centery),
            text_font,
            text_color,
            centered=False
        )

        # Draw cursor if active
        if self.name_input_active:
            cursor_x = (
                self.name_input_rect.x + 15 +
                text_font.size(self.player_name)[0]
            )
            pygame.draw.line(
                self.screen,
                self.colors.text_accent,
                (cursor_x, self.name_input_rect.y + 8),
                (cursor_x, self.name_input_rect.y + 27),
                2
            )

    def _draw_buttons(self) -> None:
        """Draw all menu buttons."""
        for button in self.buttons:
            draw_button(self.screen, button.rect, button.text,
                       self.fonts["body"],
                       self.colors.button_normal,
                       self.colors.button_hover,
                       self.colors.text_primary,
                       button.hover)

    def _draw_sliders(self) -> None:
        """Draw slider controls."""
        for slider_name, slider_rect in self.sliders.items():
            # Draw slider track
            pygame.draw.rect(self.screen, self.colors.button_disabled,
                           slider_rect, border_radius=5)

            # Draw slider handle
            if slider_name == "regions":
                value = self.selected_region_count
                min_val = self.config.min_regions
                max_val = self.config.max_regions
            else:  # "turns"
                value = self.selected_turns
                min_val = self.config.min_turns_per_player
                max_val = self.config.max_turns_per_player

            # Calculate handle position
            ratio = (value - min_val) / (max_val - min_val)
            handle_x = slider_rect.x + ratio * slider_rect.width
            handle_rect = pygame.Rect(handle_x - 10, slider_rect.y - 10, 20, 30)

            # Draw handle
            pygame.draw.rect(self.screen, self.colors.button_normal,
                           handle_rect, border_radius=5)
            pygame.draw.rect(self.screen, self.colors.text_primary,
                           handle_rect, 2, border_radius=5)

    def _draw_game_records(self) -> None:
        """Draw top game records at the bottom of the screen."""
        # Records section area
        records_height = 100
        records_y = self.config.screen_height - records_height - 10
        records_x = 20
        records_width = self.config.screen_width - 40

        # Draw background panel
        pygame.draw.rect(
            self.screen,
            self.colors.panel,
            (records_x, records_y, records_width, records_height),
            border_radius=8
        )
        pygame.draw.rect(
            self.screen,
            self.colors.text_secondary,
            (records_x, records_y, records_width, records_height),
            2,
            border_radius=8
        )

        # Draw title with mode
        title_font = self.fonts["small"]
        mode_text = "Endless" if self.records_mode == "endless" else "Classic"
        title_text = f"Top Scores ({mode_text} Mode) - Click to switch"
        draw_text(
            self.screen,
            title_text,
            (records_x + 15, records_y + 8),
            title_font,
            self.colors.text_accent,
            centered=False
        )

        # Store clickable area for mode toggle
        self.records_title_rect = pygame.Rect(records_x, records_y, records_width, 20)

        # Draw records with scrolling
        record_font = self.fonts["small"]
        record_height = 16
        visible_records = 4
        max_scroll = max(0, len(self.game_records) - visible_records)

        # Clamp scroll offset
        self.records_scroll_offset = max(0, min(self.records_scroll_offset, max_scroll))

        records_y_start = records_y + 25
        for i in range(visible_records):
            record_idx = i + self.records_scroll_offset

            if record_idx >= len(self.game_records):
                break

            record = self.game_records[record_idx]
            record_y = records_y_start + i * record_height

            # Draw rank, name, and score
            rank_text = f"{record_idx + 1}."
            name_text = record['username'][:15]  # Truncate long names
            score_text = str(record['score'])

            # Draw rank
            draw_text(
                self.screen,
                rank_text,
                (records_x + 20, record_y),
                record_font,
                self.colors.text_primary,
                centered=False
            )

            # Draw name
            draw_text(
                self.screen,
                name_text,
                (records_x + 50, record_y),
                record_font,
                self.colors.text_primary,
                centered=False
            )

            # Draw score (right-aligned)
            draw_text(
                self.screen,
                score_text,
                (records_x + records_width - 30, record_y),
                record_font,
                self.colors.text_accent,
                centered=False
            )

    def _draw_category_selection(self) -> None:
        """Draw category selection overlay."""
        # Draw overlay background
        overlay = pygame.Surface((self.config.screen_width, self.config.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))

        # Draw selection window
        window_width = 600
        window_height = 500
        window_x = (self.config.screen_width - window_width) // 2
        window_y = (self.config.screen_height - window_height) // 2

        pygame.draw.rect(self.screen, self.colors.panel,
                        (window_x, window_y, window_width, window_height),
                        border_radius=10)
        pygame.draw.rect(self.screen, self.colors.text_primary,
                        (window_x, window_y, window_width, window_height),
                        2, border_radius=10)

        # Draw title
        title_font = self.fonts["heading"]
        draw_text(self.screen, "Select Categories",
                 (self.config.screen_width // 2, window_y + 30),
                 title_font, self.colors.text_primary)

        # Draw mode selector
        mode_font = self.fonts["body"]
        mode_text = f"Mode: {self.category_mode.value.capitalize()} (click to toggle)"
        draw_text(self.screen, mode_text,
                 (self.config.screen_width // 2, window_y + 70),
                 mode_font, self.colors.text_accent)

        # Draw categories
        category_font = self.fonts["small"]
        x_start = window_x + 50
        y_start = window_y + 110

        for i, category in enumerate(self.config.available_categories):
            # Calculate position
            col = i % 2
            row = i // 2

            x = x_start + col * 250
            y = y_start + row * 35

            # Determine color
            is_selected = category in self.selected_categories
            color = self.colors.correct_answer if is_selected else self.colors.text_secondary

            # Draw category checkbox
            checkbox_rect = pygame.Rect(x - 25, y - 10, 20, 20)
            pygame.draw.rect(self.screen, color, checkbox_rect, 2, border_radius=3)

            if is_selected:
                # Draw checkmark
                pygame.draw.line(self.screen, color,
                               (x - 22, y), (x - 18, y + 4), 2)
                pygame.draw.line(self.screen, color,
                               (x - 18, y + 4), (x - 13, y - 3), 2)

            # Draw category name
            draw_text(self.screen, category,
                     (x, y),
                     category_font, color, centered=False)

        # Draw close button
        close_rect = pygame.Rect(window_x + window_width - 120,
                                window_y + window_height - 50,
                                100, 30)
        draw_button(self.screen, close_rect, "Close",
                   self.fonts["body"],
                   self.colors.button_normal,
                   self.colors.button_hover,
                   self.colors.text_primary)

        # Store close button for event handling
        self.close_button_rect = close_rect

    def update(self) -> None:
        """Update menu screen state."""
        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()

        for button in self.buttons:
            button.hover = button.rect.collidepoint(mouse_pos)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.

        Args:
            event: Pygame event

        Returns:
            True if event was handled
        """
        if self.show_category_selection:
            return self._handle_category_selection_event(event)

        # Handle name input field events
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check if clicking on name input field
            if self.name_input_rect and self.name_input_rect.collidepoint(mouse_pos):
                self.name_input_active = True
                return True
            else:
                self.name_input_active = False

        # Handle keyboard input for name
        if event.type == pygame.KEYDOWN and self.name_input_active:
            if event.key == pygame.K_BACKSPACE:
                self.player_name = self.player_name[:-1]
                return True
            elif event.key == pygame.K_RETURN:
                self.name_input_active = False
                return True
            elif event.unicode.isprintable():
                # Limit name length to 20 characters
                if len(self.player_name) < 20:
                    self.player_name += event.unicode
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check if clicking on scoreboard title to toggle mode
            if hasattr(self, 'records_title_rect') and self.records_title_rect.collidepoint(mouse_pos):
                self.records_mode = "endless" if self.records_mode == "normal" else "normal"
                self.records_scroll_offset = 0
                self._load_game_records()
                return True

            # Check sliders FIRST (before buttons) so they can be dragged directly
            for slider_name, slider_rect in self.sliders.items():
                # Make clickable area slightly larger (extend above and below slider)
                extended_rect = slider_rect.inflate(0, 40)
                if extended_rect.collidepoint(mouse_pos):
                    self.is_dragging_slider = slider_name
                    self._update_slider_value(slider_name, mouse_pos[0])
                    return True

            # Check buttons
            for button in self.buttons:
                if button.rect.collidepoint(mouse_pos):
                    # Skip button click if it's a slider text button and we're in the slider area
                    if button.action in ["region_slider", "turns_slider"]:
                        # Only trigger button action if not on the actual slider area
                        slider_name = "regions" if button.action == "region_slider" else "turns"
                        slider_rect = self.sliders[slider_name]
                        extended_rect = slider_rect.inflate(0, 40)
                        if not extended_rect.collidepoint(mouse_pos):
                            return self._handle_button_click(button.action)
                        return False
                    return self._handle_button_click(button.action)

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_dragging_slider = None

        elif event.type == pygame.MOUSEMOTION and self.is_dragging_slider:
            self._update_slider_value(self.is_dragging_slider, event.pos[0])
            return True

        # Handle scroll wheel for game records
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # Scroll up
                self.records_scroll_offset = max(0, self.records_scroll_offset - 1)
                return True
            elif event.button == 5:  # Scroll down
                max_scroll = max(0, len(self.game_records) - 4)
                self.records_scroll_offset = min(max_scroll, self.records_scroll_offset + 1)
                return True

        return False

    def _handle_category_selection_event(self, event: pygame.event.Event) -> bool:
        """Handle events in category selection overlay."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Check close button
            if hasattr(self, 'close_button_rect') and self.close_button_rect.collidepoint(mouse_pos):
                self.show_category_selection = False
                return True

            # Check mode toggle (title area)
            window_width = 600
            window_height = 500
            window_x = (self.config.screen_width - window_width) // 2
            window_y = (self.config.screen_height - window_height) // 2

            mode_rect = pygame.Rect(window_x, window_y + 60, window_width, 40)
            if mode_rect.collidepoint(mouse_pos):
                # Toggle mode
                if self.category_mode == CategorySelectionMode.INCLUDE:
                    self.category_mode = CategorySelectionMode.EXCLUDE
                else:
                    self.category_mode = CategorySelectionMode.INCLUDE

                # Update UI
                self._create_ui()
                return True

            # Check category checkboxes
            x_start = window_x + 50
            y_start = window_y + 110

            for i, category in enumerate(self.config.available_categories):
                col = i % 2
                row = i // 2

                x = x_start + col * 250
                y = y_start + row * 35

                checkbox_rect = pygame.Rect(x - 25, y - 10, 20, 20)
                if checkbox_rect.collidepoint(mouse_pos):
                    # Toggle category selection
                    if category in self.selected_categories:
                        self.selected_categories.remove(category)
                    else:
                        self.selected_categories.append(category)

                    # Sort to keep order consistent
                    self.selected_categories.sort()

                    # Update UI
                    self._create_ui()
                    return True

        return False

    def _handle_button_click(self, action: str) -> bool:
        """Handle button clicks."""
        if action == "start":
            # Start game - this would be handled by the main game
            print("Start game clicked")
            return True

        elif action == "toggle_ai":
            # Cycle AI count: 1 → 2 → 3 → 1
            self.selected_ai_count = (self.selected_ai_count % 3) + 1
            self._create_ui()
            return True

        elif action == "toggle_difficulty":
            # Cycle difficulty: EASY → MEDIUM → HARD → EASY
            difficulties = list(Difficulty)
            current_idx = difficulties.index(self.selected_difficulty)
            next_idx = (current_idx + 1) % len(difficulties)
            self.selected_difficulty = difficulties[next_idx]
            self._create_ui()
            return True

        elif action == "toggle_categories":
            # Show category selection
            self.show_category_selection = True
            return True

        elif action == "region_slider":
            # Clicked on region text - center the value
            self.selected_region_count = (self.config.min_regions + self.config.max_regions) // 2
            self._create_ui()
            return True

        elif action == "turns_slider":
            # Clicked on turns text - center the value
            self.selected_turns = (self.config.min_turns_per_player + self.config.max_turns_per_player) // 2
            self._create_ui()
            return True

        elif action == "endless":
            # Start endless mode - would be handled by main game
            print("Endless mode clicked")
            return True

        return False

    def _update_slider_value(self, slider_name: str, mouse_x: int) -> None:
        """Update slider value based on mouse position."""
        slider_rect = self.sliders[slider_name]

        # Calculate ratio (0 to 1)
        ratio = (mouse_x - slider_rect.x) / slider_rect.width
        ratio = max(0.0, min(1.0, ratio))

        if slider_name == "regions":
            min_val = self.config.min_regions
            max_val = self.config.max_regions
            value = min_val + int(ratio * (max_val - min_val))
            self.selected_region_count = value

        else:  # "turns"
            min_val = self.config.min_turns_per_player
            max_val = self.config.max_turns_per_player
            value = min_val + int(ratio * (max_val - min_val))
            self.selected_turns = value

        # Update UI
        self._create_ui()

    def get_settings(self) -> dict[str, Any]:
        """
        Get current menu settings.

        Returns:
            Dictionary with game settings
        """
        return {
            'player_name': self.player_name,
            'ai_count': self.selected_ai_count,
            'difficulty': self.selected_difficulty,
            'selected_categories': self.selected_categories.copy(),
            'category_mode': self.category_mode,
            'region_count': self.selected_region_count,
            'turns_per_player': self.selected_turns
        }


if __name__ == "__main__":
    print("=== Testing MenuScreen ===")

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    # Create config
    from src.utils.config import GameConfig
    config = GameConfig(screen_width=800, screen_height=600)

    # Create menu screen
    menu_screen = MenuScreen(screen, config)

    # Draw test screen
    menu_screen.draw()
    pygame.display.flip()

    pygame.time.delay(1000)
    pygame.quit()

    print("All tests passed!")