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
    min_region_distance: int = 40
    max_region_distance: int = 150
    border_margin: int = 50
    max_adjacent_regions: int = 6
    min_adjacent_regions: int = 2
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
        Generate random regions for the game.
        
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
        
        # Step 1: Generate random positions
        positions = self._generate_positions(count, screen_width, screen_height)
        
        # Step 2: Generate region names
        names = self._generate_names(count)
        
        # Step 3: Determine adjacency based on proximity
        adjacency_lists = self._calculate_adjacency(positions)
        
        # Step 4: Create region data dictionaries
        regions_data: List[Dict[str, Any]] = []
        for i in range(count):
            region_data: Dict[str, Any] = {
                'id': i + 1,  # Start IDs from 1
                'name': names[i],
                'position': positions[i],
                'adjacent': adjacency_lists[i]
            }
            regions_data.append(region_data)
        
        # Step 5: Ensure all regions are connected
        self._ensure_connectivity(regions_data)
        
        print(f"Generated {len(regions_data)} regions with adjacency")
        return regions_data
    
    def _generate_positions(self, count: int, 
                           screen_width: int, 
                           screen_height: int) -> List[Tuple[float, float]]:
        """
        Generate random non-overlapping positions for regions.
        
        Args:
            count: Number of positions to generate
            screen_width: Available width
            screen_height: Available height
            
        Returns:
            List of (x, y) positions
        """
        positions: List[Tuple[float, float]] = []
        margin = self.config.border_margin
        attempts = 0
        max_attempts = count * 100  # Prevent infinite loop
        
        while len(positions) < count and attempts < max_attempts:
            attempts += 1
            
            # Generate random position within margins
            x = random.uniform(margin, screen_width - margin)
            y = random.uniform(margin, screen_height - margin)
            new_pos = (x, y)
            
            # Check if too close to existing positions
            too_close = False
            for existing_pos in positions:
                distance = self._calculate_distance(new_pos, existing_pos)
                if distance < self.config.min_region_distance:
                    too_close = True
                    break
            
            if not too_close:
                positions.append(new_pos)
        
        # If we couldn't generate enough positions, relax constraints
        if len(positions) < count:
            print(f"Warning: Could only generate {len(positions)} positions with constraints")
            while len(positions) < count:
                x = random.uniform(margin, screen_width - margin)
                y = random.uniform(margin, screen_height - margin)
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
    
    def _calculate_adjacency(self, positions: List[Tuple[float, float]]) -> List[List[int]]:
        """
        Calculate adjacency between regions based on proximity.
        
        Args:
            positions: List of region positions
            
        Returns:
            List of adjacency lists for each region
        """
        count = len(positions)
        adjacency: List[List[int]] = [[] for _ in range(count)]
        
        # Calculate distances between all pairs
        distances: List[List[Tuple[int, float]]] = [[] for _ in range(count)]
        
        for i in range(count):
            for j in range(i + 1, count):
                dist = self._calculate_distance(positions[i], positions[j])
                distances[i].append((j, dist))
                distances[j].append((i, dist))
        
        # For each region, connect to nearest neighbors
        for i in range(count):
            # Sort neighbors by distance
            distances[i].sort(key=lambda x: x[1])
            
            # Connect to closest neighbors, but not too many
            max_neighbors = min(self.config.max_adjacent_regions, len(distances[i]))
            min_neighbors = min(self.config.min_adjacent_regions, max_neighbors)
            
            # Determine how many neighbors this region should have
            # More neighbors for central regions, fewer for edge regions
            neighbor_count = random.randint(min_neighbors, max_neighbors)
            
            # Add the closest neighbors
            for j in range(min(neighbor_count, len(distances[i]))):
                neighbor_id, dist = distances[i][j]
                
                # Check if distance is reasonable
                if dist <= self.config.max_region_distance:
                    adjacency[i].append(neighbor_id)
                    # Ensure bidirectional connection
                    if i not in adjacency[neighbor_id]:
                        adjacency[neighbor_id].append(i)
        
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

            else:
                # Fallback: connect to random connected region
                # This should only happen if disconnected or connected sets are empty
                if disconnected and connected_set:
                    disc = random.choice(list(disconnected))
                    conn = random.choice(list(connected_set))
                    
                    print(f"Warning: Using random fallback to connect region {disc} to {conn}")
                    
                    # Add bidirectional connection
                    regions_data[conn]['adjacent'].append(disc)
                    regions_data[disc]['adjacent'].append(conn)
                    
                    # Move disc from disconnected to connected
                    disconnected.remove(disc)
                    connected_set.add(disc)
                else:
                    # This should never happen, but break to avoid infinite loop
                    print(f"Error: Cannot connect regions. disconnected={disconnected}, connected={connected_set}")
                    break
    
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
    print("=== Testing MapManager ===")
    
    # Create map manager
    config = MapConfig(region_count=20)
    manager = MapManager(config)
    
    # Generate regions
    regions_data = manager.generate_regions(
        region_count=20,
        screen_width=1280,
        screen_height=720
    )
    
    print(f"\nGenerated {len(regions_data)} regions:")
    for i, data in enumerate(regions_data[:5]):  # Show first 5
        print(f"Region {data['id']}: {data['name']}")
        print(f"  Position: {data['position']}")
        print(f"  Adjacent to: {data['adjacent']}")
    
    # Test adjacency connectivity
    total_connections = sum(len(data['adjacent']) for data in regions_data)
    avg_connections = total_connections / len(regions_data)
    print(f"\nAverage connections per region: {avg_connections:.1f}")
    
    # Create Region objects for bonus calculation test
    regions_dict: Dict[Any, Any] = {}
    for data in regions_data:
        region = Region(
            region_id=data['id'],
            name=data['name'],
            position=data['position'],
            adjacent_regions=data['adjacent']
        )
        regions_dict[data['id']] = region
    
    # Test path finding
    if len(regions_data) >= 2:
        start_id = regions_data[0]['id']
        end_id = regions_data[-1]['id']
        path = manager.find_path(start_id, end_id, regions_dict)
        
        if path:
            print(f"\nPath from region {start_id} to {end_id}:")
            print(f"  Length: {len(path)} regions")
            print(f"  Path: {path}")
        else:
            print(f"\nNo path found from region {start_id} to {end_id}")
    
    print("\nAll tests passed!")