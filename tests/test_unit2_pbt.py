"""Property-Based Tests (PBT) for Unit 2 FilenameParser using Hypothesis (PBT-02/03)."""
import unittest
from hypothesis import given, strategies as st

from src.parser.filename_parser import FilenameParser


class TestUnit2PropertyBased(unittest.TestCase):
    """Property-Based Tests verifying parser robustness and normalization invariants."""

    VALID_KEY_ROOTS = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B", None}
    VALID_TYPES = {"Loop", "Oneshot", "Other"}

    @given(st.text())
    def test_pbt_parser_crash_resilience(self, random_string: str):
        """Invariant 4 (PBT-03): Parser NEVER crashes on arbitrary Unicode/ASCII strings."""
        result = FilenameParser.parse_filename(random_string)
        self.assertIsNotNone(result)
        self.assertIn(result.sample_type, self.VALID_TYPES)

    @given(st.text())
    def test_pbt_key_normalization_invariants(self, raw_key: str):
        """Invariant 2 (PBT-03): Extracted Key is always None or one of 12 standard sharp pitch classes."""
        root, scale = FilenameParser.normalize_key(raw_key)
        self.assertIn(root, self.VALID_KEY_ROOTS)
        if scale is not None:
            self.assertIn(scale, {"minor", "major"})

    @given(
        genre=st.sampled_from(["Rock", "HipHop", "EDM", "Pop", "Trap", "Lofi", "Jazz", "Soul"]),
        bpm=st.integers(min_value=50, max_value=220),
        key_root=st.sampled_from(["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]),
        key_scale=st.sampled_from(["minor", "major"]),
        instrument=st.sampled_from(["guitar", "bass", "kick", "synth", "vocal"]),
        sample_type=st.sampled_from(["Loop", "Oneshot"]),
        creator=st.sampled_from(["BANDLAB", "HEAVEE"])
    )
    def test_pbt_round_trip_structured_filenames(
        self, genre, bpm, key_root, key_scale, instrument, sample_type, creator
    ):
        """Property PBT-02: Structured standard filename attributes are preserved upon parsing."""
        filename = f"{genre}_{bpm}BPM_{key_root}{key_scale}_{instrument}_{sample_type}_{creator}.wav"
        meta = FilenameParser.parse_filename(filename)

        self.assertEqual(meta.sample_type, sample_type)
        self.assertEqual(meta.bpm, float(bpm))
        self.assertEqual(meta.key_root, key_root)
        self.assertEqual(meta.key_scale, key_scale)
        self.assertIn(instrument, meta.instruments)
        self.assertEqual(meta.creator, creator)


if __name__ == "__main__":
    unittest.main()
