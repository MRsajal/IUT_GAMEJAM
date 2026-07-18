from pathlib import Path

import pygame


DEFAULT_MUSIC_VOLUME = 0.30
MUSIC_FADE_IN_MS = 500
_current_track = None


def play_background_music(path, volume=DEFAULT_MUSIC_VOLUME):
    """Loop a map track, safely doing nothing when audio is unavailable."""
    global _current_track

    track = str(Path(path).resolve())
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        if _current_track == track and pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(volume)
            return True

        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=-1, fade_ms=MUSIC_FADE_IN_MS)
        _current_track = track
        return True
    except (OSError, pygame.error):
        _current_track = None
        return False
