"""Filename and metadata parser for Sound Sample Manager."""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple


@dataclass
class ParsedMetadata:
    """Represents metadata extracted from sound file name and path."""
    sample_type: str = "Oneshot"  # "Loop" | "Oneshot" (No 'Other')
    instrument: str = "Other"   # e.g. "guitar", "guitar, bass", "Other"
    instruments: List[str] = field(default_factory=list)  # List of detected instruments
    genre: str = "Other"        # e.g. "SS_Guitar_Snob", "Other"
    bpm: Optional[float] = None
    key_root: Optional[str] = None   # e.g. "C#", "D"
    key_scale: Optional[str] = None  # "minor" | "major" | None
    creator: str = "Other"      # e.g. "BANDLAB", "HEAVEE", "Other"
    raw_tokens: List[str] = field(default_factory=list)


class FilenameParser:
    """High-speed regular expression and rule-based sound file metadata parser."""

    # Map flat accidentals and unicode signs to standard sharp representation
    FLAT_TO_SHARP = {
        "DB": "C#", "Db": "C#", "D♭": "C#",
        "EB": "D#", "Eb": "D#", "E♭": "D#",
        "GB": "F#", "Gb": "F#", "G♭": "F#",
        "AB": "G#", "Ab": "G#", "A♭": "G#",
        "BB": "A#", "Bb": "A#", "B♭": "A#",
        "C#": "C#", "D#": "D#", "F#": "F#", "G#": "G#", "A#": "A#",
        "C": "C", "D": "D", "E": "E", "F": "F", "G": "G", "A": "A", "B": "B",
        "C♯": "C#", "D♯": "D#", "F♯": "F#", "G♯": "G#", "A♯": "A#",
    }

    # Known instruments dictionary
    KNOWN_INSTRUMENTS = {
        "beat": "beats",
        "beats": "beats",
        "guitar": "guitar",
        "acoustic_guitar": "guitar",
        "electric_guitar": "guitar",
        "bass": "bass",
        "808": "808",
        "808s": "808",
        "sub": "bass",
        "synth": "synth",
        "pad": "pad",
        "lead": "lead",
        "pluck": "synth",
        "keys": "keys",
        "piano": "piano",
        "rhodes": "piano",
        "organ": "keys",
        "kick": "kick",
        "snare": "snare",
        "clap": "clap",
        "rim": "snare",
        "hihat": "hihat",
        "hat": "hihat",
        "openhat": "hihat",
        "closedhat": "hihat",
        "cymbal": "cymbal",
        "ride": "cymbal",
        "crash": "cymbal",
        "drum": "drums",
        "drums": "drums",
        "percussion": "percussion",
        "perc": "percussion",
        "tom": "drums",
        "vocal": "vocal",
        "vox": "vocal",
        "acapella": "vocal",
        "fx": "fx",
        "sfx": "fx",
        "flute": "flute",
        "brass": "brass",
        "horn": "brass",
        "strings": "strings",
        "violin": "strings",
    }

    # Known creators / sound labels
    KNOWN_CREATORS = {
        "BANDLAB": "BANDLAB",
        "HEAVEE": "HEAVEE",
        "SOUNDS": "SOUNDS",
        "CYMATICS": "CYMATICS",
        "SPLICE": "SPLICE",
        "LOOPMASTERS": "LOOPMASTERS",
    }

    # Compiled regex patterns for performance (<50ms per 1,000 files)
    RE_BPM_EXPLICIT = re.compile(r'(?i)(?:^|[_ -])(\d{2,3}(?:\.\d+)?)\s*bpm(?:[_ -]|$)')
    RE_KEY_EXPLICIT = re.compile(r'(?i)(?:^|[_ -])([A-G](?:[#♯]|b|♭)?)\s*(minor|major|min|maj|m)?(?:[_ -]|$)')
    RE_TYPE_LOOP = re.compile(r'(?i)(?:^|[_ -])(loop|loops)(?:[_ -]|$)')
    RE_TYPE_ONESHOT = re.compile(r'(?i)(?:^|[_ -])(oneshot|one-shot|shot|shots|hit|hits)(?:[_ -]|$)')

    @classmethod
    def normalize_key(cls, raw_key_string: str) -> Tuple[Optional[str], Optional[str]]:
        """Normalizes raw key string into standard sharp root and scale."""
        if not raw_key_string or not raw_key_string.strip():
            return None, None

        cleaned = raw_key_string.strip()
        match = cls.RE_KEY_EXPLICIT.search(cleaned)
        if not match:
            return None, None

        root_raw = match.group(1)
        scale_raw = match.group(2)

        key_root = cls.FLAT_TO_SHARP.get(root_raw, None)
        if not key_root:
            key_root = cls.FLAT_TO_SHARP.get(root_raw.upper(), None)

        if not key_root:
            return None, None

        # Standardize scale
        if scale_raw:
            s_lower = scale_raw.lower()
            if s_lower in ("m", "min", "minor"):
                key_scale = "minor"
            elif s_lower in ("maj", "major"):
                key_scale = "major"
            else:
                key_scale = "major"
        else:
            key_scale = "minor" if cleaned.endswith("m") and len(cleaned) > 1 else "major"

        return key_root, key_scale

    @classmethod
    def parse_filename(
        cls,
        file_path_or_name: str,
        default_pack: Optional[str] = None,
    ) -> ParsedMetadata:
        """Parses a sound sample file path or file name into a structured ParsedMetadata entity."""
        if not file_path_or_name or not isinstance(file_path_or_name, str):
            return ParsedMetadata()

        p = Path(file_path_or_name)
        stem = p.stem
        parent_name = p.parent.name if p.parent else ""

        # Tokenize by underscores, hyphens, and whitespace
        tokens = [t.strip() for t in re.split(r'[_ -]+', stem) if t.strip()]

        result = ParsedMetadata(raw_tokens=tokens)

        # 1. Extract BPM
        bpm_match = cls.RE_BPM_EXPLICIT.search(stem)
        if bpm_match:
            try:
                bpm_val = float(bpm_match.group(1))
                if 40.0 <= bpm_val <= 300.0:
                    result.bpm = bpm_val
            except ValueError:
                pass
        else:
            # Check isolated number tokens
            for token in tokens:
                try:
                    num = float(token)
                    if 50.0 <= num <= 250.0:
                        result.bpm = num
                        break
                except (ValueError, TypeError):
                    pass

        # 2. Determine Type (Strictly 'Loop' or 'Oneshot')
        token_lowers = [t.lower() for t in tokens]
        if any(t in ("loop", "loops") for t in token_lowers) or cls.RE_TYPE_LOOP.search(parent_name) or cls.RE_TYPE_LOOP.search(stem):
            result.sample_type = "Loop"
        elif any(t in ("oneshot", "one-shot", "shot", "shots", "hit", "hits") for t in token_lowers) or cls.RE_TYPE_ONESHOT.search(parent_name) or cls.RE_TYPE_ONESHOT.search(stem):
            result.sample_type = "Oneshot"
        elif result.bpm is not None:
            # If no explicit keyword but BPM is present, default to Loop
            result.sample_type = "Loop"
        else:
            # Otherwise default to Oneshot
            result.sample_type = "Oneshot"

        # 3. Extract Key
        for token in reversed(tokens):
            if cls.RE_KEY_EXPLICIT.match(token) and not token.isdigit() and token.upper() not in cls.KNOWN_CREATORS:
                k_root, k_scale = cls.normalize_key(token)
                if k_root:
                    result.key_root = k_root
                    result.key_scale = k_scale
                    break

        if result.key_root is None:
            key_match = cls.RE_KEY_EXPLICIT.search(stem)
            if key_match:
                k_root, k_scale = cls.normalize_key(key_match.group(0))
                if k_root:
                    result.key_root = k_root
                    result.key_scale = k_scale

        # 4. Extract Instruments (Collect all unique matching instruments)
        detected_instruments = []
        for token in tokens:
            t_lower = token.lower()
            if t_lower in cls.KNOWN_INSTRUMENTS:
                mapped = cls.KNOWN_INSTRUMENTS[t_lower]
                if mapped not in detected_instruments:
                    detected_instruments.append(mapped)

        if not detected_instruments:
            stem_lower = stem.lower()
            for key_inst, mapped_inst in cls.KNOWN_INSTRUMENTS.items():
                if re.search(rf'(?:^|[_ -]){re.escape(key_inst)}(?:[_ -]|$)', stem_lower):
                    if mapped_inst not in detected_instruments:
                        detected_instruments.append(mapped_inst)

        if detected_instruments:
            result.instruments = detected_instruments
            result.instrument = ", ".join(detected_instruments)
        else:
            result.instruments = []
            result.instrument = "Other"

        # 5. Extract Creator (Check from end of tokens first for trailing label tags like _BANDLAB)
        for token in reversed(tokens):
            token_upper = token.upper()
            if token_upper in cls.KNOWN_CREATORS:
                result.creator = cls.KNOWN_CREATORS[token_upper]
                break

        # 6. Assign Pack / Creator strictly from the top-level parent folder name
        if default_pack and default_pack.strip():
            clean_dp = default_pack.strip()
            if clean_dp not in ("Loop", "Oneshot", "Other"):
                result.genre = clean_dp
                # If creator is still Other, check if parent folder name contains known creators
                if result.creator == "Other":
                    dp_upper = clean_dp.upper()
                    for creator_key, creator_val in cls.KNOWN_CREATORS.items():
                        if creator_key in dp_upper:
                            result.creator = creator_val
                            break
            else:
                result.genre = "Other"
        else:
            # Single file or no parent pack folder -> strictly Other
            result.genre = "Other"

        return result
