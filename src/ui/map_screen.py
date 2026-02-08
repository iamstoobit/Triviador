from __future__ import annotations
import pygame
from typing import Dict, Tuple

from src.utils.config import GameConfig
from src.game.state import GameState, Region
from src.utils.helpers import draw_text


class MapScreen:
    """
    Full map overview screen.
    """

    def __init__(self, screen: pygame.Surface, config: GameConfig):
        """
        Initialize map screen.

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

        # Map view state
        self.zoom_level: float = 1.0
        self.pan_offset: Tuple[float, float] = (0, 0)
        self.show_legend: bool = True

    def _load_fonts(self) -> None:
        """Load fonts."""
        for size_name, size in self.config.font_sizes.items():
            self.fonts[size_name] = pygame.font.SysFont(self.config.font_name, size)

    def draw(self, game_state: GameState) -> None:
        """
        Draw the map screen.

        Args:
            game_state: Current game state
        """
        # Draw background
        self.screen.fill(self.colors.background)

        # Draw title
        self._draw_title()

        # Draw map
        self._draw_map(game_state)

        # Draw legend
        if self.show_legend:
            self._draw_legend(game_state)

        # Draw controls hint
        self._draw_controls()

    def _draw_title(self) -> None:
        """Draw screen title."""
        title_font = self.fonts["heading"]
        draw_text(self.screen, "Territory Map",
                 (self.config.screen_width // 2, 40),
                 title_font, self.colors.text_primary)

    def _draw_map(self, game_state: GameState) -> None:
        """Draw the map with all regions."""
        # Calculate map area (center of screen)
        map_width = int(self.config.screen_width * 0.7)
        map_height = int(self.config.screen_height * 0.7)
        map_x = (self.config.screen_width - map_width) // 2
        map_y = 80

        # Draw map background
        pygame.draw.rect(self.screen, (245, 245, 250),
                        (map_x, map_y, map_width, map_height),
                        border_radius=5)
        pygame.draw.rect(self.screen, self.colors.text_primary,
                        (map_x, map_y, map_width, map_height),
                        2, border_radius=5)

        # Find region bounds for scaling
        if not game_state.regions:
            return

        # Get all region positions
        positions = [region.position for region in game_state.regions.values()]
        if not positions:
            return

        # Calculate bounds
        min_x = min(pos[0] for pos in positions)
        max_x = max(pos[0] for pos in positions)
        min_y = min(pos[1] for pos in positions)
        max_y = max(pos[1] for pos in positions)

        # Add padding
        padding = 20
        range_x = max(1, max_x - min_x + 2 * padding)
        range_y = max(1, max_y - min_y + 2 * padding)

        # Calculate scale to fit in map area
        scale_x = (map_width - 40) / range_x
        scale_y = (map_height - 40) / range_y
        scale = min(scale_x, scale_y) * self.zoom_level

        # Calculate offset to center map
        offset_x = map_x + 20 - (min_x - padding) * scale + self.pan_offset[0]
        offset_y = map_y + 20 - (min_y - padding) * scale + self.pan_offset[1]

        # Draw connections first (so regions appear on top)
        self._draw_map_connections(game_state, offset_x, offset_y, scale)

        # Draw regions
        self._draw_map_regions(game_state, offset_x, offset_y, scale)

    def _draw_map_connections(self, game_state: GameState,
                             offset_x: float, offset_y: float, scale: float) -> None:
        """Draw connections between regions on map."""
        # Track which connections we've already drawn to avoid duplicates
        drawn_connections: set[tuple[int, ...]] = set()

        for region_id, region in game_state.regions.items():
            # Calculate screen position
            screen_x1 = offset_x + region.position[0] * scale
            screen_y1 = offset_y + region.position[1] * scale

            for adj_id in region.adjacent_regions:
                if adj_id in game_state.regions:
                    # Create a unique identifier for this connection
                    connection_key = tuple(sorted((region_id, adj_id)))

                    # Only draw if we haven't drawn this connection yet
                    if connection_key not in drawn_connections:
                        drawn_connections.add(connection_key)

                        adj_region = game_state.regions[adj_id]

                        # Calculate adjacent region screen position
                        screen_x2 = offset_x + adj_region.position[0] * scale
                        screen_y2 = offset_y + adj_region.position[1] * scale

                        # Determine connection color
                        if (region.owner_id == adj_region.owner_id and
                            region.owner_id is not None):
                            # Same owner
                            owner_color = self.config.get_player_color(region.owner_id)
                            color = (owner_color[0], owner_color[1], owner_color[2], 150)
                        else:
                            # Different owners or neutral
                            color = self.colors.territory_border

                        # Draw connection line
                        pygame.draw.line(self.screen, color,
                                    (int(screen_x1), int(screen_y1)),
                                    (int(screen_x2), int(screen_y2)), 2)

    def _draw_map_regions(self, game_state: GameState,
                         offset_x: float, offset_y: float, scale: float) -> None:
        """Draw regions on map."""
        region_radius = max(8, int(12 * min(self.zoom_level, 1.5)))

        for region_id, region in game_state.regions.items():
            # Calculate screen position
            screen_x = offset_x + region.position[0] * scale
            screen_y = offset_y + region.position[1] * scale

            # Determine region color
            if region.owner_id is None:
                color = self.colors.territory_neutral
            else:
                color = self.config.get_player_color(region.owner_id)

            # Draw region
            pygame.draw.circle(self.screen, color,
                             (int(screen_x), int(screen_y)),
                             region_radius)

            # Draw border
            border_color = self.colors.region_border
            if region.region_type.name == "CAPITAL":
                border_color = self.colors.capital_highlight
                pygame.draw.circle(self.screen, border_color,
                                 (int(screen_x), int(screen_y)),
                                 region_radius + 2, 2)
            else:
                pygame.draw.circle(self.screen, border_color,
                                 (int(screen_x), int(screen_y)),
                                 region_radius, 2)

            # Draw region ID (small number)
            if self.zoom_level > 0.8:
                id_font = self.fonts["tiny"]
                draw_text(self.screen, str(region_id),
                         (int(screen_x), int(screen_y)),
                         id_font, (255, 255, 255))

    def _draw_legend(self, game_state: GameState) -> None:
        """Draw map legend."""
        legend_width = 250
        legend_x = self.config.screen_width - legend_width - 20
        legend_y = 80
        legend_height = 300

        # Draw legend background
        pygame.draw.rect(self.screen, self.colors.panel,
                        (legend_x, legend_y, legend_width, legend_height),
                        border_radius=5)
        pygame.draw.rect(self.screen, self.colors.text_primary,
                        (legend_x, legend_y, legend_width, legend_height),
                        2, border_radius=5)

        # Draw legend title
        legend_font = self.fonts["subheading"]
        draw_text(self.screen, "Legend",
                 (legend_x + legend_width // 2, legend_y + 20),
                 legend_font, self.colors.text_primary)

        # Draw players
        y_pos = legend_y + 60
        item_font = self.fonts["small"]

        for player_id, player in game_state.players.items():
            if not player.is_alive:
                continue

            # Player color indicator
            color = self.config.get_player_color(player_id)
            pygame.draw.circle(self.screen, color, (legend_x + 30, y_pos), 8)

            # Player name
            name = player.name
            if player.player_type.name == "HUMAN":
                name += " (You)"

            draw_text(self.screen, name,
                     (legend_x + 60, y_pos),
                     item_font, self.colors.text_primary, centered=False)

            # Region count
            regions_text = f"({len(player.regions_controlled)} regions)"
            draw_text(self.screen, regions_text,
                     (legend_x + legend_width - 20, y_pos),
                     item_font, self.colors.text_secondary, centered=False)

            y_pos += 35

        # Draw symbols
        y_pos += 20

        # Capital symbol
        pygame.draw.circle(self.screen, self.colors.capital_highlight,
                         (legend_x + 30, y_pos), 10, 2)
        draw_text(self.screen, "= Capital",
                 (legend_x + 60, y_pos),
                 item_font, self.colors.text_primary, centered=False)

        y_pos += 25

        # Neutral symbol
        pygame.draw.circle(self.screen, self.colors.territory_neutral,
                         (legend_x + 30, y_pos), 8)
        draw_text(self.screen, "= Neutral Territory",
                 (legend_x + 60, y_pos),
                 item_font, self.colors.text_primary, centered=False)

    def _draw_controls(self) -> None:
        """Draw map controls hint."""
        controls_font = self.fonts["small"]
        controls_text = "ESC: Back to Game | Mouse Wheel: Zoom | Drag: Pan"

        draw_text(self.screen, controls_text,
                 (self.config.screen_width // 2, self.config.screen_height - 20),
                 controls_font, self.colors.text_secondary)

    def update(self, game_state: GameState) -> None:
        """
        Update map screen state.

        Args:
            game_state: Current game state
        """
        # Reset zoom and pan when screen changes
        self.zoom_level = 1.0
        self.pan_offset = (0, 0)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame events.

        Args:
            event: Pygame event
            game_state: Current game state

        Returns:
            True if event was handled
        """
        if event.type == pygame.MOUSEWHEEL:
            # Zoom in/out
            zoom_factor = 1.1
            if event.y > 0:  # Scroll up
                self.zoom_level *= zoom_factor
            else:  # Scroll down
                self.zoom_level /= zoom_factor

            # Clamp zoom level
            self.zoom_level = max(0.5, min(3.0, self.zoom_level))
            return True

        elif event.type == pygame.MOUSEMOTION:
            # Pan with middle mouse button
            if event.buttons[1]:  # Middle mouse button
                self.pan_offset = (self.pan_offset[0] + event.rel[0],
                                  self.pan_offset[1] + event.rel[1])
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Exit map screen
                return True

        return False


if __name__ == "__main__":
    print("=== Testing MapScreen ===")

    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))

    # Create config
    from src.utils.config import GameConfig
    config = GameConfig(screen_width=800, screen_height=600)

    # Create map screen
    map_screen = MapScreen(screen, config)

    # Create test game state with regions
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

    # Add test regions
    for i in range(10):
        region = Region(
            region_id=i + 1,
            name=f"Region {i + 1}",
            position=(100 + i * 50, 100 + (i % 3) * 50),
            owner_id=0 if i < 5 else None
        )
        game_state.add_region(region)

    # Draw test screen
    map_screen.draw(game_state)
    pygame.display.flip()

    pygame.time.delay(1000)
    pygame.quit()

    print("All tests passed!")