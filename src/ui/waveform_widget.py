"""
Interactive Waveform Visualization Widget for BandLab Sound Manager.
Draws peak amplitudes, playback progress overlay, playhead, and handles click/drag seeks.
"""

import math
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient, QMouseEvent, QPaintEvent
from PyQt6.QtWidgets import QWidget

from src.audio.waveform_extractor import WaveformData


class WaveformWidget(QWidget):
    """
    Custom QWidget rendering normalized audio waveform peaks with interactive seek.
    """

    # Emitted when user clicks or drags across the waveform to seek (ratio: 0.0 - 1.0)
    seek_requested = pyqtSignal(float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumHeight(64)
        self.setMouseTracking(False)

        self._waveform_data: Optional[WaveformData] = None
        self._progress_ratio: float = 0.0
        self._position_ms: int = 0
        self._duration_ms: int = 0
        self._is_dragging: bool = False

        # Theme Colors
        self._bg_color = QColor("#1e1e24")
        self._bar_color_unplayed = QColor("#4a5568")
        self._bar_color_played = QColor("#00d2ff")
        self._center_line_color = QColor("#2d3748")
        self._playhead_color = QColor("#ffffff")

    def set_waveform_data(self, data: Optional[WaveformData]) -> None:
        """Sets the active waveform data and triggers a repaint."""
        self._waveform_data = data
        self._progress_ratio = 0.0
        self.update()

    def set_waveform(self, data: Optional[WaveformData]) -> None:
        """Alias for set_waveform_data."""
        self.set_waveform_data(data)

    def set_position(self, pos_ms: int) -> None:
        """Sets current position in milliseconds and updates progress."""
        self._position_ms = pos_ms
        self.set_playback_progress(pos_ms, self._duration_ms)

    def set_duration(self, dur_ms: int) -> None:
        """Sets total duration in milliseconds and updates progress."""
        self._duration_ms = dur_ms
        self.set_playback_progress(self._position_ms, dur_ms)

    def set_playback_progress(self, position_ms: int, duration_ms: int) -> None:
        """Updates playback progress ratio and triggers repaint."""
        self._position_ms = position_ms
        self._duration_ms = duration_ms
        if duration_ms > 0:
            ratio = max(0.0, min(1.0, position_ms / duration_ms))
        else:
            ratio = 0.0

        if not math.isclose(self._progress_ratio, ratio, abs_tol=1e-3):
            self._progress_ratio = ratio
            self.update()

    def clear(self) -> None:
        """Clears current waveform."""
        self.set_waveform_data(None)

    # --- Mouse Event Handlers for Seeking ---

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._handle_seek_event(event.position().x())

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._is_dragging:
            self._handle_seek_event(event.position().x())

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = False

    def _handle_seek_event(self, mouse_x: float) -> None:
        width = self.width()
        if width > 0:
            ratio = max(0.0, min(1.0, mouse_x / width))
            self._progress_ratio = ratio
            self.seek_requested.emit(ratio)
            self.update()

    # --- Custom Painting ---

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        width = self.width()
        height = self.height()
        half_h = height / 2.0

        # Draw Background
        painter.fillRect(0, 0, width, height, self._bg_color)

        # Draw Center Guideline
        painter.setPen(QPen(self._center_line_color, 1))
        painter.drawLine(0, int(half_h), width, int(half_h))

        if not self._waveform_data or not self._waveform_data.peaks_min or not self._waveform_data.is_valid:
            # If no data or null waveform, draw simple placeholder line
            return

        peaks_min = self._waveform_data.peaks_min
        peaks_max = self._waveform_data.peaks_max
        n_bins = len(peaks_min)

        if n_bins == 0:
            return

        # Calculate bar geometry
        bar_width = max(1.0, width / n_bins)
        playhead_x = width * self._progress_ratio

        # Draw waveform vertical bars
        for i in range(n_bins):
            x = i * bar_width
            mn = peaks_min[i]
            mx = peaks_max[i]

            # Scale amplitude to half-height with slight headroom
            top_y = half_h - (mx * half_h * 0.9)
            bottom_y = half_h - (mn * half_h * 0.9)

            bar_h = max(2.0, bottom_y - top_y)
            bar_y = top_y

            # Choose color based on whether bar is to the left of playhead
            if x + bar_width <= playhead_x:
                color = self._bar_color_played
            else:
                color = self._bar_color_unplayed

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(color))
            painter.drawRoundedRect(QRectF(x, bar_y, max(1.0, bar_width - 1.0), bar_h), 1.0, 1.0)

        # Draw Playhead vertical line
        if self._progress_ratio > 0.0:
            painter.setPen(QPen(self._playhead_color, 2))
            painter.drawLine(int(playhead_x), 0, int(playhead_x), height)
