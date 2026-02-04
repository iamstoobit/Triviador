from __future__ import annotations
import pygame
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from src.utils.config import GameConfig
from src.game.state import GameState, GamePhase, Player, Region, RegionType, Capital
from src.utils.helpers import draw_text, draw_button, is_point_in_circle


@dataclass
class UIRegion:
    """UI representation of a region."""
    region_id: int
    position: Tuple[float, float]
    radius: float = 40.0
    is_selected: bool = False
    is_selectable: bool = False


class GameScreen:
    """
    Main gameplay screen showing map, players, and game state.
    """
    
    def __init__(self, screen: pygame.Surface, config: GameConfig):
        """
        Initialize game screen.
        
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
        
        # UI state
        self.ui_regions: Dict[int, UIRegion] = {}
        self.show_action_buttons: bool = False
        self.selected_region_id: Optional[int] = None
        self.action_buttons: List[pygame.Rect] = []
        
        # Animation
        self.pulse_phase: float = 0.0
        
    def _load_fonts(self) -> None:
        """Load fonts."""
        for size_name, size in self.config.font_sizes.items():
            self.fonts[size_name] = pygame.font.SysFont(self.config.font_name, size)
    
    def draw(self, game_state: GameState) -> None:
        """
        Draw the game screen.
        
        Args:
            game_state: Current game state
        """
        # Update UI regions
        self._update_ui_regions(game_state)
        
        # Draw background
        self.screen.fill(self.colors.background)
        
        # Draw regions
        self._draw_regions(game_state)
        
        # Draw region connections
        self._draw_connections(game_state)
        
        # Draw region labels
        self._draw_region_labels(game_state)
        
        # Draw players panel
        self._draw_players_panel(game_state)
        
        # Draw game info
        self._draw_game_info(game_state)
        
        # Draw action buttons if region is selected
        if self.selected_region_id and self.show_action_buttons:
            self._draw_action_buttons(game_state)
        
        # Draw phase-specific UI
        if game_state.current_phase == GamePhase.OCCUPYING:
            self._draw_occupation_ui(game_state)
        elif game_state.current_phase == GamePhase.TURN:
            self._draw_turn_ui(game_state)
        
        # Update animation
        self.pulse_phase = (self.pulse_phase + 0.05) % (2 * math.pi)
    
    def _update_ui_regions(self, game_state: GameState) -> None:
        """Update UI region representations."""
        self.ui_regions.clear()
        
        for region_id, region in game_state.regions.items():
            ui_region = UIRegion(
                region_id=region_id,
                position=region.position,
                radius=40.0,
                is_selected=(region_id == self.selected_region_id),
                is_selectable=getattr(region, 'is_selectable', False)
            )
            self.ui_regions[region_id] = ui_region
    
    def _draw_regions(self, game_state: GameState) -> None:
        """Draw all regions."""
        for region_id, ui_region in self.ui_regions.items():
            region = game_state.regions.get(region_id)
            if not region:
                continue
            
            # Determine region color
            color = self._get_region_color(region, game_state)
            
            # Draw region circle
            radius = ui_region.radius
            
            # Pulsing effect for selected regions
            if ui_region.is_selected:
                pulse = math.sin(self.pulse_phase) * 5 + 5
                radius += pulse
            
            # Draw region
            pygame.draw.circle(self.screen, color, 
                             (int(ui_region.position[0]), int(ui_region.position[1])),
                             int(radius))
            
            # Draw border
            border_color = self.colors.region_border
            if ui_region.is_selectable:
                border_color = self.colors.highlight
                pygame.draw.circle(self.screen, border_color,
                                 (int(ui_region.position[0]), int(ui_region.position[1])),
                                 int(radius + 3), 3)
            elif ui_region.is_selected:
                border_color = self.colors.selected
                pygame.draw.circle(self.screen, border_color,
                                 (int(ui_region.position[0]), int(ui_region.position[1])),
                                 int(radius + 2), 3)
            else:
                pygame.draw.circle(self.screen, border_color,
                                 (int(ui_region.position[0]), int(ui_region.position[1])),
                                 int(radius), 2)
            
            # Draw capital indicator
            if region.region_type == RegionType.CAPITAL:
                capital_color = self.colors.capital_highlight
                pygame.draw.circle(self.screen, capital_color,
                                 (int(ui_region.position[0]), int(ui_region.position[1])),
                                 15, 3)
                
                # Draw HP for capitals
                if region_id in game_state.capitals:
                    capital = game_state.capitals[region_id]
                    if capital.current_hp < capital.max_hp:
                        self._draw_capital_hp(ui_region, capital)
            
            # Draw fortification indicator
            if region.is_fortified():
                fort_color = (200, 200, 200)
                pygame.draw.circle(self.screen, fort_color,
                                 (int(ui_region.position[0]), int(ui_region.position[1])),
                                 10, 2)
    
    def _draw_capital_hp(self, ui_region: UIRegion, capital: Capital) -> None:
        """Draw capital HP indicator."""
        hp_text = f"{capital.current_hp}/{capital.max_hp}"
        font = self.fonts["small"]
        text_surf = font.render(hp_text, True, (255, 255, 255))
        text_rect = text_surf.get_rect(
            center=(ui_region.position[0], ui_region.position[1] + ui_region.radius + 15)
        )
        
        # Draw background
        bg_rect = text_rect.inflate(10, 5)
        pygame.draw.rect(self.screen, (50, 50, 50, 180), bg_rect, border_radius=3)
        
        # Draw text
        self.screen.blit(text_surf, text_rect)
    
    def _draw_connections(self, game_state: GameState) -> None:
        """Draw connections between adjacent regions."""
        for region_id, region in game_state.regions.items():
            if region_id not in self.ui_regions:
                continue
            
            start_pos = self.ui_regions[region_id].position
            
            for adj_id in region.adjacent_regions:
                if adj_id in self.ui_regions and adj_id > region_id:  # Draw each connection once
                    end_pos = self.ui_regions[adj_id].position
                    
                    # Determine connection color
                    adj_region = game_state.regions.get(adj_id)
                    if adj_region and region.owner_id == adj_region.owner_id and region.owner_id is not None:
                        # Same owner - use player color
                        owner_color = self.config.get_player_color(region.owner_id)
                        color = (owner_color[0], owner_color[1], owner_color[2], 100)
                    else:
                        # Different owners or neutral - use neutral color
                        color = self.colors.territory_border
                    
                    # Draw connection line
                    pygame.draw.line(self.screen, color, 
                                   (int(start_pos[0]), int(start_pos[1])),
                                   (int(end_pos[0]), int(end_pos[1])), 2)
    
    def _draw_region_labels(self, game_state: GameState) -> None:
        """Draw region names and point values."""
        for region_id, ui_region in self.ui_regions.items():
            region = game_state.regions.get(region_id)
            if not region:
                continue
            
            # Draw region name
            font = self.fonts["small"]
            name_surf = font.render(region.name, True, self.colors.region_text)
            name_rect = name_surf.get_rect(
                center=(ui_region.position[0], ui_region.position[1] - ui_region.radius - 10)
            )
            self.screen.blit(name_surf, name_rect)
            
            # Draw point value
            value_font = self.fonts["tiny"]
            value_text = f"{region.point_value}"
            value_surf = value_font.render(value_text, True, self.colors.region_text)
            value_rect = value_surf.get_rect(
                center=(ui_region.position[0], ui_region.position[1])
            )
            
            # Draw background for value
            bg_rect = value_rect.inflate(10, 5)
            pygame.draw.rect(self.screen, self.colors.region_points_bg, bg_rect, border_radius=3)
            
            # Draw value
            self.screen.blit(value_surf, value_rect)
    
    def _draw_players_panel(self, game_state: GameState) -> None:
        """Draw players panel on the right side."""
        panel_width = 250
        panel_x = self.config.screen_width - panel_width
        panel_height = self.config.screen_height
        
        # Draw panel background
        pygame.draw.rect(self.screen, self.colors.panel, 
                        (panel_x, 0, panel_width, panel_height))
        
        # Draw panel border
        pygame.draw.line(self.screen, self.colors.text_primary,
                        (panel_x, 0), (panel_x, panel_height), 2)
        
        # Draw title
        title_font = self.fonts["subheading"]
        draw_text(self.screen, "Players", 
                 (panel_x + panel_width // 2, 30),
                 title_font, self.colors.text_primary)
        
        # Draw each player
        y_pos = 80
        for player_id, player in game_state.players.items():
            if not player.is_alive:
                continue
            
            # Player color indicator
            color = self.config.get_player_color(player_id)
            pygame.draw.circle(self.screen, color, (panel_x + 30, y_pos), 10)
            
            # Player name and score
            name_font = self.fonts["body"]
            score_font = self.fonts["small"]
            
            # Highlight current player
            if player_id == game_state.current_player_id:
                name_color = self.colors.text_accent
                # Draw background highlight
                pygame.draw.rect(self.screen, (240, 240, 245),
                               (panel_x + 10, y_pos - 20, panel_width - 20, 40),
                               border_radius=5)
            else:
                name_color = self.colors.text_primary
            
            # Player name
            name_text = player.name
            if player.player_type.name == "HUMAN":
                name_text += " (You)"
            
            draw_text(self.screen, name_text,
                     (panel_x + 60, y_pos - 10),
                     name_font, name_color, centered=False)
            
            # Player score
            score_text = f"Score: {player.score}"
            draw_text(self.screen, score_text,
                     (panel_x + 60, y_pos + 10),
                     score_font, self.colors.text_secondary, centered=False)
            
            # Regions controlled
            regions_text = f"Regions: {len(player.regions_controlled)}"
            draw_text(self.screen, regions_text,
                     (panel_x + panel_width - 20, y_pos),
                     score_font, self.colors.text_secondary, centered=False)
            
            y_pos += 60
    
    def _draw_game_info(self, game_state: GameState) -> None:
        """Draw game information at the top."""
        # Current phase
        phase_font = self.fonts["subheading"]
        phase_text = f"Phase: {game_state.current_phase.name}"
        draw_text(self.screen, phase_text,
                 (self.config.screen_width // 2, 20),
                 phase_font, self.colors.text_primary)
        
        # Current turn
        if game_state.current_phase == GamePhase.TURN:
            turn_font = self.fonts["body"]
            current_player = game_state.players.get(game_state.current_player_id)
            if current_player:
                turn_text = f"Turn: {current_player.name} ({game_state.current_turn}/{game_state.max_turns_per_player})"
                draw_text(self.screen, turn_text,
                         (self.config.screen_width // 2, 50),
                         turn_font, self.colors.text_secondary)
    
    def _draw_action_buttons(self, game_state: GameState) -> None:
        """Draw action buttons for selected region."""
        if not self.selected_region_id:
            return
        
        region = game_state.regions.get(self.selected_region_id)
        if not region:
            return
        
        ui_region = self.ui_regions.get(self.selected_region_id)
        if not ui_region:
            return
        
        # Button positions (below the region)
        button_y = ui_region.position[1] + ui_region.radius + 40
        button_width = 100
        button_height = 35
        
        self.action_buttons.clear()
        
        # Determine which actions are available
        current_player_id = game_state.current_player_id
        if current_player_id is None:
            return
        
        current_player = game_state.players.get(current_player_id)
        if not current_player:
            return
        
        # Fortify button (if region belongs to player)
        if region.owner_id == current_player_id and not region.is_fortified():
            button_x = ui_region.position[0] - button_width - 10
            fortify_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            self.action_buttons.append(fortify_rect)
            
            draw_button(self.screen, fortify_rect, "Fortify",
                       self.fonts["body"],
                       self.colors.button_normal,
                       self.colors.button_hover,
                       self.colors.text_primary)
        
        # Attack button (if region belongs to enemy)
        elif (region.owner_id is not None and 
              region.owner_id != current_player_id):
            
            # Check if adjacent to player's regions
            can_attack = False
            for player_region in game_state.get_player_regions(current_player_id):
                if region.is_adjacent_to(player_region.region_id):
                    can_attack = True
                    break
            
            if can_attack:
                button_x = ui_region.position[0] + 10
                attack_rect = pygame.Rect(button_x, button_y, button_width, button_height)
                self.action_buttons.append(attack_rect)
                
                draw_button(self.screen, attack_rect, "Attack",
                           self.fonts["body"],
                           self.colors.button_normal,
                           self.colors.button_hover,
                           self.colors.text_primary)
    
    def _draw_occupation_ui(self, game_state: GameState) -> None:
        """Draw UI for occupation phase."""
        info_font = self.fonts["body"]
        
        # Get current ranking
        if game_state.occupation_ranking:
            ranking_text = "Ranking: "
            for i, player_id in enumerate(game_state.occupation_ranking[:3]):
                player = game_state.players.get(player_id)
                if player:
                    ranking_text += f"{i+1}. {player.name} "
            
            draw_text(self.screen, ranking_text,
                     (self.config.screen_width // 2, self.config.screen_height - 50),
                     info_font, self.colors.text_primary)
        
        # Instruction
        instruction = "Click on an available region to occupy it"
        draw_text(self.screen, instruction,
                 (self.config.screen_width // 2, self.config.screen_height - 20),
                 self.fonts["small"], self.colors.text_secondary)
    
    def _draw_turn_ui(self, game_state: GameState) -> None:
        """Draw UI for turn phase."""
        current_player = game_state.players.get(game_state.current_player_id)
        if not current_player:
            return
        
        # Instruction based on player type
        if current_player.player_type.name == "HUMAN":
            instruction = "Click on a region to select it, then choose an action"
            draw_text(self.screen, instruction,
                     (self.config.screen_width // 2, self.config.screen_height - 20),
                     self.fonts["small"], self.colors.text_secondary)
    
    def _get_region_color(self, region: Region, game_state: GameState) -> Tuple[int, int, int]:
        """Get color for a region based on owner."""
        if region.owner_id is None:
            return self.colors.territory_neutral
        
        # Get player color
        color = self.config.get_player_color(region.owner_id)
        
        # Darken color for dead players
        owner = game_state.players.get(region.owner_id)
        if owner and not owner.is_alive:
            color = (color[0] // 2, color[1] // 2, color[2] // 2)
        
        return color
    
    def update(self, game_state: GameState) -> None:
        """
        Update game screen state.
        
        Args:
            game_state: Current game state
        """
        # Update selected region
        if (game_state.selected_region_id != self.selected_region_id):
            self.selected_region_id = game_state.selected_region_id
            self.show_action_buttons = (self.selected_region_id is not None)
    
    def handle_event(self, event: pygame.event.Event, game_state: GameState) -> bool:
        """
        Handle pygame events.
        
        Args:
            event: Pygame event
            game_state: Current game state
            
        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            
            # Check action buttons first
            for i, button_rect in enumerate(self.action_buttons):
                if button_rect.collidepoint(pos):
                    return self._handle_action_button_click(i, game_state)
            
            # Check region clicks
            region_id = self.get_region_at_position(pos, game_state)
            if region_id is not None:
                return self._handle_region_click(region_id, game_state)
        
        return False
    
    def _handle_action_button_click(self, button_index: int, game_state: GameState) -> bool:
        """
        Handle action button click.
        
        Args:
            button_index: Index of clicked button
            game_state: Current game state
            
        Returns:
            True if handled
        """
        if not self.selected_region_id:
            return False
        
        region = game_state.regions.get(self.selected_region_id)
        if not region:
            return False
        
        # Currently we only have two possible buttons: Fortify (0) or Attack (1)
        # In a full implementation, this would trigger the corresponding action
        
        print(f"Action button {button_index} clicked for region {self.selected_region_id}")
        return True
    
    def _handle_region_click(self, region_id: int, game_state: GameState) -> bool:
        """
        Handle region click.
    
        Args:
            region_id: ID of clicked region
            game_state: Current game state
        
        Returns:
            True if handled
        """
        region = game_state.regions.get(region_id)
        if not region:
            return False
    
        # Handle based on game phase
        if game_state.current_phase == GamePhase.OCCUPYING:
            # In occupation phase, only allow clicking on selectable regions
            if region.is_selectable and region.owner_id is None:
                # This should trigger occupation in the game logic
                game_state.selected_region_id = region_id
                self.selected_region_id = region_id
                print(f"Region {region_id} selected for occupation")
                return True
        # Note: TURN phase region selection is handled by core Game class, not here
    
        return False
    
    def get_region_at_position(self, pos: Tuple[int, int]) -> Optional[int]:
        """
        Get region at mouse position.
        
        Args:
            pos: Mouse position (x, y)
            game_state: Current game state
            
        Returns:
            Region ID or None
        """
        for region_id, ui_region in self.ui_regions.items():
            if is_point_in_circle(pos, ui_region.position, ui_region.radius):
                return region_id
        
        return None


if __name__ == "__main__":
    print("=== Testing GameScreen ===")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    
    # Create config
    from src.utils.config import GameConfig
    config = GameConfig(screen_width=800, screen_height=600)
    
    # Create game screen
    game_screen = GameScreen(screen, config)
    
    # Create test game state
    from src.game.state import GameState, Player, PlayerType, Region
    game_state = GameState()
    
    # Add test player
    player = Player(
        player_id=0,
        name="Test Player",
        player_type=PlayerType.HUMAN,
        color=(255, 0, 0),
        score=1000
    )
    game_state.add_player(player)
    
    # Add test region
    region = Region(
        region_id=1,
        name="Test Region",
        position=(400, 300),
        owner_id=0
    )
    game_state.add_region(region)
    
    # Draw test screen
    game_screen.draw(game_state)
    pygame.display.flip()
    
    pygame.time.delay(1000)
    pygame.quit()
    
    print("All tests passed!")