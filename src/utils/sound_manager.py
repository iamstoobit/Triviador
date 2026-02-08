from __future__ import annotations
import pygame
import os
import numpy as np
from typing import Dict, Optional
from pathlib import Path


class SoundManager:
    """
    Manages loading and playing sound effects and music.
    """

    def __init__(self):
        """Initialize sound manager."""
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.music_volume: float = 0.5
        self.sfx_volume: float = 0.7
        self.is_muted: bool = False

    def load_sounds(self, assets_dir: str) -> bool:
        """
        Load all sound effects from assets directory.

        Args:
            assets_dir: Path to assets directory

        Returns:
            True if sounds loaded successfully, False otherwise
        """
        try:
            sounds_dir = os.path.join(assets_dir, "sounds", "sfx")
            music_dir = os.path.join(assets_dir, "sounds", "music")

            # Create directories if they don't exist
            Path(sounds_dir).mkdir(parents=True, exist_ok=True)
            Path(music_dir).mkdir(parents=True, exist_ok=True)

            # List of required sound files
            sound_files = {
                "click": "click.wav",
                "hover": "hover.wav",
                "correct": "correct.wav",
                "wrong": "wrong.wav",
                "occupy": "occupy.wav",
                "capture": "capture.wav",
                "fortify": "fortify.wav",
                "battle_start": "battle_start.wav",
                "battle_win": "battle_win.wav",
                "battle_lose": "battle_lose.wav",
                "capital_hit": "capital_hit.wav",
                "capital_capture": "capital_capture.wav",
                "game_start": "game_start.wav",
                "game_over": "game_over.wav",
                "turn_start": "turn_start.wav",
            }

            # Try to load each sound
            for sound_name, filename in sound_files.items():
                filepath = os.path.join(sounds_dir, filename)

                if os.path.exists(filepath):
                    try:
                        sound = pygame.mixer.Sound(filepath)
                        self.sounds[sound_name] = sound
                        print(f"Loaded sound: {sound_name}")
                    except pygame.error as e:
                        print(f"Failed to load sound {filename}: {e}")
                        self._create_placeholder_sound(sound_name)
                else:
                    print(f"Sound file not found: {filepath}")
                    self._create_placeholder_sound(sound_name)

            # Set volumes
            self.set_sfx_volume(self.sfx_volume)

            print(f"Loaded {len(self.sounds)} sound effects")
            return True

        except Exception as e:
            print(f"Error loading sounds: {e}")
            return False

    def _create_placeholder_sound(self, sound_name: str) -> None:
        """
        Create a placeholder sound effect.

        Args:
            sound_name: Name of the sound
        """
        # Create a simple beep sound
        try:
            # Different frequencies for different sounds
            frequencies = {
                "click": 440,      # A4
                "hover": 523,      # C5
                "correct": 659,    # E5
                "wrong": 392,      # G4
                "occupy": 587,     # D5
                "capture": 784,    # G5
                "fortify": 698,    # F5
                "battle_start": 330,  # E4
                "battle_win": 880,    # A5
                "battle_lose": 294,   # D4
                "capital_hit": 247,   # B3
                "capital_capture": 988,  # B5
                "game_start": 659,   # E5
                "game_over": 220,    # A3
                "turn_start": 494,   # B4
            }

            freq = frequencies.get(sound_name, 440)
            duration = 100  # milliseconds
            sample_rate = 44100

            t = np.linspace(0, duration / 1000, int(sample_rate * duration / 1000), False)
            wave = np.sin(2 * np.pi * freq * t)

            # Convert to 16-bit integers
            audio = (wave * 32767).astype(np.int16)

            # Create stereo sound
            stereo_audio = np.column_stack((audio, audio))

            # Create pygame sound
            sound = pygame.sndarray.make_sound(stereo_audio)
            self.sounds[sound_name] = sound

        except ImportError:
            # If numpy not available, create silent sound
            silent_sound = pygame.mixer.Sound(buffer=bytes([0] * 100))
            self.sounds[sound_name] = silent_sound
            print(f"Created silent placeholder for {sound_name}")
        except Exception as e:
            print(f"Failed to create placeholder for {sound_name}: {e}")
            silent_sound = pygame.mixer.Sound(buffer=bytes([0] * 100))
            self.sounds[sound_name] = silent_sound

    def play_sound(self, sound_name: str, volume: Optional[float] = None) -> bool:
        """
        Play a sound effect.

        Args:
            sound_name: Name of the sound to play
            volume: Volume (0.0 to 1.0), uses current SFX volume if None

        Returns:
            True if sound was played, False otherwise
        """
        if self.is_muted:
            return False

        if sound_name not in self.sounds:
            print(f"Sound not found: {sound_name}")
            return False

        try:
            sound = self.sounds[sound_name]

            # Set volume if specified
            if volume is not None:
                sound.set_volume(max(0.0, min(1.0, volume)))
            else:
                sound.set_volume(self.sfx_volume)

            sound.play()
            return True

        except Exception as e:
            print(f"Error playing sound {sound_name}: {e}")
            return False

    def play_music(self, music_file: str, loop: bool = True) -> bool:
        """
        Play background music.

        Args:
            music_file: Path to music file
            loop: Whether to loop the music

        Returns:
            True if music started, False otherwise
        """
        if self.is_muted:
            return False

        try:
            if os.path.exists(music_file):
                pygame.mixer.music.load(music_file)
                pygame.mixer.music.set_volume(self.music_volume)

                if loop:
                    pygame.mixer.music.play(-1)  # -1 means loop indefinitely
                else:
                    pygame.mixer.music.play()

                return True
            else:
                print(f"Music file not found: {music_file}")
                return False

        except pygame.error as e:
            print(f"Error playing music: {e}")
            return False

    def stop_music(self) -> None:
        """Stop background music."""
        pygame.mixer.music.stop()

    def pause_music(self) -> None:
        """Pause background music."""
        pygame.mixer.music.pause()

    def unpause_music(self) -> None:
        """Unpause background music."""
        pygame.mixer.music.unpause()

    def set_music_volume(self, volume: float) -> None:
        """
        Set background music volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume: float) -> None:
        """
        Set sound effects volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.sfx_volume)

    def toggle_mute(self) -> bool:
        """
        Toggle mute state.

        Returns:
            New mute state (True = muted, False = unmuted)
        """
        self.is_muted = not self.is_muted

        if self.is_muted:
            pygame.mixer.music.set_volume(0.0)
            for sound in self.sounds.values():
                sound.set_volume(0.0)
        else:
            pygame.mixer.music.set_volume(self.music_volume)
            for sound in self.sounds.values():
                sound.set_volume(self.sfx_volume)

        return self.is_muted

    def preload_all(self) -> None:
        """
        Preload all sounds to reduce lag during gameplay.
        This plays each sound once at zero volume.
        """
        print("Preloading sounds...")
        for sound_name in self.sounds:
            try:
                sound = self.sounds[sound_name]
                original_volume = sound.get_volume()
                sound.set_volume(0.0)
                sound.play()
                sound.set_volume(original_volume)
            except Exception:
                pass
        print("Sound preloading complete")


if __name__ == "__main__":
    print("=== Testing SoundManager ===")

    # Initialize pygame mixer
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

    # Create sound manager
    manager = SoundManager()

    # Test loading sounds (will create placeholders)
    success = manager.load_sounds("assets")
    print(f"Sound loading successful: {success}")

    # Test playing sounds
    test_sounds = ["click", "hover", "correct", "wrong"]
    for sound_name in test_sounds:
        played = manager.play_sound(sound_name)
        print(f"Played {sound_name}: {played}")
        pygame.time.delay(200)  # Small delay between sounds

    # Test volume control
    manager.set_sfx_volume(0.5)
    manager.set_music_volume(0.3)
    print(f"SFX volume: {manager.sfx_volume}")
    print(f"Music volume: {manager.music_volume}")

    # Test mute toggle
    muted = manager.toggle_mute()
    print(f"Muted: {muted}")

    unmuted = manager.toggle_mute()
    print(f"Muted: {unmuted}")

    print("\nAll tests passed!")