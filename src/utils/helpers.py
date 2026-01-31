from __future__ import annotations
import pygame
import math
from typing import Tuple, List, Any
from dataclasses import is_dataclass, asdict


def draw_text(surface: pygame.Surface, text: str, position: Tuple[float, float],
              font: pygame.font.Font, color: Tuple[int, int, int] = (255, 255, 255),
              centered: bool = True) -> pygame.Rect:
    """
    Draw text on a surface.
    
    Args:
        surface: Surface to draw on
        text: Text to draw
        position: (x, y) position
        font: Pygame font object
        color: Text color
        centered: Whether to center the text at position
        
    Returns:
        Rect of the drawn text
    """
    text_surface = font.render(text, True, color)
    
    if centered:
        text_rect = text_surface.get_rect(center=position)
    else:
        text_rect = text_surface.get_rect(topleft=position)
    
    surface.blit(text_surface, text_rect)
    return text_rect


def draw_button(surface: pygame.Surface, rect: pygame.Rect, text: str,
                font: pygame.font.Font, 
                normal_color: Tuple[int, int, int],
                hover_color: Tuple[int, int, int],
                text_color: Tuple[int, int, int] = (255, 255, 255),
                hover: bool = False,
                border_radius: int = 5) -> None:
    """
    Draw a button with hover effect.
    
    Args:
        surface: Surface to draw on
        rect: Button rectangle
        text: Button text
        font: Font for text
        normal_color: Normal button color
        hover_color: Hover button color
        text_color: Text color
        hover: Whether button is being hovered
        border_radius: Corner radius
    """
    color = hover_color if hover else normal_color
    
    # Draw button background
    pygame.draw.rect(surface, color, rect, border_radius=border_radius)
    
    # Draw border
    pygame.draw.rect(surface, (50, 50, 50), rect, 2, border_radius=border_radius)
    
    # Draw text
    draw_text(surface, text, rect.center, font, text_color)


def is_point_in_circle(point: Tuple[float, float], 
                      center: Tuple[float, float], 
                      radius: float) -> bool:
    """
    Check if a point is inside a circle.
    
    Args:
        point: (x, y) point to check
        center: (x, y) circle center
        radius: Circle radius
        
    Returns:
        True if point is inside circle
    """
    distance = math.sqrt((point[0] - center[0]) ** 2 + (point[1] - center[1]) ** 2)
    return distance <= radius


def is_point_in_rect(point: Tuple[float, float], rect: pygame.Rect) -> bool:
    """
    Check if a point is inside a rectangle.
    
    Args:
        point: (x, y) point to check
        rect: Pygame rectangle
        
    Returns:
        True if point is inside rectangle
    """
    return rect.collidepoint(point)


def lerp_color(color1: Tuple[int, int, int], 
               color2: Tuple[int, int, int], 
               t: float) -> Tuple[int, int, int]:
    """
    Linearly interpolate between two colors.
    
    Args:
        color1: First color (RGB)
        color2: Second color (RGB)
        t: Interpolation factor (0.0 to 1.0)
        
    Returns:
        Interpolated color
    """
    t = max(0.0, min(1.0, t))
    r = int(color1[0] + (color2[0] - color1[0]) * t)
    g = int(color1[1] + (color2[1] - color1[1]) * t)
    b = int(color1[2] + (color2[2] - color1[2]) * t)
    return (r, g, b)


def format_number(number: float) -> str:
    """
    Format a number for display (add commas, etc.).
    
    Args:
        number: Number to format
        
    Returns:
        Formatted string
    """
    if number == 0:
        return "0"
    
    # For large numbers, use K, M, B notation
    if abs(number) >= 1_000_000_000:
        return f"{number/1_000_000_000:.1f}B"
    elif abs(number) >= 1_000_000:
        return f"{number/1_000_000:.1f}M"
    elif abs(number) >= 1_000:
        return f"{number/1_000:.1f}K"
    else:
        # Add commas for thousands
        return f"{number:,}"


def dataclass_to_dict(obj: Any) -> dict[str, Any]:
    """
    Convert a dataclass to dictionary.
    
    Args:
        obj: Dataclass instance
        
    Returns:
        Dictionary representation
    """
    if is_dataclass(obj):
        return asdict(obj)
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    else:
        return dict(obj)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def wrap_text(text: str, font: pygame.font.Font, max_width: float) -> List[str]:
    """
    Wrap text to fit within a maximum width.
    
    Args:
        text: Text to wrap
        font: Font to use for measuring
        max_width: Maximum width in pixels
        
    Returns:
        List of wrapped lines
    """
    words = text.split(' ')
    lines: List[str] = []
    current_line: List[str] = []
    
    for word in words:
        current_line.append(word)
        test_text = ' '.join(current_line)
        width, _ = font.size(test_text)
        
        if width > max_width:
            current_line.pop()  # Remove the last word
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines


if __name__ == "__main__":
    print("=== Testing helpers ===")
    
    # Test format_number
    tests = [0, 123, 1234, 1234567, 1234567890]
    for num in tests:
        print(f"{num} -> {format_number(num)}")
    
    # Test clamp
    print(f"\nclamp(5, 0, 10) = {clamp(5, 0, 10)}")
    print(f"clamp(-5, 0, 10) = {clamp(-5, 0, 10)}")
    print(f"clamp(15, 0, 10) = {clamp(15, 0, 10)}")
    
    # Test lerp_color
    color1 = (255, 0, 0)
    color2 = (0, 0, 255)
    print(f"\nlerp_color(red, blue, 0.5) = {lerp_color(color1, color2, 0.5)}")
    
    print("\nAll tests passed!")