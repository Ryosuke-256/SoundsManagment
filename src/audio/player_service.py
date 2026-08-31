"""
Audio Player Service wrapping PyQt6 QMediaPlayer and QAudioOutput.
Provides high-level playback state management, looping, seek, volume, and Qt signals.
"""

from enum import Enum, auto
import logging
import os
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QUrl
try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    HAS_QT_MULTIMEDIA = True
except ImportError:
    HAS_QT_MULTIMEDIA = False

logger = logging.getLogger(__name__)


from dataclasses import dataclass

class PlaybackState(Enum):
    """Audio playback state enum."""
    STOPPED = auto()
    PLAYING = auto()
    PAUSED = auto()


@dataclass
class PlaybackMode:
    """Audio playback settings and modes."""
    auto_play: bool = True
    loop_playback: bool = False
    volume: float = 0.8
    is_muted: bool = False


class AudioPlayerService(QObject):
    """
    High-level audio playback service for BandLab Sound Manager.
    Encapsulates QMediaPlayer, QAudioOutput, and provides event signals.
    """

    # Qt Custom Signals
    state_changed = pyqtSignal(object)           # PlaybackState
    progress_changed = pyqtSignal(int, int)      # (position_ms, duration_ms)
    source_changed = pyqtSignal(str)             # current file path
    volume_changed = pyqtSignal(float, bool)     # (volume 0.0-1.0, is_muted)
    mode_changed = pyqtSignal(bool, bool)        # (auto_play, loop_playback)
    error_occurred = pyqtSignal(str)             # error message

    def __init__(self, headless: bool = False, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._headless = headless or not HAS_QT_MULTIMEDIA

        self._state = PlaybackState.STOPPED
        self._current_file: Optional[str] = None
        self._current_is_loop_type: bool = False
        self._duration_ms: int = 0
        self._position_ms: int = 0

        self._auto_play: bool = True
        self._loop_playback: bool = False
        self._volume: float = 0.8
        self._is_muted: bool = False

        self._player: Optional[QMediaPlayer] = None
        self._audio_output: Optional[QAudioOutput] = None

        if not self._headless:
            self._init_player()

    def _init_player(self) -> None:
        """Initializes PyQt6 QtMultimedia player and audio output."""
        try:
            self._player = QMediaPlayer(self)
            self._audio_output = QAudioOutput(self)
            self._player.setAudioOutput(self._audio_output)

            self._audio_output.setVolume(self._volume)
            self._audio_output.setMuted(self._is_muted)

            # Connect signals
            self._player.positionChanged.connect(self._on_position_changed)
            self._player.durationChanged.connect(self._on_duration_changed)
            self._player.mediaStatusChanged.connect(self._on_media_status_changed)
            self._player.errorOccurred.connect(self._on_player_error)
        except Exception as e:
            logger.warning("Failed to initialize QMediaPlayer, falling back to headless mode: %s", e)
            self._headless = True
            self._player = None
            self._audio_output = None

    # --- Properties ---

    @property
    def state(self) -> PlaybackState:
        return self._state

    @property
    def current_file(self) -> Optional[str]:
        return self._current_file

    @property
    def duration_ms(self) -> int:
        return self._duration_ms

    @property
    def position_ms(self) -> int:
        return self._position_ms

    @property
    def auto_play(self) -> bool:
        return self._auto_play

    @property
    def loop_playback(self) -> bool:
        return self._loop_playback

    @property
    def volume(self) -> float:
        return self._volume

    @property
    def is_muted(self) -> bool:
        return self._is_muted

    # --- Control Methods ---

    def set_auto_play(self, enabled: bool) -> None:
        """Sets the global Auto-Play toggle."""
        if self._auto_play != enabled:
            self._auto_play = enabled
            self.mode_changed.emit(self._auto_play, self._loop_playback)

    def set_loop_playback(self, enabled: bool) -> None:
        """Sets the global Loop-Playback toggle."""
        if self._loop_playback != enabled:
            self._loop_playback = enabled
            self.mode_changed.emit(self._auto_play, self._loop_playback)

    def set_volume(self, volume: float) -> None:
        """Sets output volume clamped between 0.0 and 1.0."""
        clamped = max(0.0, min(1.0, float(volume)))
        self._volume = clamped
        if self._audio_output and not self._headless:
            self._audio_output.setVolume(clamped)
        self.volume_changed.emit(self._volume, self._is_muted)

    def set_muted(self, muted: bool) -> None:
        """Mutes or unmutes the audio output."""
        self._is_muted = bool(muted)
        if self._audio_output and not self._headless:
            self._audio_output.setMuted(self._is_muted)
        self.volume_changed.emit(self._volume, self._is_muted)

    def toggle_mute(self) -> bool:
        """Toggles mute state and returns new muted state."""
        self.set_muted(not self._is_muted)
        return self._is_muted

    def play_sample(self, file_path: str, is_loop: bool = False, force_play: bool = False) -> None:
        """
        Loads a sample file and triggers playback if Auto-Play is ON or force_play is True.

        Args:
            file_path: Absolute path to the sound file.
            is_loop: Whether this specific sound is categorized as 'Loop' type.
            force_play: Explicitly play regardless of auto_play setting.
        """
        if not file_path:
            self._handle_error("Empty file path provided")
            return

        norm_path = os.path.abspath(file_path)
        if not os.path.isfile(norm_path):
            self._handle_error(f"File not found: {norm_path}")
            return

        self._current_file = norm_path
        self._current_is_loop_type = is_loop
        self._position_ms = 0
        self.source_changed.emit(norm_path)

        if not self._headless and self._player:
            try:
                url = QUrl.fromLocalFile(norm_path)
                self._player.setSource(url)
            except Exception as e:
                logger.error("Error setting media source: %s", e)
                self._handle_error(f"Failed to load audio: {e}")
                return

        if self._auto_play or force_play:
            self.play()
        else:
            self._set_state(PlaybackState.STOPPED)

    def play(self) -> None:
        """Starts or resumes audio playback."""
        if not self._current_file:
            return

        self._set_state(PlaybackState.PLAYING)
        if not self._headless and self._player:
            try:
                self._player.play()
            except Exception as e:
                logger.error("Error playing audio: %s", e)
                self._handle_error(f"Playback failed: {e}")

    def pause(self) -> None:
        """Pauses audio playback."""
        if self._state == PlaybackState.PLAYING:
            self._set_state(PlaybackState.PAUSED)
            if not self._headless and self._player:
                try:
                    self._player.pause()
                except Exception as e:
                    logger.error("Error pausing audio: %s", e)

    def resume(self) -> None:
        """Resumes playback from paused position."""
        if self._state == PlaybackState.PAUSED:
            self.play()

    def stop(self) -> None:
        """Stops playback and rewinds position to 0ms."""
        self._position_ms = 0
        self._set_state(PlaybackState.STOPPED)
        if not self._headless and self._player:
            try:
                self._player.stop()
                self._player.setPosition(0)
            except Exception as e:
                logger.error("Error stopping audio: %s", e)
        self.progress_changed.emit(0, self._duration_ms)

    def toggle_play_pause(self) -> None:
        """Toggles between Playing and Paused/Stopped."""
        if self._state == PlaybackState.PLAYING:
            self.pause()
        elif self._state == PlaybackState.PAUSED:
            self.resume()
        elif self._state == PlaybackState.STOPPED:
            self.play()

    def seek_ms(self, position_ms: int) -> None:
        """Seeks playback to the specified millisecond position."""
        target = max(0, min(position_ms, self._duration_ms if self._duration_ms > 0 else position_ms))
        self._position_ms = target
        if not self._headless and self._player:
            self._player.setPosition(target)
        self.progress_changed.emit(self._position_ms, self._duration_ms)

    def seek_ratio(self, ratio: float) -> None:
        """Seeks playback to a normalized ratio (0.0 to 1.0) of duration."""
        clamped_ratio = max(0.0, min(1.0, float(ratio)))
        if self._duration_ms > 0:
            target_ms = int(clamped_ratio * self._duration_ms)
            self.seek_ms(target_ms)

    # --- Internal Event Handlers ---

    def _set_state(self, new_state: PlaybackState) -> None:
        if self._state != new_state:
            self._state = new_state
            self.state_changed.emit(self._state)

    def _on_position_changed(self, position_ms: int) -> None:
        self._position_ms = position_ms
        self.progress_changed.emit(self._position_ms, self._duration_ms)

    def _on_duration_changed(self, duration_ms: int) -> None:
        self._duration_ms = duration_ms
        self.progress_changed.emit(self._position_ms, self._duration_ms)

    def _on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            # Check if track should loop (Global Loop ON or Type is 'Loop')
            if self._loop_playback or self._current_is_loop_type:
                logger.debug("Looping sample: %s", self._current_file)
                self.seek_ms(0)
                self.play()
            else:
                self.stop()

    def _on_player_error(self, error: QMediaPlayer.Error, error_string: str) -> None:
        logger.error("QMediaPlayer error (%s): %s", error, error_string)
        self._handle_error(f"Playback error: {error_string}")

    def _handle_error(self, msg: str) -> None:
        self._set_state(PlaybackState.STOPPED)
        self.error_occurred.emit(msg)
