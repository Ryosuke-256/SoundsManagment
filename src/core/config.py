"""Configuration model and JSON persistence for Sound Sample Manager."""
import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any


@dataclass
class LibraryConfig:
    """Application and sound library configuration."""
    library_root: str = ""
    copy_mode: str = "copy"  # "copy" | "move"
    auto_backup_enabled: bool = True
    max_backup_generations: int = 5
    default_volume: float = 0.8
    auto_play_default: bool = True
    loop_playback_default: bool = True

    def __post_init__(self):
        if not self.library_root:
            # Default to SoundLibrary in current working directory
            self.library_root = str(Path(os.getcwd()) / "SoundLibrary")

    @property
    def database_dir(self) -> Path:
        """Directory for SQLite database."""
        return Path(self.library_root) / "Database"

    @property
    def database_path(self) -> Path:
        """Path to SQLite database file."""
        return self.database_dir / "library.db"

    @property
    def backup_dir(self) -> Path:
        """Directory for database backups."""
        return Path(self.library_root) / "Backups"

    @property
    def library_dir(self) -> Path:
        """Root directory for organized library sound files."""
        return Path(self.library_root) / "Library"

    @property
    def imports_dir(self) -> Path:
        """Directory for staging imports."""
        return Path(self.library_root) / "Imports"

    @classmethod
    def load_from_file(cls, config_path: str) -> "LibraryConfig":
        """Loads configuration from JSON file or returns default if not found."""
        p = Path(config_path)
        if not p.exists():
            return cls()
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            return cls(**data)
        except Exception:
            return cls()

    def save_to_file(self, config_path: str) -> None:
        """Saves configuration to JSON file."""
        p = Path(config_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2, ensure_ascii=False)
