from pathlib import Path

import pygame


DEFAULT_MUSIC_VOLUME = 0.30
DEFAULT_SOUND_EFFECT_VOLUME = 0.65
MUSIC_FADE_IN_MS = 500
_current_track = None
_current_music_volume = DEFAULT_MUSIC_VOLUME
_master_volume = 1.0
_sound_effect_cache = {}


def get_master_volume():
    return _master_volume


def set_master_volume(volume):
    """Set the shared music/effect volume from 0.0 to 1.0."""
    global _master_volume

    _master_volume = max(0.0, min(1.0, float(volume)))
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(
                _current_music_volume * _master_volume
            )
    except pygame.error:
        pass
    return _master_volume


def play_background_music(path, volume=DEFAULT_MUSIC_VOLUME):
    """Loop a map track, safely doing nothing when audio is unavailable."""
    global _current_track, _current_music_volume

    track = str(Path(path).resolve())
    _current_music_volume = max(0.0, min(1.0, float(volume)))
    effective_volume = _current_music_volume * _master_volume
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        if _current_track == track and pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(effective_volume)
            return True

        pygame.mixer.music.load(track)
        pygame.mixer.music.set_volume(effective_volume)
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

        base_volume = max(0.0, min(1.0, float(volume)))
        sound.set_volume(base_volume * _master_volume)
        sound.play(maxtime=max(0, int(max_duration_ms)))
        return True
    except (OSError, pygame.error):
        return False
