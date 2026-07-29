"""
AIAvatarWidget — Animated AI face for Command Nexus chat windows
===============================================================
Supports:
  - Static image (default)
  - Animated GIF
  - Video loop (MP4/WebM)
  - Frame-cycling from pose images (for character sheets)

States: idle, listening, talking, thinking
"""

from __future__ import annotations
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QMovie, QPixmap, QPainter, QFont, QColor
from PySide6.QtWidgets import QLabel, QWidget, QVBoxLayout, QHBoxLayout, QSizePolicy
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget


class AIAvatarWidget(QWidget):
    """
    Displays an AI avatar with animated states.
    Place next to chat window for visual feedback.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        idle_image: str | None = None,
        idle_video: str | None = None,  # body movement / breathing loop
        talking_video: str | None = None,  # head talking / mouth movement
        talking_gif: str | None = None,
        pose_frames: list[str] | None = None,
        size: QSize = QSize(280, 420),
        fallback_text: str = "AI",
    ):
        super().__init__(parent)
        self._size = size
        self._fallback_text = fallback_text
        self._current_state = "idle"

        # Frame cycling for pose-based animation
        self._pose_frames: list[QPixmap] = []
        self._pose_index = 0
        self._pose_timer = QTimer(self)
        self._pose_timer.timeout.connect(self._next_pose_frame)

        # Idle video player (body movement / breathing)
        self._idle_media_player: QMediaPlayer | None = None
        self._idle_video_widget: QVideoWidget | None = None

        # Talking video player (head/mouth movement)
        self._talk_media_player: QMediaPlayer | None = None
        self._talk_video_widget: QVideoWidget | None = None

        # GIF movie
        self._movie: QMovie | None = None

        self._setup_ui()
        self._load_assets(idle_image, idle_video, talking_video, talking_gif, pose_frames)

    def _setup_ui(self):
        self.setFixedSize(self._size)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background-color: transparent; border: none;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Stacked widget container for image + dual videos
        from PySide6.QtWidgets import QStackedWidget
        self._stack = QStackedWidget(self)
        self._stack.setFixedSize(self._size)

        # Page 0: Static image / GIF display
        self._display = QLabel(self._stack)
        self._display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._display.setScaledContents(True)
        self._display.setFixedSize(self._size)
        self._stack.addWidget(self._display)

        # Page 1: Idle video (body movement / breathing)
        self._idle_video_widget = QVideoWidget(self._stack)
        self._idle_video_widget.setFixedSize(self._size)
        self._stack.addWidget(self._idle_video_widget)

        # Page 2: Talking video (head/mouth movement)
        self._talk_video_widget = QVideoWidget(self._stack)
        self._talk_video_widget.setFixedSize(self._size)
        self._stack.addWidget(self._talk_video_widget)

        layout.addWidget(self._stack, alignment=Qt.AlignmentFlag.AlignCenter)

        # Status indicator dot (small colored circle for state)
        self._status_label = QLabel("●")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("color: #3fb950; font-size: 10px; background: transparent;")
        layout.addWidget(self._status_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def _load_assets(
        self,
        idle_image: str | None,
        idle_video: str | None,
        talking_video: str | None,
        talking_gif: str | None,
        pose_frames: list[str] | None,
    ):
        from PySide6.QtCore import QUrl

        # Load idle image
        if idle_image and Path(idle_image).exists():
            self._idle_pixmap = QPixmap(idle_image)
            self._display.setPixmap(self._idle_pixmap)
        else:
            self._idle_pixmap = self._generate_placeholder()
            self._display.setPixmap(self._idle_pixmap)

        # Load pose frames for cycling animation
        if pose_frames:
            self._pose_frames = []
            for p in pose_frames:
                if Path(p).exists():
                    self._pose_frames.append(QPixmap(p))
            if self._pose_frames:
                self._display.setPixmap(self._pose_frames[0])

        # Setup GIF
        if talking_gif and Path(talking_gif).exists():
            self._movie = QMovie(talking_gif)
            self._movie.setScaledSize(self._size)

        # Setup idle video (body movement / breathing loop)
        if idle_video and Path(idle_video).exists():
            self._idle_media_player = QMediaPlayer(self)
            self._idle_media_player.setVideoOutput(self._idle_video_widget)
            self._idle_media_player.setSource(QUrl.fromLocalFile(str(Path(idle_video).resolve())))
            self._idle_media_player.setLoops(QMediaPlayer.Loops.Infinite)

        # Setup talking video (head/mouth movement)
        if talking_video and Path(talking_video).exists():
            self._talk_media_player = QMediaPlayer(self)
            self._talk_media_player.setVideoOutput(self._talk_video_widget)
            self._talk_media_player.setSource(QUrl.fromLocalFile(str(Path(talking_video).resolve())))
            self._talk_media_player.setLoops(QMediaPlayer.Loops.Infinite)

    def _generate_placeholder(self) -> QPixmap:
        """Generate a simple circular avatar placeholder with initials."""
        pm = QPixmap(self._size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Circle background
        painter.setBrush(QColor("#21262d"))
        painter.setPen(QColor("#30363d"))
        cx, cy = self._size.width() // 2, self._size.height() // 2
        radius = min(cx, cy) - 10
        painter.drawEllipse(cx - radius, cy - radius - 30, radius * 2, radius * 2)

        # Text
        painter.setPen(QColor("#58a6ff"))
        font = QFont("Segoe UI", 28, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(pm.rect().adjusted(0, -20, 0, 0), Qt.AlignmentFlag.AlignCenter, self._fallback_text)
        painter.end()
        return pm

    def set_state(self, state: str):
        """
        Set avatar state: idle, listening, talking, thinking.
        Automatically handles animation transitions.
        """
        if self._current_state == state:
            return
        self._current_state = state

        if state == "idle":
            self._stop_all_animations()
            self._start_idle_animation()
            self._status_label.setStyleSheet("color: #3fb950; font-size: 10px; background: transparent;")  # green
            self._status_label.setText("● idle")

        elif state == "listening":
            self._stop_all_animations()
            self._start_idle_animation()
            self._status_label.setStyleSheet("color: #58a6ff; font-size: 10px; background: transparent;")  # blue
            self._status_label.setText("● listening")

        elif state == "talking":
            self._status_label.setStyleSheet("color: #d29922; font-size: 10px; background: transparent;")  # amber
            self._status_label.setText("● talking")
            self._start_talking_animation()

        elif state == "thinking":
            self._stop_all_animations()
            self._start_idle_animation()
            self._status_label.setStyleSheet("color: #a371f7; font-size: 10px; background: transparent;")  # purple
            self._status_label.setText("● thinking")

    def _start_idle_animation(self):
        """Show the idle visual: idle video > static image."""
        if self._idle_media_player:
            self._stack.setCurrentIndex(1)  # Show idle video page
            self._idle_media_player.play()
        else:
            self._stack.setCurrentIndex(0)  # Show static image page
            self._display.setPixmap(self._idle_pixmap)

    def _start_talking_animation(self):
        """Choose the best available talking animation method."""
        # Priority: talking video > idle video > gif > pose frames > static image
        if self._talk_media_player:
            self._stack.setCurrentIndex(2)  # Show talking video page
            self._talk_media_player.play()
            return

        if self._idle_media_player:
            self._stack.setCurrentIndex(1)
            self._idle_media_player.play()
            return

        if self._movie:
            self._stack.setCurrentIndex(0)
            self._display.setMovie(self._movie)
            self._movie.start()
            return

        if self._pose_frames:
            self._stack.setCurrentIndex(0)
            self._pose_timer.start(150)  # ~6-7 fps for pose cycling
            return

        # Fallback: just show idle image
        self._stack.setCurrentIndex(0)
        self._display.setPixmap(self._idle_pixmap)

    def _next_pose_frame(self):
        """Cycle to next pose frame."""
        if not self._pose_frames:
            return
        self._pose_index = (self._pose_index + 1) % len(self._pose_frames)
        self._display.setPixmap(self._pose_frames[self._pose_index])

    def _stop_all_animations(self):
        """Stop all active animations."""
        self._pose_timer.stop()
        if self._movie:
            self._movie.stop()
            self._display.setMovie(None)
        if self._talk_media_player:
            self._talk_media_player.stop()
        if self._idle_media_player:
            self._idle_media_player.stop()

    def set_idle_image(self, path: str):
        """Update the idle image (e.g., user's character sheet front pose)."""
        if Path(path).exists():
            self._idle_pixmap = QPixmap(path)
            if self._current_state == "idle":
                self._display.setPixmap(self._idle_pixmap)

    def add_pose_frames(self, paths: list[str]):
        """Add pose frame images for animation cycling."""
        self._pose_frames = []
        for p in paths:
            if Path(p).exists():
                self._pose_frames.append(QPixmap(p))

    def set_idle_video(self, path: str):
        """Set a looping video for idle/body movement state."""
        if not Path(path).exists():
            return
        from PySide6.QtCore import QUrl
        if self._idle_media_player is None:
            self._idle_media_player = QMediaPlayer(self)
            self._idle_media_player.setVideoOutput(self._idle_video_widget)
        self._idle_media_player.setSource(QUrl.fromLocalFile(str(Path(path).resolve())))
        self._idle_media_player.setLoops(QMediaPlayer.Loops.Infinite)

    def set_talking_video(self, path: str):
        """Set a looping video for the talking state."""
        if not Path(path).exists():
            return
        from PySide6.QtCore import QUrl
        if self._talk_media_player is None:
            self._talk_media_player = QMediaPlayer(self)
            self._talk_media_player.setVideoOutput(self._talk_video_widget)
        self._talk_media_player.setSource(QUrl.fromLocalFile(str(Path(path).resolve())))
        self._talk_media_player.setLoops(QMediaPlayer.Loops.Infinite)

    def set_talking_gif(self, path: str):
        """Set an animated GIF for the talking state."""
        if not Path(path).exists():
            return
        if self._movie:
            self._movie.stop()
        self._movie = QMovie(path)
        self._movie.setScaledSize(self._size)

    def resizeEvent(self, event):
        """Keep display and video sized to widget."""
        super().resizeEvent(event)
        new_size = self.size()
        self._display.setFixedSize(new_size)
        if self._idle_video_widget:
            self._idle_video_widget.setFixedSize(new_size)
        if self._talk_video_widget:
            self._talk_video_widget.setFixedSize(new_size)


def avatar_for_ai(ai_name: str, avatar_dir: str | None = None) -> AIAvatarWidget:
    """
    Convenience factory: looks for common avatar assets in a directory.
    Expected files in avatar_dir:
      - idle.png / idle.jpg        (static idle image)
      - body.mp4 / idle.mp4        (idle body movement video loop)
      - head.mp4 / talking.mp4     (talking head/mouth movement video)
      - talking.gif                (animated GIF fallback)
      - pose_01.png, pose_02.png, ... (frame sequence)
    """
    idle_img = None
    idle_vid = None
    talk_gif = None
    talk_vid = None
    poses = []

    if avatar_dir:
        d = Path(avatar_dir)
        # Static idle image
        for ext in (".png", ".jpg", ".jpeg"):
            if (d / f"idle{ext}").exists():
                idle_img = str(d / f"idle{ext}")
                break
        # Idle body movement video
        for name in ("body", "idle"):
            for ext in (".mp4", ".webm", ".mov"):
                if (d / f"{name}{ext}").exists():
                    idle_vid = str(d / f"{name}{ext}")
                    break
            if idle_vid:
                break
        # Talking head video
        for name in ("head", "talking"):
            for ext in (".mp4", ".webm", ".mov"):
                if (d / f"{name}{ext}").exists():
                    talk_vid = str(d / f"{name}{ext}")
                    break
            if talk_vid:
                break
        # GIF fallback
        for ext in (".gif",):
            if (d / f"talking{ext}").exists():
                talk_gif = str(d / f"talking{ext}")
                break
        # Pose frames
        for f in sorted(d.glob("pose_*")):
            if f.suffix.lower() in (".png", ".jpg", ".jpeg"):
                poses.append(str(f))

    return AIAvatarWidget(
        idle_image=idle_img,
        idle_video=idle_vid,
        talking_video=talk_vid,
        talking_gif=talk_gif,
        pose_frames=poses if poses else None,
        fallback_text=ai_name[:2].upper(),
    )
