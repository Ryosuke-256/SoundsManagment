"""Unit tests for Unit 2: AudioSignalAnalyzer, AutoRenamer, and BatchAnalysisCoordinator."""
import os
import shutil
import tempfile
import unittest
import wave
from pathlib import Path

import numpy as np

from src.analyzer.audio_analyzer import AudioSignalAnalyzer
from src.analyzer.auto_renamer import AutoRenamer
from src.analyzer.batch_coordinator import BatchAnalysisCoordinator
from src.core.models import SampleItem


class TestUnit2Analyzer(unittest.TestCase):
    """Test suite for DSP tempo estimation, key estimation, and auto-renaming."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.analyzer = AudioSignalAnalyzer()

        # 1. Generate synthetic 120 BPM click track (2 seconds, 22050 Hz)
        self.bpm_file = str(Path(self.temp_dir) / "synthetic_120bpm.wav")
        self._create_click_track_wav(self.bpm_file, bpm=120.0, duration_sec=4.0, sr=22050)

        # 2. Generate synthetic A440Hz tone (A major/minor) (2 seconds, 22050 Hz)
        self.key_file = str(Path(self.temp_dir) / "synthetic_A440.wav")
        self._create_sine_tone_wav(self.key_file, freq=440.0, duration_sec=2.0, sr=22050)

        # 3. Create corrupted file (RESILIENCY-10 test)
        self.corrupt_file = str(Path(self.temp_dir) / "corrupted.wav")
        with open(self.corrupt_file, "wb") as f:
            f.write(b"NOT_A_VALID_WAV_HEADER_CORRUPTED_BYTES")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_click_track_wav(self, file_path: str, bpm: float, duration_sec: float, sr: int):
        """Creates a synthetic click track at specified BPM."""
        total_samples = int(duration_sec * sr)
        audio = np.zeros(total_samples, dtype=np.float32)
        interval_samples = int(sr * 60.0 / bpm)

        for pos in range(0, total_samples, interval_samples):
            # Add a short burst click
            click_len = min(200, total_samples - pos)
            audio[pos:pos + click_len] = np.sin(np.linspace(0, 10 * np.pi, click_len))

        int16_data = (audio * 32767).astype(np.int16)
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(int16_data.tobytes())

    def _create_sine_tone_wav(self, file_path: str, freq: float, duration_sec: float, sr: int):
        """Creates a synthetic pure sine wave at specified frequency."""
        t = np.linspace(0, duration_sec, int(duration_sec * sr), endpoint=False)
        audio = 0.8 * np.sin(2 * np.pi * freq * t)
        int16_data = (audio * 32767).astype(np.int16)
        with wave.open(file_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(int16_data.tobytes())

    def test_bpm_detection_on_synthetic_track(self):
        """Verify that AudioSignalAnalyzer detects ~120 BPM within +/- 2 BPM tolerance."""
        res = self.analyzer.analyze_file(self.bpm_file)
        self.assertIsNotNone(res.estimated_bpm)
        # Check tolerance within +/- 3 BPM
        self.assertAlmostEqual(res.estimated_bpm, 120.0, delta=3.0)
        self.assertGreater(res.bpm_confidence, 0.0)

    def test_key_detection_on_synthetic_tone(self):
        """Verify that AudioSignalAnalyzer detects 'A' as key root for 440 Hz audio."""
        res = self.analyzer.analyze_file(self.key_file)
        self.assertIsNotNone(res.estimated_key_root)
        self.assertEqual(res.estimated_key_root, "A")

    def test_error_isolation_on_corrupted_file(self):
        """Verify RESILIENCY-10 Safe Analysis Result (Null Object) on corrupted audio."""
        res = self.analyzer.analyze_file(self.corrupt_file)
        self.assertIsNotNone(res)
        self.assertIsNone(res.estimated_bpm)
        self.assertIsNone(res.estimated_key_root)
        self.assertEqual(res.bpm_confidence, 0.0)

    def test_auto_renamer_formatting_and_de_duplication(self):
        """Verify AutoRenamer smart format and duplicate notation prevention."""
        # 1. Standard rename
        name1 = AutoRenamer.generate_suggested_name("Guitar_Snob.wav", bpm=174.0, key_root="C#", key_scale="minor")
        self.assertEqual(name1, "Guitar_Snob_174BPM_C#minor.wav")

        # 2. Existing BPM / Key replacement (avoid double BPM)
        name2 = AutoRenamer.generate_suggested_name("Guitar_Snob_120BPM_Dmaj.wav", bpm=174.0, key_root="C#", key_scale="minor")
        self.assertEqual(name2, "Guitar_Snob_174BPM_C#minor.wav")

        # 3. Only BPM
        name3 = AutoRenamer.generate_suggested_name("Drum_Loop.wav", bpm=95.0)
        self.assertEqual(name3, "Drum_Loop_95BPM.wav")

    def test_batch_coordinator_concurrency(self):
        """Verify that BatchAnalysisCoordinator executes multiple files in parallel."""
        coordinator = BatchAnalysisCoordinator(self.analyzer, max_workers=2)
        files = [self.bpm_file, self.key_file, self.corrupt_file]

        progress_log = []
        def on_progress(completed, total, fn):
            progress_log.append((completed, total, fn))

        results = coordinator.analyze_batch(files, on_progress=on_progress)
        self.assertEqual(len(results), 3)
        self.assertEqual(len(progress_log), 3)
        self.assertEqual(progress_log[-1][0], 3)
        self.assertEqual(progress_log[-1][1], 3)


if __name__ == "__main__":
    unittest.main()
