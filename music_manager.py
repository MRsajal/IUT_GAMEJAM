from pathlib import Path

import pygame


DEFAULT_MUSIC_VOLUME = 0.30
DEFAULT_SOUND_EFFECT_VOLUME = 0.65
MUSIC_FADE_IN_MS = 500
_current_track = None
_sound_effect_cache = {}


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


def play_sound_effect(
    path,
    volume=DEFAULT_SOUND_EFFECT_VOLUME,
    max_duration_ms=0,
):
    """Play and cache a short effect without interrupting map music."""
    effect_path = str(Path(path).resolve())
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        sound = _sound_effect_cache.get(effect_path)
        if sound is None:
            sound = pygame.mixer.Sound(effect_path)
            _sound_effect_cache[effect_path] = sound

        sound.set_volume(max(0.0, min(1.0, volume)))
        sound.play(maxtime=max(0, int(max_duration_ms)))
        return True
    except (OSError, pygame.error):
        return False
