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
        self.selected_ai_count: int = 2
        self.selected_difficulty: Difficulty = Difficulty.MEDIUM
        self.selected_categories: List[str] = config.selected_categories.copy()
        self.category_mode: CategorySelectionMode = CategorySelectionMode.INCLUDE
        self.selected_region_count: int = config.region_count
        self.selected_turns: int = config.turns_per_player
        
        # UI state
        self.show_category_selection: bool = False
        self.is_dragging_slider: Optional[str] = None
        
        # Initialize UI
        self._create_ui()
    
    def _load_fonts(self) -> None:
        """Load fonts."""
        for size_name, size in self.config.font_sizes.items():
            self.fonts[size_name] = pygame.font.SysFont(self.config.font_name, size)
    
    def _create_ui(self) -> None:
        """Create menu UI elements."""
        screen_width = self.config.screen_width
        screen_height = self.config.screen_height
        
        # Clear existing UI
        self.buttons.clear()
        self.sliders.clear()
        self.dropdowns.clear()
        
        # Title
        # (No button for title, just text)
        
        # Start Game button
        start_rect = pygame.Rect(screen_width // 2 - 100, screen_height - 100, 200, 50)
        self.buttons.append(MenuButton(start_rect, "Start Game", "start"))
        
        # Settings buttons
        settings_y = 150
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
        
        # Exit button
        exit_rect = pygame.Rect(20, screen_height - 50, 100, 30)
        self.buttons.append(MenuButton(exit_rect, "Exit", "exit"))
    
    def draw(self) -> None:
        """Draw the menu screen."""
        # Draw background
        self.screen.fill(self.colors.background)
        
        # Draw title
        self._draw_title()
        
        # Draw buttons
        self._draw_buttons()
        
        # Draw sliders
        self._draw_sliders()
        
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
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            
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
            
        elif action == "exit":
            # Exit game - would be handled by main game
            print("Exit clicked")
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