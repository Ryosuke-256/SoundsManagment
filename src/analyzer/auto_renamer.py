"""Auto-renamer for generating standardized filenames based on audio analysis results."""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Tuple

from src.analyzer.audio_analyzer import AudioAnalysisResult
from src.core.models import SampleItem


@dataclass
class RenamePreviewItem:
    """Preview item for UI confirmation before applying rename."""
    sample_id: int
    current_path: str
    current_name: str
    new_name: str
    detected_bpm: Optional[float]
    detected_key: Optional[str]
    is_approved: bool = True


class AutoRenamer:
    """Generates standardized sample filenames following the pattern [Base]_[BPM]BPM_[Key].[ext]."""

    # Patterns to match existing trailing BPM or Key notations to prevent duplication
    RE_EXISTING_BPM = re.compile(r'(?i)[_ -](\d{2,3}(?:\.\d+)?)\s*bpm')
    RE_EXISTING_KEY = re.compile(r'(?i)[_ -]([A-Ga-g][#b♯♭]?(?:minor|major|min|maj|m)?)')

    @classmethod
    def clean_base_name(cls, filename_stem: str) -> str:
        """Strips existing trailing BPM and Key tokens from the base filename."""
        cleaned = filename_stem
        # Remove trailing BPM
        cleaned = cls.RE_EXISTING_BPM.sub("", cleaned)
        # Remove trailing Key
        cleaned = cls.RE_EXISTING_KEY.sub("", cleaned)
        # Clean consecutive trailing underscores/spaces
        cleaned = re.sub(r'[_ -]+$', '', cleaned)
        cleaned = re.sub(r'^[_ -]+', '', cleaned)
        return cleaned if cleaned else filename_stem

    @classmethod
    def generate_suggested_name(
        cls,
        original_filename: str,
        bpm: Optional[float] = None,
        key_root: Optional[str] = None,
        key_scale: Optional[str] = None,
    ) -> str:
        """Generates a standardized filename appending estimated BPM and Key.
        
        Examples:
            "Kick_Sample.wav" (BPM=120, Key=C major) -> "Kick_Sample_120BPM_Cmajor.wav"
            "Guitar_Loop_120BPM.wav" (BPM=174, Key=C# minor) -> "Guitar_Loop_174BPM_C#minor.wav"
        """
        p = Path(original_filename)
        ext = p.suffix
        clean_stem = cls.clean_base_name(p.stem)

        parts = [clean_stem]

        if bpm is not None:
            bpm_rounded = int(round(bpm))
            parts.append(f"{bpm_rounded}BPM")

        if key_root:
            scale_str = key_scale if key_scale else "major"
            parts.append(f"{key_root}{scale_str}")

        return f"{'_'.join(parts)}{ext}"

    @classmethod
    def create_rename_previews(
        cls,
        samples: List[SampleItem],
        analysis_results: List[AudioAnalysisResult],
    ) -> List[RenamePreviewItem]:
        """Creates rename preview list matching sample records with analysis results."""
        results_by_path = {r.file_path: r for r in analysis_results}
        previews = []

        for sample in samples:
            res = results_by_path.get(sample.file_path)
            if not res:
                continue

            bpm = res.estimated_bpm or sample.bpm
            key_root = res.estimated_key_root or sample.key_root
            key_scale = res.estimated_key_scale or sample.key_scale

            new_name = cls.generate_suggested_name(
                original_filename=sample.file_name,
                bpm=bpm,
                key_root=key_root,
                key_scale=key_scale,
            )

            key_str = f"{key_root} {key_scale}" if key_root else None

            previews.append(RenamePreviewItem(
                sample_id=sample.id or 0,
                current_path=sample.file_path,
                current_name=sample.file_name,
                new_name=new_name,
                detected_bpm=bpm,
                detected_key=key_str,
                is_approved=True,
            ))

        return previews
