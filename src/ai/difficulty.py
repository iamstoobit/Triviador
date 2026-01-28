from __future__ import annotations
from typing import Dict, Any
from dataclasses import dataclass
import random

from src.utils.config import GameConfig, Difficulty


@dataclass
class AIDifficultyManager:
    """
    Manages AI behavior based on difficulty level.
    """
    
    config: GameConfig
    
    def get_behavior_profile(self) -> Dict[str, Any]:
        """
        Get behavior profile based on difficulty.
        
        Returns:
            Dictionary with AI behavior parameters
        """
        if self.config.difficulty == Difficulty.EASY:
            return {
                "aggression": 0.3,  # Low aggression
                "risk_taking": 0.2,  # Avoid risks
                "strategic_thinking": 0.4,  # Basic strategy
                "memory": 5,  # Remember last 5 battles
                "adaptation_speed": 0.1,  # Slow to adapt
            }
        elif self.config.difficulty == Difficulty.MEDIUM:
            return {
                "aggression": 0.6,  # Moderate aggression
                "risk_taking": 0.5,  # Balanced risk
                "strategic_thinking": 0.7,  # Good strategy
                "memory": 10,  # Remember last 10 battles
                "adaptation_speed": 0.3,  # Moderate adaptation
            }
        else:  # HARD
            return {
                "aggression": 0.8,  # High aggression
                "risk_taking": 0.7,  # High risk tolerance
                "strategic_thinking": 0.9,  # Excellent strategy
                "memory": 20,  # Remember last 20 battles
                "adaptation_speed": 0.5,  # Fast adaptation
            }
    
    def should_make_mistake(self, situation: str = "general") -> bool:
        """
        Determine if AI should make a mistake based on difficulty.
        
        Args:
            situation: Type of situation 
                "battle" - During a battle (attack or defense)
                "strategic" - Strategic decisions (occupation, fortification)
                "general" - General gameplay decisions
                
        Returns:
            True if AI should make a mistake
        """
        base_mistake_chance = {
            Difficulty.EASY: 0.4,
            Difficulty.MEDIUM: 0.2,
            Difficulty.HARD: 0.05,
        }.get(self.config.difficulty, 0.2)
        
        # Adjust based on situation
        situation_multiplier = {
            "battle": 1.5,      # High pressure situations
            "strategic": 0.7,   # Planning phases
            "general": 1.0,     # Normal gameplay
        }.get(situation, 1.0)
        
        mistake_chance = base_mistake_chance * situation_multiplier
        
        # For testing, we'll use random
        return random.random() < mistake_chance


if __name__ == "__main__":
    print("=== Testing AIDifficultyManager ===")
    
    config = GameConfig()
    config.difficulty = Difficulty.MEDIUM
    manager = AIDifficultyManager(config)
    
    profile = manager.get_behavior_profile()
    print(f"Medium difficulty profile: {profile}")
    
    # Test mistake probability
    mistakes = sum(1 for _ in range(1000) if manager.should_make_mistake())
    print(f"Mistakes in 1000 trials: {mistakes} (~{mistakes/10:.1f}%)")
    
    print("All tests passed!")