"""Sample repository implementing CRUD, dynamic faceted search, and facet aggregations."""
import sqlite3
from typing import List, Dict, Any, Optional, Tuple

from src.core.models import SampleItem, SearchFilter, get_current_iso_timestamp
from src.database.db_manager import DatabaseManager


class SampleRepository:
    """Repository for querying, inserting, updating, and deleting SampleItem records."""

    ALLOWED_SORT_COLUMNS = {
        "id": "id",
        "file_name": "file_name",
        "sample_type": "sample_type",
        "instrument": "instrument",
        "genre": "genre",
        "bpm": "bpm",
        "key_root": "key_root",
        "creator": "creator",
        "duration_sec": "duration_sec",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def insert_sample(self, sample: SampleItem, conn: Optional[sqlite3.Connection] = None) -> int:
        """Inserts a single SampleItem into the database and returns its assigned ID."""
        sql = """
        INSERT INTO samples (
            file_path, file_name, file_size, file_hash, sample_type,
            instrument, genre, bpm, key_root, key_scale, creator,
            duration_sec, sample_rate, channels, bit_depth, format,
            tags, is_favorite, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """
        params = (
            sample.file_path,
            sample.file_name,
            sample.file_size,
            sample.file_hash,
            sample.sample_type,
            sample.instrument,
            sample.genre,
            sample.bpm,
            sample.key_root,
            sample.key_scale,
            sample.creator,
            sample.duration_sec,
            sample.sample_rate,
            sample.channels,
            sample.bit_depth,
            sample.format,
            sample.tags,
            1 if sample.is_favorite else 0,
            sample.created_at or get_current_iso_timestamp(),
            sample.updated_at or get_current_iso_timestamp(),
        )

        if conn is not None:
            cursor = conn.execute(sql, params)
            sample.id = cursor.lastrowid
            return sample.id
        else:
            with self.db_manager.transaction() as transaction_conn:
                cursor = transaction_conn.execute(sql, params)
                sample.id = cursor.lastrowid
                return sample.id

    def insert_samples_batch(self, samples: List[SampleItem], conn: Optional[sqlite3.Connection] = None) -> int:
        """Inserts a list of SampleItem records in batch within a single transaction."""
        if not samples:
            return 0

        sql = """
        INSERT INTO samples (
            file_path, file_name, file_size, file_hash, sample_type,
            instrument, genre, bpm, key_root, key_scale, creator,
            duration_sec, sample_rate, channels, bit_depth, format,
            tags, is_favorite, created_at, updated_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        );
        """
        params_list = []
        for s in samples:
            params_list.append((
                s.file_path,
                s.file_name,
                s.file_size,
                s.file_hash,
                s.sample_type,
                s.instrument,
                s.genre,
                s.bpm,
                s.key_root,
                s.key_scale,
                s.creator,
                s.duration_sec,
                s.sample_rate,
                s.channels,
                s.bit_depth,
                s.format,
                s.tags,
                1 if s.is_favorite else 0,
                s.created_at or get_current_iso_timestamp(),
                s.updated_at or get_current_iso_timestamp(),
            ))

        if conn is not None:
            conn.executemany(sql, params_list)
            return len(samples)
        else:
            with self.db_manager.transaction() as transaction_conn:
                transaction_conn.executemany(sql, params_list)
                return len(samples)

    def update_sample(self, sample: SampleItem) -> bool:
        """Updates metadata of an existing SampleItem record."""
        if sample.id is None:
            raise ValueError("SampleItem ID cannot be None when updating.")

        sql = """
        UPDATE samples SET
            file_path = ?, file_name = ?, file_size = ?, file_hash = ?,
            sample_type = ?, instrument = ?, genre = ?, bpm = ?,
            key_root = ?, key_scale = ?, creator = ?, duration_sec = ?,
            sample_rate = ?, channels = ?, bit_depth = ?, format = ?,
            tags = ?, is_favorite = ?, updated_at = ?
        WHERE id = ?;
        """
        params = (
            sample.file_path,
            sample.file_name,
            sample.file_size,
            sample.file_hash,
            sample.sample_type,
            sample.instrument,
            sample.genre,
            sample.bpm,
            sample.key_root,
            sample.key_scale,
            sample.creator,
            sample.duration_sec,
            sample.sample_rate,
            sample.channels,
            sample.bit_depth,
            sample.format,
            sample.tags,
            1 if sample.is_favorite else 0,
            get_current_iso_timestamp(),
            sample.id,
        )

        with self.db_manager.transaction() as conn:
            cursor = conn.execute(sql, params)
            return cursor.rowcount > 0

    def delete_sample(self, sample_id: int) -> bool:
        """Deletes a single sample record by its ID."""
        sql = "DELETE FROM samples WHERE id = ?;"
        with self.db_manager.transaction() as conn:
            cursor = conn.execute(sql, (sample_id,))
            return cursor.rowcount > 0

    def delete_samples_batch(self, sample_ids: List[int]) -> int:
        """Deletes multiple sample records by their IDs in a single transaction."""
        if not sample_ids:
            return 0
        placeholders = ",".join(["?"] * len(sample_ids))
        sql = f"DELETE FROM samples WHERE id IN ({placeholders});"
        with self.db_manager.transaction() as conn:
            cursor = conn.execute(sql, tuple(sample_ids))
            return cursor.rowcount

    def get_sample_by_id(self, sample_id: int) -> Optional[SampleItem]:
        """Retrieves a single sample record by ID."""
        sql = "SELECT * FROM samples WHERE id = ?;"
        conn = self.db_manager.get_connection()
        cursor = conn.execute(sql, (sample_id,))
        row = cursor.fetchone()
        return SampleItem.from_row(row) if row else None

    def get_sample_by_path(self, file_path: str) -> Optional[SampleItem]:
        """Retrieves a single sample record by its unique file path."""
        sql = "SELECT * FROM samples WHERE file_path = ?;"
        conn = self.db_manager.get_connection()
        cursor = conn.execute(sql, (file_path,))
        row = cursor.fetchone()
        return SampleItem.from_row(row) if row else None

    def get_sample_by_hash(self, file_hash: str) -> Optional[SampleItem]:
        """Retrieves a sample record by its hash."""
        if not file_hash:
            return None
        sql = "SELECT * FROM samples WHERE file_hash = ? LIMIT 1;"
        conn = self.db_manager.get_connection()
        cursor = conn.execute(sql, (file_hash,))
        row = cursor.fetchone()
        return SampleItem.from_row(row) if row else None

    def search_samples(self, search_filter: SearchFilter) -> List[SampleItem]:
        """Executes a faceted search query with parameterized SQL filtering and sorting."""
        conditions: List[str] = []
        params: List[Any] = []

        # Sample Types
        if search_filter.sample_types:
            placeholders = ",".join(["?"] * len(search_filter.sample_types))
            conditions.append(f"sample_type IN ({placeholders})")
            params.extend(search_filter.sample_types)

        # Instruments
        if search_filter.instruments:
            placeholders = ",".join(["?"] * len(search_filter.instruments))
            conditions.append(f"instrument IN ({placeholders})")
            params.extend(search_filter.instruments)

        # Genres
        if search_filter.genres:
            placeholders = ",".join(["?"] * len(search_filter.genres))
            conditions.append(f"genre IN ({placeholders})")
            params.extend(search_filter.genres)

        # Key Roots
        if search_filter.key_roots:
            placeholders = ",".join(["?"] * len(search_filter.key_roots))
            conditions.append(f"key_root IN ({placeholders})")
            params.extend(search_filter.key_roots)

        # Key Scales
        if search_filter.key_scales:
            placeholders = ",".join(["?"] * len(search_filter.key_scales))
            conditions.append(f"key_scale IN ({placeholders})")
            params.extend(search_filter.key_scales)

        # BPM Range
        if search_filter.bpm_min is not None:
            conditions.append("bpm >= ?")
            params.append(search_filter.bpm_min)
        if search_filter.bpm_max is not None:
            conditions.append("bpm <= ?")
            params.append(search_filter.bpm_max)

        # Creators
        if search_filter.creators:
            placeholders = ",".join(["?"] * len(search_filter.creators))
            conditions.append(f"creator IN ({placeholders})")
            params.extend(search_filter.creators)

        # Favorites Only
        if search_filter.is_favorite_only:
            conditions.append("is_favorite = 1")

        # Query text (free text match across file_name, tags, instrument, genre, creator)
        if search_filter.query_text and search_filter.query_text.strip():
            wildcard = f"%{search_filter.query_text.strip()}%"
            conditions.append(
                "(file_name LIKE ? OR tags LIKE ? OR instrument LIKE ? OR genre LIKE ? OR creator LIKE ?)"
            )
            params.extend([wildcard] * 5)

        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""

        # Validate sorting column against whitelist to prevent SQL injection
        sort_col = self.ALLOWED_SORT_COLUMNS.get(search_filter.sort_column, "file_name")
        sort_dir = "DESC" if search_filter.sort_direction.upper() == "DESC" else "ASC"

        # NULL ordering handling for numeric fields (e.g. bpm)
        if sort_col == "bpm":
            order_clause = f" ORDER BY (bpm IS NULL), bpm {sort_dir}, file_name ASC"
        else:
            order_clause = f" ORDER BY {sort_col} {sort_dir}"

        sql = f"SELECT * FROM samples{where_clause}{order_clause};"

        conn = self.db_manager.get_connection()
        cursor = conn.execute(sql, tuple(params))
        rows = cursor.fetchall()
        return [SampleItem.from_row(row) for row in rows]

    def get_facet_counts(self) -> Dict[str, Dict[str, int]]:
        """Computes on-demand item counts grouped by each facet attribute using indexes."""
        conn = self.db_manager.get_connection()
        facets: Dict[str, Dict[str, int]] = {
            "sample_types": {},
            "instruments": {},
            "genres": {},
            "keys": {},
            "creators": {},
        }

        # Sample Types
        cursor = conn.execute("SELECT sample_type, COUNT(*) as count FROM samples GROUP BY sample_type;")
        for row in cursor.fetchall():
            facets["sample_types"][row["sample_type"]] = row["count"]

        # Instruments
        cursor = conn.execute(
            "SELECT instrument, COUNT(*) as count FROM samples WHERE instrument IS NOT NULL AND instrument != '' GROUP BY instrument ORDER BY count DESC;"
        )
        for row in cursor.fetchall():
            facets["instruments"][row["instrument"]] = row["count"]

        # Genres
        cursor = conn.execute(
            "SELECT genre, COUNT(*) as count FROM samples WHERE genre IS NOT NULL AND genre != '' GROUP BY genre ORDER BY count DESC;"
        )
        for row in cursor.fetchall():
            facets["genres"][row["genre"]] = row["count"]

        # Keys (combined key_root + key_scale e.g. "C# minor")
        cursor = conn.execute(
            "SELECT key_root, key_scale, COUNT(*) as count FROM samples WHERE key_root IS NOT NULL AND key_root != '' GROUP BY key_root, key_scale ORDER BY count DESC;"
        )
        for row in cursor.fetchall():
            scale_str = f" {row['key_scale']}" if row['key_scale'] else ""
            key_name = f"{row['key_root']}{scale_str}"
            facets["keys"][key_name] = row["count"]

        # Creators
        cursor = conn.execute(
            "SELECT creator, COUNT(*) as count FROM samples WHERE creator IS NOT NULL AND creator != '' GROUP BY creator ORDER BY count DESC;"
        )
        for row in cursor.fetchall():
            facets["creators"][row["creator"]] = row["count"]

        return facets

    def get_total_count(self) -> int:
        """Returns total number of sound sample items in the library."""
        conn = self.db_manager.get_connection()
        cursor = conn.execute("SELECT COUNT(*) as count FROM samples;")
        row = cursor.fetchone()
        return row["count"] if row else 0
