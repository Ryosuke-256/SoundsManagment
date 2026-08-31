"""
Unit tests for AudioPlayerService (Unit 3).
Tests playback states, volume/mute control, looping, seeking, and fault tolerance.
"""

import os
import sys
import unittest
import wave

from PyQt6.QtCore import QCoreApplication
from src.audio.player_service import AudioPlayerService, PlaybackState


class TestUnit3AudioPlayerService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication(sys.argv)
        else:
            cls.app = QCoreApplication.instance()

    def setUp(self):
        self.player = AudioPlayerService(headless=True)
        self.test_wav_path = "test_player_sample.wav"
        # Create a small valid WAV file
        with wave.open(self.test_wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(44100)
            wf.writeframes(b"\x00\x00" * 44100)  # 1 second of silence

    def tearDown(self):
        if os.path.exists(self.test_wav_path):
            try:
                os.remove(self.test_wav_path)
            except OSError:
                pass

    def test_initial_state(self):
        self.assertEqual(self.player.state, PlaybackState.STOPPED)
        self.assertEqual(self.player.position_ms, 0)
        self.assertTrue(self.player.auto_play)
        self.assertFalse(self.player.loop_playback)
        self.assertAlmostEqual(self.player.volume, 0.8)
        self.assertFalse(self.player.is_muted)

    def test_volume_and_mute_control(self):
        # Clamping
        self.player.set_volume(1.5)
        self.assertEqual(self.player.volume, 1.0)
        self.player.set_volume(-0.5)
        self.assertEqual(self.player.volume, 0.0)
        self.player.set_volume(0.5)
        self.assertEqual(self.player.volume, 0.5)

        # Mute toggle
        self.player.set_muted(True)
        self.assertTrue(self.player.is_muted)
        self.player.toggle_mute()
        self.assertFalse(self.player.is_muted)

    def test_mode_toggles(self):
        self.player.set_auto_play(False)
        self.assertFalse(self.player.auto_play)

        self.player.set_loop_playback(True)
        self.assertTrue(self.player.loop_playback)

    def test_play_pause_resume_stop_lifecycle(self):
        self.player.play_sample(self.test_wav_path, is_loop=False, force_play=True)
        self.assertEqual(self.player.state, PlaybackState.PLAYING)

        self.player.pause()
        self.assertEqual(self.player.state, PlaybackState.PAUSED)

        self.player.resume()
        self.assertEqual(self.player.state, PlaybackState.PLAYING)

        self.player.stop()
        self.assertEqual(self.player.state, PlaybackState.STOPPED)
        self.assertEqual(self.player.position_ms, 0)

    def test_toggle_play_pause(self):
        self.player.play_sample(self.test_wav_path, force_play=False)
        self.player.set_auto_play(False)
        self.player.play_sample(self.test_wav_path, force_play=False)
        self.assertEqual(self.player.state, PlaybackState.STOPPED)

        self.player.toggle_play_pause()
        self.assertEqual(self.player.state, PlaybackState.PLAYING)

        self.player.toggle_play_pause()
        self.assertEqual(self.player.state, PlaybackState.PAUSED)

    def test_seek_clamping(self):
        self.player._duration_ms = 10000  # 10s
        self.player.seek_ms(5000)
        self.assertEqual(self.player.position_ms, 5000)

        # Seek past duration
        self.player.seek_ms(15000)
        self.assertEqual(self.player.position_ms, 10000)

        # Seek negative
        self.player.seek_ms(-500)
        self.assertEqual(self.player.position_ms, 0)

        # Seek ratio
        self.player.seek_ratio(0.75)
        self.assertEqual(self.player.position_ms, 7500)

    def test_nonexistent_file_resilience(self):
        errors = []
        self.player.error_occurred.connect(lambda err: errors.append(err))

        self.player.play_sample("non_existent_audio_file.wav")
        self.assertEqual(self.player.state, PlaybackState.STOPPED)
        self.assertTrue(len(errors) > 0)


if __name__ == "__main__":
    unittest.main()
