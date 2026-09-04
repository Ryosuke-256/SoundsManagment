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

    def upsert_sample(self, sample: SampleItem, conn: Optional[sqlite3.Connection] = None) -> int:
        """Inserts a sample or updates it if a record with the same file_path already exists."""
        existing = self.get_sample_by_path(sample.file_path)
        if existing and existing.id:
            sample.id = existing.id
            self.update_sample(sample)
            return sample.id
        else:
            return self.insert_sample(sample, conn=conn)

    def upsert_samples_batch(self, samples: List[SampleItem]) -> int:
        """Upserts a batch of SampleItem records in a single transaction."""
        if not samples:
            return 0
        with self.db_manager.transaction() as conn:
            for s in samples:
                self.upsert_sample(s, conn=conn)
        return len(samples)

    def get_all_samples(self) -> List[SampleItem]:
        """Retrieves all sound sample records from the database."""
        conn = self.db_manager.get_connection()
        cursor = conn.execute("SELECT * FROM samples ORDER BY id ASC;")
        rows = cursor.fetchall()
        return [SampleItem.from_row(row) for row in rows]

    def find_duplicate_groups(self) -> List[Dict[str, Any]]:
        """Identifies groups of duplicate sound samples (e.g. sample.wav, sample_1.wav, sample_2.wav).
        
        Returns:
            List[Dict[str, Any]]: List of duplicate group summaries with latest and obsolete records.
        """
        import re
        import os
        from pathlib import Path

        all_samples = self.get_all_samples()
        re_dup = re.compile(r'^(.*?)(?:_(\d+))?(\.[^.]+)$')

        # Group by (parent_dir, base_canonical_filename)
        groups_dict: Dict[Tuple[str, str], List[Tuple[int, SampleItem]]] = {}

        for s in all_samples:
            p = Path(s.file_path)
            parent_dir = str(p.parent)
            match = re_dup.match(p.name)
            if match:
                base_stem = match.group(1)
                seq_num = int(match.group(2)) if match.group(2) else 0
                ext = match.group(3)
                canonical_name = f"{base_stem}{ext}"
            else:
                canonical_name = p.name
                seq_num = 0

            key = (parent_dir, canonical_name)
            if key not in groups_dict:
                groups_dict[key] = []
            groups_dict[key].append((seq_num, s))

        duplicate_groups: List[Dict[str, Any]] = []

        for (parent_dir, canonical_name), items in groups_dict.items():
            if len(items) > 1:
                # Sort items by file modification time or sequence number (highest first)
                def get_sort_key(item_tuple):
                    seq, sample = item_tuple
                    mtime = 0.0
                    try:
                        if os.path.exists(sample.file_path):
                            mtime = os.path.getmtime(sample.file_path)
                    except OSError:
                        pass
                    return (mtime, seq, sample.id or 0)

                sorted_items = sorted(items, key=get_sort_key, reverse=True)
                latest_sample = sorted_items[0][1]
                obsolete_samples = [it[1] for it in sorted_items[1:]]

                canonical_path = str(Path(parent_dir) / canonical_name)

                duplicate_groups.append({
                    "canonical_name": canonical_name,
                    "canonical_path": canonical_path,
                    "parent_dir": parent_dir,
                    "latest_sample": latest_sample,
                    "obsolete_samples": obsolete_samples,
                    "all_samples": [it[1] for it in sorted_items],
                })

        return duplicate_groups

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

    def clear_all_samples(self) -> int:
        """Deletes all sample records from the database in a single transaction."""
        sql = "DELETE FROM samples;"
        with self.db_manager.transaction() as conn:
            cursor = conn.execute(sql)
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

        # Instruments (Multi-instrument substring / token matching, supports Other)
        if search_filter.instruments:
            inst_clauses = []
            for inst in search_filter.instruments:
                if inst == "Other":
                    inst_clauses.append("(instrument = 'Other' OR instrument IS NULL OR instrument = '')")
                else:
                    inst_clauses.append("(instrument LIKE ? OR instrument = ?)")
                    params.extend([f"%{inst}%", inst])
            conditions.append("(" + " OR ".join(inst_clauses) + ")")

        # Genres (supports Other)
        if search_filter.genres:
            genre_clauses = []
            for gen in search_filter.genres:
                if gen == "Other":
                    genre_clauses.append("(genre = 'Other' OR genre IS NULL OR genre = '')")
                else:
                    genre_clauses.append("genre = ?")
                    params.append(gen)
            conditions.append("(" + " OR ".join(genre_clauses) + ")")

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

        # Unclassified / Other Filters
        if search_filter.only_unclassified_instrument:
            conditions.append("(instrument = 'Other' OR instrument IS NULL OR instrument = '')")
        if search_filter.only_unclassified_genre:
            conditions.append("(genre = 'Other' OR genre IS NULL OR genre = '')")
        if search_filter.only_unknown_key:
            conditions.append("(key_root IS NULL OR key_root = '' OR key_root = 'Other')")
        if search_filter.only_unknown_bpm:
            conditions.append("(bpm IS NULL OR bpm = 0)")

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

    def get_all_instruments(self) -> List[str]:
        """Returns list of all unique individual instrument tags from the database."""
        conn = self.db_manager.get_connection()
        cursor = conn.execute("SELECT DISTINCT instrument FROM samples WHERE instrument IS NOT NULL AND instrument != '';")
        inst_set = set()
        for row in cursor.fetchall():
            raw = row["instrument"]
            for part in raw.split(","):
                clean = part.strip()
                if clean:
                    inst_set.add(clean)
        return sorted(inst_set)

    def get_all_genres(self) -> List[str]:
        """Returns list of all unique genre tags from the database."""
        conn = self.db_manager.get_connection()
        cursor = conn.execute("SELECT DISTINCT genre FROM samples WHERE genre IS NOT NULL AND genre != '';")
        genre_set = set()
        for row in cursor.fetchall():
            clean = row["genre"].strip()
            if clean:
                genre_set.add(clean)
        return sorted(genre_set)
