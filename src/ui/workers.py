"""Non-blocking background QThread worker tasks for file import, scanning, and DSP analysis."""
import os
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import QThread, pyqtSignal

from src.core.models import SampleItem, ImportSummary
from src.parser.filename_parser import FilenameParser
from src.database.repository import SampleRepository
from src.storage.file_manager import LibraryFileManager
from src.analyzer.batch_coordinator import BatchAnalysisCoordinator
from src.analyzer.audio_analyzer import AudioAnalysisResult


class ImportWorker(QThread):
    """Background worker for batch importing sound samples into the library."""

    progress = pyqtSignal(int, int, str)       # current, total, filename
    finished = pyqtSignal(ImportSummary)       # summary stats
    error = pyqtSignal(str)                   # error message

    SUPPORTED_EXTS = {".wav", ".mp3", ".ogg", ".flac", ".aif", ".aiff"}

    def __init__(
        self,
        source_folder: str,
        repo: SampleRepository,
        file_mgr: LibraryFileManager,
        parser: Optional[FilenameParser] = None,
        copy_mode: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self.source_folder = source_folder
        self.repo = repo
        self.file_mgr = file_mgr
        self.parser = parser or FilenameParser()
        self.copy_mode = copy_mode
        self._is_cancelled = False

    def cancel(self):
        """Requests cancellation of import process."""
        self._is_cancelled = True

    def run(self):
        summary = ImportSummary()
        src_path = Path(self.source_folder)
        if not src_path.exists():
            self.error.emit(f"Source folder does not exist: {self.source_folder}")
            return

        # 1. Discover audio files
        audio_files: List[Path] = []
        for root, _, files in os.walk(src_path):
            if self._is_cancelled:
                break
            for f in files:
                p = Path(root) / f
                if p.suffix.lower() in self.SUPPORTED_EXTS:
                    audio_files.append(p)

        summary.total_files_scanned = len(audio_files)
        if summary.total_files_scanned == 0:
            self.finished.emit(summary)
            return

        imported_records: List[SampleItem] = []

        pack_name = src_path.name

        # 2. Process and import each file
        for idx, file_p in enumerate(audio_files, start=1):
            if self._is_cancelled:
                break

            self.progress.emit(idx, summary.total_files_scanned, file_p.name)

            try:
                # Parse metadata from filename with folder name fallback
                parsed = self.parser.parse_filename(file_p.name, default_pack=pack_name)

                # Copy/Move file to managed hierarchy with overwrite mode
                final_path, final_name, file_size, file_hash = self.file_mgr.import_single_file(
                    src_path=str(file_p),
                    sample_type=parsed.sample_type,
                    genre=parsed.genre,
                    instrument=parsed.instrument,
                    move=not self.copy_mode,
                    overwrite=True,
                )

                if parsed.sample_type == "Other" or parsed.instrument == "Other":
                    summary.other_classified_count += 1

                # Construct SampleItem
                item = SampleItem(
                    file_path=final_path,
                    file_name=final_name,
                    file_size=file_size,
                    file_hash=file_hash,
                    sample_type=parsed.sample_type,
                    instrument=parsed.instrument,
                    genre=parsed.genre,
                    bpm=parsed.bpm,
                    key_root=parsed.key_root,
                    key_scale=parsed.key_scale,
                    creator=parsed.creator,
                    duration_sec=0.0,
                    sample_rate=44100,
                    channels=2,
                    bit_depth=16,
                    format=file_p.suffix.upper().replace(".", ""),
                )
                imported_records.append(item)
                summary.imported_count += 1

            except Exception as e:
                summary.errors_count += 1
                summary.error_details.append(f"{file_p.name}: {str(e)}")

        # Batch upsert into repository
        if imported_records:
            try:
                self.repo.upsert_samples_batch(imported_records)
            except Exception as e:
                self.error.emit(f"Failed to commit imported samples to database: {str(e)}")
                return

        self.finished.emit(summary)


class ConsolidateDuplicatesWorker(QThread):
    """Background worker for detecting duplicate files and consolidating them to the latest file."""

    progress = pyqtSignal(int, int, str)       # current, total, description
    finished = pyqtSignal(int, int)            # groups_consolidated, files_cleaned
    error = pyqtSignal(str)

    def __init__(self, repo: SampleRepository, file_mgr: LibraryFileManager, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.file_mgr = file_mgr
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            duplicate_groups = self.repo.find_duplicate_groups()
            total_groups = len(duplicate_groups)

            if total_groups == 0:
                self.finished.emit(0, 0)
                return

            consolidated_count = 0
            files_cleaned_count = 0

            for idx, group in enumerate(duplicate_groups, start=1):
                if self._is_cancelled:
                    break

                canonical_name = group["canonical_name"]
                self.progress.emit(idx, total_groups, f"Consolidating: {canonical_name}")

                canonical_path = group["canonical_path"]
                all_paths = [s.file_path for s in group["all_samples"]]
                latest_sample = group["latest_sample"]

                # 1. Consolidate physical files
                resolved_canon_path = self.file_mgr.consolidate_file_group(
                    canonical_target_path=canonical_path,
                    all_duplicate_paths=all_paths,
                    latest_file_path=latest_sample.file_path,
                )

                # 2. Update DB: Delete obsolete records
                obsolete_ids = [s.id for s in group["obsolete_samples"] if s.id]
                if obsolete_ids:
                    self.repo.delete_samples_batch(obsolete_ids)
                    files_cleaned_count += len(obsolete_ids)

                # 3. Update the kept record to canonical name/path & latest stats
                latest_sample.file_path = resolved_canon_path
                latest_sample.file_name = canonical_name
                p = Path(resolved_canon_path)
                if p.exists():
                    latest_sample.file_size = p.stat().st_size
                    latest_sample.file_hash = self.file_mgr.calculate_file_hash(resolved_canon_path)

                if latest_sample.id:
                    self.repo.update_sample(latest_sample)
                else:
                    self.repo.upsert_sample(latest_sample)
                consolidated_count += 1

            self.finished.emit(consolidated_count, files_cleaned_count)

        except Exception as e:
            self.error.emit(f"Error during duplicate consolidation: {str(e)}")


class BatchAnalyzeWorker(QThread):
    """Background worker for batch DSP signal analysis (BPM & Key detection)."""

    progress = pyqtSignal(int, int, str)       # current, total, filename
    finished = pyqtSignal(list)                # List[AudioAnalysisResult]
    error = pyqtSignal(str)

    def __init__(self, file_paths: List[str], coordinator: Optional[BatchAnalysisCoordinator] = None, parent=None):
        super().__init__(parent)
        self.file_paths = file_paths
        self.coordinator = coordinator or BatchAnalysisCoordinator()
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            results = self.coordinator.analyze_batch(
                file_paths=self.file_paths,
                on_progress=lambda cur, tot, name: self.progress.emit(cur, tot, name),
            )
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(f"Error during audio signal analysis: {str(e)}")


class RescanWorker(QThread):
    """Background worker for synchronizing the database with library folder changes."""

    progress = pyqtSignal(int, int, str)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, repo: SampleRepository, file_mgr: LibraryFileManager, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.file_mgr = file_mgr
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            samples = self.repo.get_all_samples()
            synced = 0
            for idx, s in enumerate(samples, start=1):
                if self._is_cancelled:
                    break
                self.progress.emit(idx, len(samples), s.file_name)
                # Check if physical file was deleted outside the app
                if not os.path.exists(s.file_path) and s.id:
                    self.repo.delete_sample_by_id(s.id)
                    synced += 1
            self.finished.emit(synced)
        except Exception as e:
            self.error.emit(f"Rescan failed: {str(e)}")
