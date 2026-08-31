"""Library file manager for managed folder hierarchy, routing, duplicate numbering, and safe deletion."""
import hashlib
import os
import shutil
from pathlib import Path
from typing import List, Tuple, Optional

from src.core.config import LibraryConfig
from src.core.models import SampleItem


class LibraryFileManager:
    """Manages the structured file system hierarchy (Library/Loop, Library/Oneshot, Library/Other)."""

    def __init__(self, config: LibraryConfig):
        self.config = config
        self.setup_library_hierarchy()

    def setup_library_hierarchy(self) -> None:
        """Creates the standard directory tree under library_root."""
        dirs_to_create = [
            self.config.database_dir,
            self.config.backup_dir,
            self.config.imports_dir,
            self.config.library_dir / "Loop",
            self.config.library_dir / "Loop" / "Other",
            self.config.library_dir / "Oneshot",
            self.config.library_dir / "Oneshot" / "Other",
            self.config.library_dir / "Other",
        ]
        for d in dirs_to_create:
            d.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculates SHA-256 hash of a file for fingerprinting and duplicate detection."""
        p = Path(file_path)
        if not p.exists():
            return ""
        sha256 = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def determine_target_directory(self, sample_type: str, genre: str, instrument: str) -> Path:
        """Determines the target subdirectory in the structured library based on metadata."""
        type_clean = (sample_type or "Oneshot").strip()
        genre_clean = (genre or "Other").strip()
        inst_clean = (instrument or "Other").strip()

        if type_clean == "Loop":
            if genre_clean != "Other" and inst_clean != "Other":
                target_dir = self.config.library_dir / "Loop" / genre_clean / inst_clean
            elif genre_clean != "Other":
                target_dir = self.config.library_dir / "Loop" / genre_clean / "Other"
            else:
                target_dir = self.config.library_dir / "Loop" / "Other"
        else:
            # Oneshot category
            if inst_clean != "Other":
                target_dir = self.config.library_dir / "Oneshot" / inst_clean
            else:
                target_dir = self.config.library_dir / "Oneshot" / "Other"

        return target_dir

    def resolve_unique_target_path(self, target_dir: Path, original_filename: str) -> Tuple[Path, str]:
        """Resolves duplicate file names by appending incrementing sequential numbers (_1, _2...).
        
        Returns:
            Tuple[Path, str]: (Unique full target Path, unique file name)
        """
        target_dir.mkdir(parents=True, exist_ok=True)
        p = Path(original_filename)
        stem = p.stem
        suffix = p.suffix

        candidate_name = original_filename
        candidate_path = target_dir / candidate_name
        counter = 1

        while candidate_path.exists():
            candidate_name = f"{stem}_{counter}{suffix}"
            candidate_path = target_dir / candidate_name
            counter += 1

        return candidate_path, candidate_name

    def import_single_file(
        self,
        src_path: str,
        sample_type: str = "Other",
        genre: str = "Other",
        instrument: str = "Other",
        move: Optional[bool] = None,
        overwrite: bool = True,
    ) -> Tuple[str, str, int, str]:
        """Copies or moves a single audio file to its structured location in the managed library.
        
        Args:
            src_path: Source file path.
            sample_type: "Loop" | "Oneshot" | "Other"
            genre: Genre / Pack name
            instrument: Instrument name
            move: If True, moves the file; if False, copies; if None, uses config.copy_mode.
            overwrite: If True (default), overwrites existing target file. If False, appends sequential numbering.
            
        Returns:
            Tuple[str, str, int, str]: (Final target absolute path, final filename, file size, SHA256 hash)
        """
        src = Path(src_path).resolve()
        if not src.exists():
            raise FileNotFoundError(f"Source file does not exist: {src_path}")

        target_dir = self.determine_target_directory(sample_type, genre, instrument)
        target_dir.mkdir(parents=True, exist_ok=True)

        if overwrite:
            target_path = target_dir / src.name
            final_filename = src.name
        else:
            target_path, final_filename = self.resolve_unique_target_path(target_dir, src.name)

        should_move = (self.config.copy_mode == "move") if move is None else move

        if src.resolve() != target_path.resolve():
            if should_move:
                shutil.move(str(src), str(target_path))
            else:
                shutil.copy2(str(src), str(target_path))

        file_size = target_path.stat().st_size
        file_hash = self.calculate_file_hash(str(target_path))

        return str(target_path.resolve()), final_filename, file_size, file_hash

    def consolidate_file_group(
        self,
        canonical_target_path: str,
        all_duplicate_paths: List[str],
        latest_file_path: str,
    ) -> str:
        """Consolidates a group of duplicate files into a single canonical target file.
        
        Moves/replaces the canonical target with the latest file's content, and sends all
        redundant duplicate files safely to the Windows Recycle Bin.
        
        Returns:
            str: Resolved absolute canonical path.
        """
        canon_p = Path(canonical_target_path).resolve()
        latest_p = Path(latest_file_path).resolve()

        # If the latest file is a numbered duplicate (e.g. sample_2.wav), copy/move it to canonical (sample.wav)
        if latest_p.exists() and latest_p != canon_p:
            shutil.copy2(str(latest_p), str(canon_p))

        # Delete all other obsolete duplicate files
        for fp in all_duplicate_paths:
            p = Path(fp).resolve()
            if p != canon_p and p.exists():
                self.delete_physical_file(str(p), use_recycle_bin=True)

        return str(canon_p)

    def rename_library_file(self, current_file_path: str, new_filename: str) -> str:
        """Renames a file in the library and returns the new absolute path."""
        current_p = Path(current_file_path).resolve()
        if not current_p.exists():
            raise FileNotFoundError(f"File to rename not found: {current_file_path}")

        target_p, _ = self.resolve_unique_target_path(current_p.parent, new_filename)
        current_p.rename(target_p)
        return str(target_p.resolve())

    def relocate_library_file(
        self,
        current_file_path: str,
        new_sample_type: str,
        new_genre: str,
        new_instrument: str,
        new_filename: Optional[str] = None
    ) -> Tuple[str, str]:
        """Moves an existing library file to a new category directory."""
        current_p = Path(current_file_path).resolve()
        if not current_p.exists():
            raise FileNotFoundError(f"File not found: {current_file_path}")

        target_dir = self.determine_target_directory(new_sample_type, new_genre, new_instrument)
        filename = new_filename if new_filename else current_p.name
        target_p, final_name = self.resolve_unique_target_path(target_dir, filename)

        shutil.move(str(current_p), str(target_p))
        return str(target_p.resolve()), final_name

    def delete_physical_file(self, file_path: str, use_recycle_bin: bool = True) -> bool:
        """Deletes a physical audio file, safely sending it to the Windows Recycle Bin if available."""
        p = Path(file_path).resolve()
        if not p.exists():
            return False

        if use_recycle_bin:
            try:
                import send2trash
                send2trash.send2trash(str(p))
                return True
            except ImportError:
                # Fallback to direct deletion if send2trash is not installed
                p.unlink()
                return True
            except Exception:
                p.unlink()
                return True
        else:
            p.unlink()
            return True

    def cleanup_batch_files(self, file_paths: List[str]) -> None:
        """Cleans up a list of files during rollback of a failed batch operation."""
        for fp in file_paths:
            try:
                p = Path(fp)
                if p.exists():
                    p.unlink()
            except OSError:
                pass
