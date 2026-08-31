"""Unit tests for Unit 1: DatabaseManager and SampleRepository."""
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.core.models import SampleItem, SearchFilter
from src.database.db_manager import DatabaseManager, DatabaseCorruptedError
from src.database.repository import SampleRepository


class TestUnit1Database(unittest.TestCase):
    """Test suite for database initialization, WAL mode, CRUD, search, and backups."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_library.db")
        self.backup_dir = str(Path(self.temp_dir) / "Backups")
        self.db_manager = DatabaseManager(self.db_path)
        self.repository = SampleRepository(self.db_manager)

    def tearDown(self):
        self.db_manager.close_connection()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_database_initialization_and_wal(self):
        """Verify that tables and indexes are created and WAL mode is active."""
        conn = self.db_manager.get_connection()
        cursor = conn.execute("PRAGMA journal_mode;")
        row = cursor.fetchone()
        self.assertEqual(row[0].lower(), "wal")

        self.assertTrue(self.db_manager.check_integrity())

    def test_sample_crud_operations(self):
        """Verify Insert, Query, Update, and Delete operations for SampleItem."""
        sample = SampleItem(
            file_path="C:/Sounds/guitar_loop.wav",
            file_name="guitar_loop.wav",
            file_size=102400,
            file_hash="hash12345",
            sample_type="Loop",
            instrument="guitar",
            genre="SS_Guitar_Snob",
            bpm=174.0,
            key_root="C#",
            key_scale="minor",
            creator="BANDLAB",
            duration_sec=5.5,
            is_favorite=True,
            tags="electric,lead",
        )

        # 1. Insert
        sample_id = self.repository.insert_sample(sample)
        self.assertIsNotNone(sample_id)
        self.assertEqual(sample.id, sample_id)

        # 2. Query by ID
        fetched = self.repository.get_sample_by_id(sample_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.file_name, "guitar_loop.wav")
        self.assertEqual(fetched.bpm, 174.0)
        self.assertEqual(fetched.key_root, "C#")
        self.assertEqual(fetched.key_scale, "minor")
        self.assertTrue(fetched.is_favorite)

        # 3. Query by path
        fetched_path = self.repository.get_sample_by_path("C:/Sounds/guitar_loop.wav")
        self.assertIsNotNone(fetched_path)
        self.assertEqual(fetched_path.id, sample_id)

        # 4. Update
        fetched.bpm = 175.0
        fetched.tags = "electric,lead,edited"
        self.assertTrue(self.repository.update_sample(fetched))

        updated = self.repository.get_sample_by_id(sample_id)
        self.assertEqual(updated.bpm, 175.0)
        self.assertEqual(updated.tags, "electric,lead,edited")

        # 5. Delete
        self.assertTrue(self.repository.delete_sample(sample_id))
        self.assertIsNone(self.repository.get_sample_by_id(sample_id))

    def test_faceted_search_and_filtering(self):
        """Verify faceted search with type, instrument, genre, bpm range, key, and free text."""
        samples = [
            SampleItem(
                file_path=f"C:/Sounds/loop_{i}.wav",
                file_name=f"loop_{i}.wav",
                sample_type="Loop",
                instrument="guitar" if i % 2 == 0 else "bass",
                genre="Rock",
                bpm=120.0 + i * 10,
                key_root="C" if i % 2 == 0 else "D",
                key_scale="minor",
                creator="BANDLAB",
            )
            for i in range(10)
        ]
        # Add a Oneshot sample
        samples.append(SampleItem(
            file_path="C:/Sounds/kick_01.wav",
            file_name="kick_01.wav",
            sample_type="Oneshot",
            instrument="kick",
            genre="Electronic",
            creator="HEAVEE",
        ))
        # Add an Other sample
        samples.append(SampleItem(
            file_path="C:/Sounds/ambient_noise.wav",
            file_name="ambient_noise.wav",
            sample_type="Other",
            instrument="Other",
            genre="Other",
            creator="Other",
            tags="field_recording,fx",
        ))

        self.repository.insert_samples_batch(samples)
        self.assertEqual(self.repository.get_total_count(), 12)

        # Filter by Type
        res_loop = self.repository.search_samples(SearchFilter(sample_types=["Loop"]))
        self.assertEqual(len(res_loop), 10)

        # Filter by Instrument + BPM range
        res_guitar = self.repository.search_samples(SearchFilter(
            instruments=["guitar"],
            bpm_min=120.0,
            bpm_max=150.0
        ))
        # i = 0 (120), i = 2 (140) -> 2 results
        self.assertEqual(len(res_guitar), 2)

        # Filter by Key
        res_key = self.repository.search_samples(SearchFilter(key_roots=["D"]))
        self.assertEqual(len(res_key), 5)

        # Free text search
        res_text = self.repository.search_samples(SearchFilter(query_text="ambient"))
        self.assertEqual(len(res_text), 1)
        self.assertEqual(res_text[0].file_name, "ambient_noise.wav")

        # Facet aggregation counts
        facets = self.repository.get_facet_counts()
        self.assertEqual(facets["sample_types"]["Loop"], 10)
        self.assertEqual(facets["sample_types"]["Oneshot"], 1)
        self.assertEqual(facets["sample_types"]["Other"], 1)
        self.assertEqual(facets["instruments"]["guitar"], 5)
        self.assertEqual(facets["instruments"]["kick"], 1)

    def test_backup_creation_and_restore(self):
        """Verify snapshot backup generation, rotation, and database restoration."""
        # Insert test data
        self.repository.insert_sample(SampleItem(
            file_path="C:/Sounds/test1.wav",
            file_name="test1.wav",
            sample_type="Loop",
        ))

        # Create 3 backups
        for _ in range(3):
            backup_path = self.db_manager.create_snapshot_backup(self.backup_dir, max_generations=5)
            self.assertTrue(os.path.exists(backup_path))

        backups = self.db_manager.get_available_backups(self.backup_dir)
        self.assertEqual(len(backups), 3)

        # Modify database
        self.repository.insert_sample(SampleItem(
            file_path="C:/Sounds/test2.wav",
            file_name="test2.wav",
            sample_type="Oneshot",
        ))
        self.assertEqual(self.repository.get_total_count(), 2)

        # Restore from the oldest backup (which only had 1 record)
        oldest_backup = backups[-1].file_path
        self.assertTrue(self.db_manager.restore_from_backup(oldest_backup))
        self.assertEqual(self.repository.get_total_count(), 1)


if __name__ == "__main__":
    unittest.main()
