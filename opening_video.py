"""Opening cinematic playback for the game."""

from pathlib import Path

import pygame


VIDEO_PATH = Path(__file__).parent / "openingvid" / "opening_vid.mp4"
SLIME_VIDEO_PATH = Path(__file__).parent / "openingvid" / "slime_map.mp4"


def play_video(video_path, screen_size=(600, 320)):
    """Play an MP4. SPACE/ENTER skips and ESC quits playback."""
    try:
        import cv2
    except ImportError:
        print(
            "Opening video skipped: install OpenCV with "
            "'python -m pip install opencv-python'."
        )
        return True

    video_path = Path(video_path)
    if not video_path.exists():
        print(f"Video not found: {video_path}")
        return True

    screen = pygame.display.set_mode(screen_size)
    pygame.display.set_caption("Arcane Kickoff")
    clock = pygame.time.Clock()
    video = cv2.VideoCapture(str(video_path))
    fps = video.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30

    keep_playing = True
    continue_game = True
    while keep_playing:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                keep_playing = False
                continue_game = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    keep_playing = False
                    continue_game = False
                elif event.key in (
                    pygame.K_SPACE,
                    pygame.K_RETURN,
                    pygame.K_KP_ENTER,
                ):
                    keep_playing = False

        if not keep_playing:
            break

        success, frame = video.read()
        if not success:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame_height, frame_width = frame.shape[:2]
        frame_surface = pygame.image.frombuffer(
            frame.tobytes(), (frame_width, frame_height), "RGB"
        )

        screen_width, screen_height = screen_size
        scale = min(
            screen_width / frame_width,
            screen_height / frame_height,
        )
        target_size = (
            max(1, round(frame_width * scale)),
            max(1, round(frame_height * scale)),
        )
        frame_surface = pygame.transform.smoothscale(
            frame_surface, target_size
        )
        frame_rect = frame_surface.get_rect(
            center=(screen_width // 2, screen_height // 2)
        )

        screen.fill((0, 0, 0))
        screen.blit(frame_surface, frame_rect)
        skip_font = pygame.font.Font(None, 18)
        skip_text = skip_font.render(
            "SPACE: Skip", True, (235, 235, 235)
        )
        screen.blit(skip_text, (screen_width - skip_text.get_width() - 10, 8))
        pygame.display.flip()
        clock.tick(round(fps))

    video.release()
    return continue_game


def play_opening_video(screen_size=(600, 320)):
    return play_video(VIDEO_PATH, screen_size)
