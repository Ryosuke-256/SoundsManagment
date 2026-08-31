"""Unit tests for Unit 2: FilenameParser and metadata extraction."""
import unittest

from src.parser.filename_parser import FilenameParser


class TestUnit2Parser(unittest.TestCase):
    """Test suite for parsing BandLab and general sound sample filenames."""

    def test_bandlab_loop_filename_parsing(self):
        """Verify parsing of BandLab loop file with BPM, Key, genre, instrument, and creator."""
        filename = "03_SS_Guitar_Snob_174_4_bar_Loop_C#_guitar_174BPM_C♯minor_BANDLAB.wav"
        metadata = FilenameParser.parse_filename(filename)

        self.assertEqual(metadata.sample_type, "Loop")
        self.assertEqual(metadata.instrument, "guitar")
        self.assertEqual(metadata.genre, "SS_Guitar_Snob")
        self.assertEqual(metadata.bpm, 174.0)
        self.assertEqual(metadata.key_root, "C#")
        self.assertEqual(metadata.key_scale, "minor")
        self.assertEqual(metadata.creator, "BANDLAB")

    def test_bandlab_oneshot_filename_parsing(self):
        """Verify parsing of BandLab oneshot drum sample."""
        filename = "01_HEAVEE_kick_oneshot_BANDLAB.wav"
        metadata = FilenameParser.parse_filename(filename)

        self.assertEqual(metadata.sample_type, "Oneshot")
        self.assertEqual(metadata.instrument, "kick")
        self.assertEqual(metadata.creator, "BANDLAB")
        self.assertIsNone(metadata.bpm)

    def test_flat_accidental_and_unicode_normalization(self):
        """Verify that flat note accidentals and Unicode signs are converted to standard sharp."""
        k_root1, k_scale1 = FilenameParser.normalize_key("Db minor")
        self.assertEqual(k_root1, "C#")
        self.assertEqual(k_scale1, "minor")

        k_root2, k_scale2 = FilenameParser.normalize_key("Eb maj")
        self.assertEqual(k_root2, "D#")
        self.assertEqual(k_scale2, "major")

        k_root3, k_scale3 = FilenameParser.normalize_key("F♯m")
        self.assertEqual(k_root3, "F#")
        self.assertEqual(k_scale3, "minor")

        k_root4, k_scale4 = FilenameParser.normalize_key("Bb")
        self.assertEqual(k_root4, "A#")
        self.assertEqual(k_scale4, "major")

    def test_unclassified_fallback_to_other_and_default_oneshot(self):
        """Verify that unknown tokens fall back gracefully to 'Other' and type defaults to 'Oneshot' when no BPM."""
        filename = "some_random_audio_clip_recording.wav"
        metadata = FilenameParser.parse_filename(filename)

        self.assertEqual(metadata.sample_type, "Oneshot")
        self.assertEqual(metadata.instrument, "Other")
        self.assertEqual(metadata.genre, "Other")
        self.assertIsNone(metadata.bpm)
        self.assertIsNone(metadata.key_root)
        self.assertEqual(metadata.creator, "Other")

    def test_default_loop_when_bpm_present(self):
        """Verify that a sample without explicit loop/oneshot keyword defaults to 'Loop' if BPM is present."""
        filename = "synth_melody_128bpm_F#m.wav"
        metadata = FilenameParser.parse_filename(filename)

        self.assertEqual(metadata.sample_type, "Loop")
        self.assertEqual(metadata.bpm, 128.0)
        self.assertEqual(metadata.key_root, "F#")
        self.assertEqual(metadata.key_scale, "minor")
        self.assertEqual(metadata.instrument, "synth")

    def test_multi_instrument_parsing(self):
        """Verify that multiple instruments in a single filename are all extracted."""
        filename = "03_guitar_bass_drums_174BPM.wav"
        metadata = FilenameParser.parse_filename(filename)

        self.assertEqual(metadata.instruments, ["guitar", "bass", "drums"])
        self.assertEqual(metadata.instrument, "guitar, bass, drums")
        self.assertEqual(metadata.bpm, 174.0)

    def test_beats_instrument_parsing(self):
        """Verify that 'beat' and 'beats' are classified as 'beats' instrument."""
        fn1 = "hiphop_beat_90bpm.wav"
        meta1 = FilenameParser.parse_filename(fn1)
        self.assertEqual(meta1.instrument, "beats")
        self.assertIn("beats", meta1.instruments)

        fn2 = "trap_beats_140bpm.wav"
        meta2 = FilenameParser.parse_filename(fn2)
        self.assertEqual(meta2.instrument, "beats")
        self.assertIn("beats", meta2.instruments)

    def test_parser_speed_benchmark(self):
        """Verify that parsing 1,000 filenames takes < 50ms."""
        import time
        filenames = [
            f"0{i % 9}_SS_Guitar_Snob_174_4_bar_Loop_C#_guitar_174BPM_C♯minor_BANDLAB_{i}.wav"
            for i in range(1000)
        ]
        start_time = time.perf_counter()
        for fn in filenames:
            FilenameParser.parse_filename(fn)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Performance requirement: 1,000 files < 50ms
        self.assertLess(elapsed_ms, 50.0)


if __name__ == "__main__":
    unittest.main()
