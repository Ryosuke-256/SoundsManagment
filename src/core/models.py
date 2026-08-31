"""Domain entities and data transfer objects for Sound Sample Manager."""
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


def get_current_iso_timestamp() -> str:
    """Returns current UTC ISO 8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class SampleItem:
    """Represents a single sound sample item in the sound library."""
    file_path: str
    file_name: str
    id: Optional[int] = None
    file_size: int = 0
    file_hash: str = ""
    sample_type: str = "Other"  # "Loop" | "Oneshot" | "Other"
    instrument: str = "Other"   # e.g. "guitar", "bass", "kick", "Other"
    genre: str = "Other"        # e.g. "SS_Guitar_Snob", "Other"
    bpm: Optional[float] = None
    key_root: Optional[str] = None   # e.g. "C#", "D"
    key_scale: Optional[str] = None  # "minor" | "major"
    creator: str = "Other"      # e.g. "BANDLAB", "Other"
    duration_sec: float = 0.0
    sample_rate: int = 44100
    channels: int = 2
    bit_depth: int = 16
    format: str = "WAV"
    tags: str = ""
    is_favorite: bool = False
    created_at: str = field(default_factory=get_current_iso_timestamp)
    updated_at: str = field(default_factory=get_current_iso_timestamp)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d["is_favorite"] = 1 if self.is_favorite else 0
        return d

    @classmethod
    def from_row(cls, row: Any) -> "SampleItem":
        """Create SampleItem from a SQLite Row or dict-like object."""
        return cls(
            id=row["id"],
            file_path=row["file_path"],
            file_name=row["file_name"],
            file_size=row["file_size"],
            file_hash=row["file_hash"],
            sample_type=row["sample_type"],
            instrument=row["instrument"],
            genre=row["genre"],
            bpm=row["bpm"],
            key_root=row["key_root"],
            key_scale=row["key_scale"],
            creator=row["creator"],
            duration_sec=row["duration_sec"],
            sample_rate=row["sample_rate"],
            channels=row["channels"],
            bit_depth=row["bit_depth"],
            format=row["format"],
            tags=row["tags"] if row["tags"] is not None else "",
            is_favorite=bool(row["is_favorite"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


    @property
    def instruments(self) -> List[str]:
        """Returns list of individual instrument tags parsed from the instrument field."""
        if not self.instrument or self.instrument == "Other":
            return []
        return [inst.strip() for inst in self.instrument.split(",") if inst.strip()]


@dataclass
class SearchFilter:
    """Filter criteria and sorting specifications for searching sound samples."""
    query_text: Optional[str] = None
    sample_types: List[str] = field(default_factory=list)
    instruments: List[str] = field(default_factory=list)
    genres: List[str] = field(default_factory=list)
    key_roots: List[str] = field(default_factory=list)
    key_scales: List[str] = field(default_factory=list)
    bpm_min: Optional[float] = None
    bpm_max: Optional[float] = None
    creators: List[str] = field(default_factory=list)
    is_favorite_only: bool = False
    only_unclassified_instrument: bool = False
    only_unclassified_genre: bool = False
    only_unknown_key: bool = False
    only_unknown_bpm: bool = False
    sort_column: str = "file_name"
    sort_direction: str = "ASC"  # "ASC" | "DESC"


@dataclass
class ImportSummary:
    """Summary of batch import operation."""
    total_files_scanned: int = 0
    imported_count: int = 0
    duplicate_renamed_count: int = 0
    other_classified_count: int = 0
    errors_count: int = 0
    error_details: List[str] = field(default_factory=list)


@dataclass
class BackupInfo:
    """Metadata of an SQLite snapshot backup."""
    file_path: str
    file_name: str
    file_size: int
    created_time: str
