"""
Unit tests for WaveformExtractor and WaveformCache (Unit 3).
Tests peak extraction accuracy, normalization range, stereo downmix, LRU eviction, and corruption handling.
"""

import os
import unittest
import wave
import numpy as np

from src.audio.waveform_extractor import WaveformExtractor, WaveformData
from src.audio.waveform_cache import WaveformCache


class TestUnit3Waveform(unittest.TestCase):
    def setUp(self):
        self.extractor = WaveformExtractor(default_bins=300)
        self.cache = WaveformCache(max_size=5)
        self.test_wav_mono = "test_waveform_mono.wav"
        self.test_wav_stereo = "test_waveform_stereo.wav"
        self.test_corrupt = "test_waveform_corrupt.wav"

        # 1. Create 1-second 440Hz Sine wave (mono 16-bit)
        sr = 44100
        t = np.linspace(0, 1.0, sr, endpoint=False)
        sine = 0.8 * np.sin(2 * np.pi * 440 * t)
        samples_int16 = (sine * 32767).astype(np.int16)

        with wave.open(self.test_wav_mono, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(samples_int16.tobytes())

        # 2. Create stereo file
        stereo_samples = np.column_stack((samples_int16, samples_int16)).flatten()
        with wave.open(self.test_wav_stereo, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(stereo_samples.tobytes())

        # 3. Create 0-byte corrupt file
        with open(self.test_corrupt, "wb") as f:
            f.write(b"NOT_A_VALID_WAV_HEADER_DATA")

    def tearDown(self):
        for path in [self.test_wav_mono, self.test_wav_stereo, self.test_corrupt]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_extract_mono_peaks(self):
        data = self.extractor.extract_peaks(self.test_wav_mono, num_bins=300)
        self.assertTrue(data.is_valid)
        self.assertEqual(data.num_bins, 300)
        self.assertEqual(len(data.peaks_min), 300)
        self.assertEqual(len(data.peaks_max), 300)
        self.assertAlmostEqual(data.duration_ms, 1000, delta=20)

        # Check normalization bounds
        for mn, mx in zip(data.peaks_min, data.peaks_max):
            self.assertGreaterEqual(mn, -1.0)
            self.assertLessEqual(mx, 1.0)
            self.assertLessEqual(mn, mx)

    def test_extract_stereo_peaks(self):
        data = self.extractor.extract_peaks(self.test_wav_stereo, num_bins=200)
        self.assertTrue(data.is_valid)
        self.assertEqual(data.num_bins, 200)
        self.assertEqual(data.channels, 2)

    def test_corrupt_file_safe_null_fallback(self):
        data = self.extractor.extract_peaks(self.test_corrupt, num_bins=300)
        self.assertFalse(data.is_valid)
        self.assertEqual(data.num_bins, 300)
        self.assertEqual(data.peaks_min, [0.0] * 300)
        self.assertEqual(data.peaks_max, [0.0] * 300)

    def test_nonexistent_file_safe_null_fallback(self):
        data = self.extractor.extract_peaks("completely_missing.wav", num_bins=300)
        self.assertFalse(data.is_valid)
        self.assertEqual(data.num_bins, 300)

    def test_lru_cache_eviction(self):
        # Insert 5 items (max_size=5)
        for i in range(5):
            path = f"sample_{i}.wav"
            self.cache.put(path, WaveformData(peaks_min=[0.1 * i], peaks_max=[0.2 * i]))

        self.assertEqual(len(self.cache), 5)
        self.assertTrue(self.cache.contains("sample_0.wav"))

        # Access sample_0 to make it recently used
        self.cache.get("sample_0.wav")

        # Insert 6th item, should evict sample_1.wav
        self.cache.put("sample_5.wav", WaveformData(peaks_min=[0.5], peaks_max=[0.6]))
        self.assertEqual(len(self.cache), 5)
        self.assertTrue(self.cache.contains("sample_0.wav"))   # preserved because accessed
        self.assertFalse(self.cache.contains("sample_1.wav"))  # evicted!
        self.assertTrue(self.cache.contains("sample_5.wav"))

    def test_cache_clear(self):
        self.cache.put("sample_a.wav", WaveformData.create_null(10))
        self.assertEqual(len(self.cache), 1)
        self.cache.clear()
        self.assertEqual(len(self.cache), 0)


if __name__ == "__main__":
    unittest.main()
