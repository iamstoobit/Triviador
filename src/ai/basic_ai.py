from typing import List
import random

from src.game.state import Region


class BasicAI:
    """Basic AI that makes random decisions (for testing)."""
    
    def choose_occupation_region(self, available_regions: List[Region]) -> Region:
        """Choose a random region."""
        return random.choice(available_regions)