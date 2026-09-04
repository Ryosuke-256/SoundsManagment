"""Unit tests for Unit 1: LibraryFileManager and structured storage."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.core.config import LibraryConfig
from src.storage.file_manager import LibraryFileManager


class TestUnit1Storage(unittest.TestCase):
    """Test suite for library file management, folder routing, duplicate resolution, and deletion."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.library_root = str(Path(self.temp_dir) / "TestSoundLibrary")
        self.config = LibraryConfig(library_root=self.library_root, copy_mode="copy")
        self.file_manager = LibraryFileManager(self.config)

        # Create dummy sound files for importing
        self.src_dir = Path(self.temp_dir) / "source_files"
        self.src_dir.mkdir()
        self.sample_file = self.src_dir / "guitar_sample.wav"
        with open(self.sample_file, "wb") as f:
            f.write(b"RIFFdummydataWAVEfmt ")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_hierarchy_creation(self):
        """Verify that library hierarchy directories are automatically initialized."""
        self.assertTrue(self.config.database_dir.exists())
        self.assertTrue(self.config.backup_dir.exists())
        self.assertTrue((self.config.library_dir / "Loop").exists())
        self.assertTrue((self.config.library_dir / "Oneshot").exists())
        self.assertTrue((self.config.library_dir / "Other").exists())

    def test_folder_routing_and_import(self):
        """Verify routing of Loop, Oneshot, and Other sound files into structured folders."""
        # 1. Loop with Genre and Instrument
        dest_path, filename, size, file_hash = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="SS_Guitar_Snob",
            instrument="guitar",
        )
        self.assertTrue(os.path.exists(dest_path))
        self.assertEqual(filename, "guitar_sample.wav")
        self.assertTrue(file_hash != "")
        self.assertIn("Loop", dest_path)
        self.assertIn("SS_Guitar_Snob", dest_path)
        self.assertIn("guitar", dest_path)

        # 2. Oneshot with Instrument
        dest_oneshot, _, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Oneshot",
            instrument="kick",
        )
        self.assertIn("Oneshot", dest_oneshot)
        self.assertIn("kick", dest_oneshot)

        # 3. Unclassified -> Other
        dest_other, _, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Other",
        )
        self.assertIn("Other", dest_other)

    def test_overwrite_import_mode(self):
        """Verify that importing an existing file name overwrites the target file when overwrite=True."""
        # First import
        dest1, name1, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="Rock",
            instrument="guitar",
            overwrite=True,
        )
        self.assertEqual(name1, "guitar_sample.wav")

        # Second import -> should overwrite and keep guitar_sample.wav
        dest2, name2, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="Rock",
            instrument="guitar",
            overwrite=True,
        )
        self.assertEqual(name2, "guitar_sample.wav")
        self.assertEqual(dest1, dest2)
        self.assertTrue(os.path.exists(dest2))

    def test_duplicate_file_sequential_numbering_when_overwrite_disabled(self):
        """Verify that importing with overwrite=False appends sequential numbers (_1, _2...)."""
        dest1, name1, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="Rock",
            instrument="guitar",
            overwrite=False,
        )
        self.assertEqual(name1, "guitar_sample.wav")

        dest2, name2, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="Rock",
            instrument="guitar",
            overwrite=False,
        )
        self.assertEqual(name2, "guitar_sample_1.wav")
        self.assertTrue(os.path.exists(dest2))

    def test_consolidate_file_group(self):
        """Verify consolidation of duplicate files into a single canonical target."""
        target_dir = self.config.library_dir / "Loop" / "TestPack"
        target_dir.mkdir(parents=True, exist_ok=True)
        canon_file = target_dir / "sample.wav"
        dup1_file = target_dir / "sample_1.wav"
        dup2_file = target_dir / "sample_2.wav"

        canon_file.write_bytes(b"OLD_ORIGINAL")
        dup1_file.write_bytes(b"OLD_DUP1")
        dup2_file.write_bytes(b"LATEST_CONTENT_V2")

        res_path = self.file_manager.consolidate_file_group(
            canonical_target_path=str(canon_file),
            all_duplicate_paths=[str(canon_file), str(dup1_file), str(dup2_file)],
            latest_file_path=str(dup2_file),
        )

        self.assertEqual(res_path, str(canon_file.resolve()))
        self.assertTrue(canon_file.exists())
        self.assertEqual(canon_file.read_bytes(), b"LATEST_CONTENT_V2")
        self.assertFalse(dup1_file.exists())
        self.assertFalse(dup2_file.exists())

    def test_safe_physical_deletion(self):
        """Verify physical file deletion using delete_physical_file."""
        dest, _, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Oneshot",
            instrument="snare",
        )
        self.assertTrue(os.path.exists(dest))

        # Delete (direct or recycle bin)
        self.assertTrue(self.file_manager.delete_physical_file(dest, use_recycle_bin=False))
        self.assertFalse(os.path.exists(dest))

    def test_batch_rollback_cleanup(self):
        """Verify that cleanup_batch_files safely deletes all temporary files during rollback."""
        dest1, _, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="Jazz",
            instrument="piano",
        )
        dest2, _, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="Jazz",
            instrument="bass",
        )
        self.assertTrue(os.path.exists(dest1))
        self.assertTrue(os.path.exists(dest2))

        # Perform rollback cleanup
        self.file_manager.cleanup_batch_files([dest1, dest2])
        self.assertFalse(os.path.exists(dest1))
        self.assertFalse(os.path.exists(dest2))

    def test_clear_all_library_files(self):
        """Verify that clear_all_library_files purges all audio files and resets folders."""
        dest1, _, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Loop",
            genre="Jazz",
            instrument="piano",
        )
        dest2, _, _, _ = self.file_manager.import_single_file(
            src_path=str(self.sample_file),
            sample_type="Oneshot",
            instrument="kick",
        )
        self.assertTrue(os.path.exists(dest1))
        self.assertTrue(os.path.exists(dest2))

        deleted = self.file_manager.clear_all_library_files(use_recycle_bin=False)
        self.assertEqual(deleted, 2)
        self.assertFalse(os.path.exists(dest1))
        self.assertFalse(os.path.exists(dest2))
        self.assertTrue((self.config.library_dir / "Loop").exists())
        self.assertTrue((self.config.library_dir / "Oneshot").exists())


if __name__ == "__main__":
    unittest.main()
