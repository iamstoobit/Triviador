from __future__ import annotations
import random
import math
from typing import List, Dict, Tuple, Set, Optional, Any
from dataclasses import dataclass, field

from src.game.state import Region


@dataclass
class MapConfig:
    """Configuration for map generation."""
    
    region_count: int = 24
    border_margin: int = 50
    region_names: List[str] = field(default_factory=lambda: [
        "Arctic", "Tundra", "Taiga", "Forest", "Plains", "Desert", 
        "Savanna", "Jungle", "Mountains", "Hills", "Swamp", "Coast",
        "Island", "Peninsula", "Archipelago", "Valley", "Canyon", 
        "Plateau", "Mesa", "Oasis", "Volcano", "Glacier", "Fjord",
        "Delta", "Basin", "Cliff", "Cave", "Reef", "Lagoon", "Bay",
        "Strait", "Isthmus", "Atoll", "Geyser", "Crater", "Summit"
    ])


class MapManager:
    """
    Manages map generation and region relationships.
    Generates random territories with positions and adjacency.
    """
    
    def __init__(self, config: Optional[MapConfig] = None):
        """
        Initialize map manager.
        
        Args:
            config: Map configuration, uses default if None
        """
        self.config = config or MapConfig()
        self.regions: Dict[int, Region] = {}
        
    def generate_regions(self, region_count: Optional[int] = None,
                        screen_width: int = 1280,
                        screen_height: int = 720) -> List[Dict[str, Any]]:
        """
        Generate grid-based regions for the game.
        
        Args:
            region_count: Number of regions to generate (uses config if None)
            screen_width: Width of the game screen
            screen_height: Height of the game screen
            
        Returns:
            List of region data dictionaries for creating Region objects
        """
        count = region_count or self.config.region_count
        count = max(16, min(32, count))  # Clamp between 16-32 as per rules
        
        print(f"Generating {count} regions...")
        
        # Step 1: Generate grid dimensions
        grid_width, grid_height = self._calculate_grid_dimensions(count, screen_width, screen_height)
        
        # Step 2: Generate positions on grid
        positions = self._generate_grid_positions(count, grid_width, grid_height, screen_width, screen_height)

        # Step 3: Generate region names
        names = self._generate_names(count)
        
        # Step 4: Determine adjacency based on grid neighbours
        adjacency_lists = self._calculate_grid_adjacency(count, grid_width, grid_height)

        # Step 5: Create region data dictionaries
        regions_data: List[Dict[str, Any]] = []
        for i in range(count):
            region_data: Dict[str, Any] = {
                'id': i + 1,  # Start IDs from 1
                'name': names[i],
                'position': positions[i],
                'adjacent': adjacency_lists[i]
            }
            regions_data.append(region_data)
        
        # Step 6: Ensure all regions are connected
        self._ensure_connectivity(regions_data)

        for region_data in regions_data:
            region_data['adjacent'] = [adj_idx + 1 for adj_idx in region_data['adjacent']]
        
        print(f"Generated {len(regions_data)} regions in {grid_width}x{grid_height} grid")
        return regions_data
    
    def _calculate_grid_dimensions(self, count: int, 
                                screen_width: int = 1280,
                                screen_height: int = 720) -> Tuple[int, int]:
        """
        Calculate optimal grid dimensions for given region count.
        Prioritizes grids with no empty cells that match screen aspect ratio.
        
        Args:
            count: Number of regions
            screen_width: Screen width (for aspect ratio)
            screen_height: Screen height (for aspect ratio)
            
        Returns:
            (grid_width, grid_height) - dimensions in number of cells
        """
        target_aspect = screen_width / screen_height
        best_score = float('inf')
        best_dimensions = (1, count)
        
        # Try all possible grid dimensions
        for width in range(1, count + 1):
            height = (count + width - 1) // width  # Ceiling division
            
            # Calculate how well this grid fits
            aspect_ratio = width / height
            aspect_diff = abs(aspect_ratio - target_aspect)
            
            # Penalize empty cells: (width * height - count)
            empty_cells = width * height - count
            
            # Combined score (lower is better)
            # Weight aspect ratio difference more heavily
            score = aspect_diff * 10 + empty_cells
            
            if score < best_score:
                best_score = score
                best_dimensions = (width, height)
        
        return best_dimensions

    def _generate_grid_positions(self, count: int, grid_width: int, 
                                grid_height: int, screen_width: int, 
                                screen_height: int) -> List[Tuple[float, float]]:
        """
        Generate positions for regions in a grid layout.
        
        Args:
            count: Number of regions
            grid_width: Grid width in cells
            grid_height: Grid height in cells
            screen_width: Available width
            screen_height: Available height
            
        Returns:
            List of (x, y) positions
        """
        positions: List[Tuple[float, float]] = []
        margin = self.config.border_margin
        
        # Calculate cell size
        available_width = screen_width - 2 * margin
        available_height = screen_height - 2 * margin
        
        cell_width = (available_width / grid_width) * 0.85
        cell_height = (available_height / grid_height) * 0.85
        
        # Calculate region radius (for non-overlapping)
        region_radius = min(cell_width, cell_height) * 0.25
        
        # Shuffle indices to distribute regions randomly in grid
        grid_cells = [(x, y) for x in range(grid_width) for y in range(grid_height)]
        
        # Assign first 'count' cells to regions
        for i in range(count):
            grid_x, grid_y = grid_cells[i]
            
            # Center the region in its grid cell with small random offset
            center_x = margin + (grid_x + 0.5) * cell_width
            center_y = margin + (grid_y + 0.5) * cell_height
            
            # Add small random offset for natural look (but keep within cell)
            offset_x = random.uniform(-cell_width * 0.05, cell_width * 0.05)
            offset_y = random.uniform(-cell_height * 0.05, cell_height * 0.05)
            
            x = center_x + offset_x
            y = center_y + offset_y
            
            # Ensure position stays within cell bounds
            x = max(margin + region_radius, min(screen_width - margin - region_radius, x))
            y = max(margin + region_radius, min(screen_height - margin - region_radius, y))
            
            positions.append((x, y))
        
        return positions

    def _generate_names(self, count: int) -> List[str]:
        """
        Generate unique names for regions.
        
        Args:
            count: Number of names needed
            
        Returns:
            List of region names
        """
        available_names = self.config.region_names.copy()
        random.shuffle(available_names)
        
        # If we need more names than available, add numbers
        names: List[str] = []
        for i in range(count):
            if i < len(available_names):
                names.append(available_names[i])
            else:
                # Create compound names
                base_name = random.choice(available_names)
                suffix = random.choice(["North", "South", "East", "West", 
                                       "Upper", "Lower", "New", "Old", 
                                       "Greater", "Lesser", "Central"])
                names.append(f"{base_name} {suffix}")
        
        # Ensure uniqueness
        unique_names: List[str] = []
        name_count: Dict[str, int] = {}
        
        for name in names:
            if name in name_count:
                name_count[name] += 1
                unique_names.append(f"{name} {name_count[name]}")
            else:
                name_count[name] = 1
                unique_names.append(name)
        
        return unique_names

    def _calculate_grid_adjacency(self, count: int, 
                                 grid_width: int, 
                                 grid_height: int) -> List[List[int]]:
        """
        Calculate adjacency based on grid positions.
        Regions are adjacent if they are in neighboring grid cells.
        
        Args:
            count: Number of regions
            grid_width: Grid width in cells
            grid_height: Grid height in cells
            
        Returns:
            List of adjacency lists for each region
        """
        # Map from grid position to region index
        grid_to_region: Dict[Tuple[int, int], int] = {}
        region_to_grid: Dict[int, Tuple[int, int]] = {}
        
        # First, create a list of all grid cells
        grid_cells = [(x, y) for x in range(grid_width) for y in range(grid_height)]
        
        # Assign first 'count' cells to regions
        for i in range(count):
            grid_x, grid_y = grid_cells[i]
            grid_to_region[(grid_x, grid_y)] = i
            region_to_grid[i] = (grid_x, grid_y)
        
        # Initialize adjacency lists
        adjacency: List[List[int]] = [[] for _ in range(count)]
        
        # For each region, check its grid neighbors
        for region_id in range(count):
            grid_x, grid_y = region_to_grid[region_id]
            
            # Check all 4 cardinal directions
            orthogonal_neighbors = [
                (grid_x - 1, grid_y),  # Left
                (grid_x + 1, grid_y),  # Right
                (grid_x, grid_y - 1),  # Up
                (grid_x, grid_y + 1),  # Down
            ]
            
            for neighbor_x, neighbor_y in orthogonal_neighbors:
                if (neighbor_x, neighbor_y) in grid_to_region:
                    neighbor_id = grid_to_region[(neighbor_x, neighbor_y)]
                    # Add bidirectional connection
                    if neighbor_id not in adjacency[region_id]:
                        adjacency[region_id].append(neighbor_id)
                    if region_id not in adjacency[neighbor_id]:
                        adjacency[neighbor_id].append(region_id)
        
        # Add some random diagonal connections for more interesting maps
        for region_id in range(count):
            grid_x, grid_y = region_to_grid[region_id]
            
            # Check diagonal neighbors
            diagonals = [
                (grid_x - 1, grid_y - 1),  # Top-left
                (grid_x + 1, grid_y - 1),  # Top-right
                (grid_x - 1, grid_y + 1),  # Bottom-left
                (grid_x + 1, grid_y + 1),  # Bottom-right
            ]
            
            for diag_x, diag_y in diagonals:
                if random.random() < 0.3:  # 30% chance for diagonal connection
                    if (diag_x, diag_y) in grid_to_region:
                        neighbor_id = grid_to_region[(diag_x, diag_y)]
                        if neighbor_id not in adjacency[region_id]:
                            adjacency[region_id].append(neighbor_id)
                        if region_id not in adjacency[neighbor_id]:
                            adjacency[neighbor_id].append(region_id)
        
        return adjacency

    def _ensure_connectivity(self, regions_data: List[Dict[str, Any]]) -> None:
        """
        Ensure all regions are connected (no isolated islands).
        
        Args:
            regions_data: List of region data dictionaries
        """
        if not regions_data:
            return
        
        # Use BFS to find all connected regions
        visited: Set[int] = set()
        queue: List[int] = [0]  # Start with region 0
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            
            visited.add(current)
            
            # Add all adjacent regions to queue
            for neighbor in regions_data[current]['adjacent']:
                if neighbor not in visited:
                    queue.append(neighbor)
        
        # If not all regions are connected, add connections
        if len(visited) < len(regions_data):
            print(f"Warning: Map not fully connected. Connecting {len(visited)}/{len(regions_data)} regions.")
            self._connect_isolated_regions(regions_data, visited)

    def _connect_isolated_regions(self, regions_data: List[Dict[str, Any]], 
                                 connected_set: Set[int]) -> None:
        """
        Connect isolated regions to the main graph.
        
        Args:
            regions_data: List of region data dictionaries
            connected_set: Set of already connected region indices
        """
        all_regions = set(range(len(regions_data)))
        disconnected = all_regions - connected_set
        
        while disconnected:
            # Find closest pair between connected and disconnected
            best_pair = None
            best_distance = float('inf')
            
            for conn in connected_set:
                conn_pos = regions_data[conn]['position']
                for disc in disconnected:
                    disc_pos = regions_data[disc]['position']
                    distance = self._calculate_distance(conn_pos, disc_pos)
                    
                    if distance < best_distance:
                        best_distance = distance
                        best_pair = (conn, disc)
            
            if best_pair:
                conn, disc = best_pair
                # Add bidirectional connection
                regions_data[conn]['adjacent'].append(disc)
                regions_data[disc]['adjacent'].append(conn)
                
                # Move disc from disconnected to connected
                disconnected.remove(disc)
                connected_set.add(disc)

    def _calculate_distance(self, pos1: Tuple[float, float], 
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
    
    def find_path(self, start_region_id: int, end_region_id: int,
                 regions: Dict[int, Region]) -> Optional[List[int]]:
        """
        Find shortest path between two regions.
        
        Args:
            start_region_id: Starting region ID
            end_region_id: Destination region ID
            regions: Dictionary of region_id -> Region
            
        Returns:
            List of region IDs forming the path, or None if no path exists
        """
        if (start_region_id not in regions or 
            end_region_id not in regions):
            return None
        
        # BFS for shortest path
        visited: Set[int] = set()
        queue: List[Tuple[int, List[int]]] = [(start_region_id, [start_region_id])]
        
        while queue:
            current_id, path = queue.pop(0)
            
            if current_id == end_region_id:
                return path
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            current_region = regions[current_id]
            
            for neighbor_id in current_region.adjacent_regions:
                if neighbor_id not in visited and neighbor_id in regions:
                    new_path = path + [neighbor_id]
                    queue.append((neighbor_id, new_path))
        
        return None

    def get_region_at_position(self, position: Tuple[float, float],
                              regions: Dict[int, Region],
                              radius: float = 30.0) -> Optional[int]:
        """
        Find region at given screen position.
        
        Args:
            position: (x, y) screen position
            regions: Dictionary of region_id -> Region
            radius: Click radius
            
        Returns:
            Region ID at position, or None if no region found
        """
        for region_id, region in regions.items():
            distance = self._calculate_distance(position, region.position)
            if distance < radius:
                return region_id
        return None

if __name__ == "__main__":
    print("=== Testing MapManager Grid Layout ===")
    
    # Create map manager
    config = MapConfig(region_count=24)
    manager = MapManager(config)
    
    # Generate regions
    regions_data = manager.generate_regions(
        region_count=24,
        screen_width=1280,
        screen_height=720
    )
    
    print(f"\nGenerated {len(regions_data)} regions:")
    
    # Check for overlaps
    positions = [data['position'] for data in regions_data]
    min_distance = float('inf')
    
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            dist = manager._calculate_distance(positions[i], positions[j])
            min_distance = min(min_distance, dist)
    
    print(f"Minimum distance between regions: {min_distance:.1f} pixels")
    
    # Check if all regions are on screen
    all_on_screen = True
    for i, pos in enumerate(positions):
        if pos[0] < 0 or pos[0] > 1280 or pos[1] < 0 or pos[1] > 720:
            print(f"Region {i+1} at position {pos} is off-screen!")
            all_on_screen = False
    
    if all_on_screen:
        print("All regions are on screen ✓")
    
    # Show adjacency statistics
    total_connections = sum(len(data['adjacent']) for data in regions_data)
    avg_connections = total_connections / len(regions_data)
    print(f"Average connections per region: {avg_connections:.1f}")
    
    print("\nGrid layout test complete!")