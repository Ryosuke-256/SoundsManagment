"""
Property-based tests for Unit 3 (Audio Engine & Waveform Visualizer) using Hypothesis.
Validates waveform peak bounds, bin counts, and seek clamping invariants (PBT-04).
"""

import os
import sys
import wave
from hypothesis import given, settings, strategies as st
import numpy as np
from PyQt6.QtCore import QCoreApplication

from src.audio.waveform_extractor import WaveformExtractor, WaveformData
from src.audio.player_service import AudioPlayerService


class TestUnit3PropertyBased:
    @classmethod
    def setup_class(cls):
        if QCoreApplication.instance() is None:
            cls.app = QCoreApplication(sys.argv)
        else:
            cls.app = QCoreApplication.instance()

    @settings(max_examples=30, deadline=1000)
    @given(
        duration_s=st.floats(min_value=0.05, max_value=2.0),
        freq=st.floats(min_value=50.0, max_value=2000.0),
        amplitude=st.floats(min_value=0.0, max_value=1.0),
        num_bins=st.integers(min_value=10, max_value=400),
    )
    def test_waveform_peak_invariants(self, duration_s: float, freq: float, amplitude: float, num_bins: int):
        """
        PBT-04: Validates that for any valid synthesized audio:
        1. Peak arrays have length exactly equal to num_bins.
        2. All peak values are within [-1.0, 1.0].
        3. peaks_min[i] <= peaks_max[i] for all bins.
        """
        temp_wav = f"temp_pbt_{num_bins}.wav"
        sr = 44100
        n_samples = int(duration_s * sr)
        t = np.linspace(0, duration_s, n_samples, endpoint=False)
        audio = amplitude * np.sin(2 * np.pi * freq * t)
        samples_int16 = (audio * 32767).astype(np.int16)

        try:
            with wave.open(temp_wav, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sr)
                wf.writeframes(samples_int16.tobytes())

            extractor = WaveformExtractor()
            data = extractor.extract_peaks(temp_wav, num_bins=num_bins)

            assert data.is_valid is True
            assert len(data.peaks_min) == num_bins
            assert len(data.peaks_max) == num_bins

            for mn, mx in zip(data.peaks_min, data.peaks_max):
                assert -1.0 <= mn <= 1.0
                assert -1.0 <= mx <= 1.0
                assert mn <= mx

        finally:
            if os.path.exists(temp_wav):
                try:
                    os.remove(temp_wav)
                except OSError:
                    pass

    @settings(max_examples=50)
    @given(
        duration_ms=st.integers(min_value=0, max_value=300000),
        target_seek_ms=st.integers(min_value=-100000, max_value=500000),
    )
    def test_seek_clamping_invariant(self, duration_ms: int, target_seek_ms: int):
        """
        PBT-04: Validates that seek_ms always clamps position_ms between 0 and duration_ms.
        """
        player = AudioPlayerService(headless=True)
        player._duration_ms = duration_ms
        player.seek_ms(target_seek_ms)

        expected_max = duration_ms if duration_ms > 0 else max(0, target_seek_ms)
        assert 0 <= player.position_ms <= expected_max
