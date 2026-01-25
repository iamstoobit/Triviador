import sys
import pygame
import traceback
from typing import NoReturn

# Import game modules
try:
    from src.game.core import Game
    from src.utils.config import GameConfig
    from src.game.state import GameState
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure all required modules are present.")
    sys.exit(1)


def main() -> NoReturn:
    """
    Main function that initializes and runs the game.
    
    This function:
    1. Initializes Pygame and its modules
    2. Creates game configuration
    3. Initializes the main Game instance
    4. Runs the game loop
    5. Handles cleanup on exit
    """
    # Initialize Pygame
    if not initialize_pygame():
        print("Failed to initialize Pygame. Exiting.")
        sys.exit(1)
    
    try:
        # Create game configuration
        config: GameConfig = GameConfig.load()
        print(f"Configuration loaded: {config.ai_count} AI, {config.difficulty.value} difficulty")

        # Initialize the main game
        game: Game = Game(config)
        
        # Run the main game loop
        game.run()
        
    except Exception as e:
        print(f"Fatal error occurred: {e}")
        traceback.print_exc()
    
    # Ensure clean exit
    finally:
        cleanup_pygame()
        sys.exit(0)


def initialize_pygame() -> bool:
    """
    Initialize Pygame and its required modules.
    
    Returns:
        bool: True if initialization was successful, False otherwise
    """
    try:
        # Initialize Pygame core
        pygame.init()
        
        # Initialize specific Pygame modules
        if not pygame.font.get_init():
            pygame.font.init()
            
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            
        return True
        
    except pygame.error as e:
        print(f"Pygame initialization error: {e}")
        return False


def cleanup_pygame() -> None:
    """Safely clean up Pygame resources."""
    try:
        pygame.mixer.quit()
        pygame.font.quit()
        pygame.quit()
    except Exception:
        pass  # Silently ignore cleanup errors


if __name__ == "__main__":
    main()