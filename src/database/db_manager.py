"""Database manager implementing Thread-Local connection, WAL mode, integrity checks, and backups."""
import os
import shutil
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Generator, Optional

from src.core.models import BackupInfo


class DatabaseCorruptedError(Exception):
    """Raised when SQLite database integrity check fails."""
    pass


class DatabaseManager:
    """Manages SQLite database lifecycle, Thread-Local connections, WAL mode, and backups."""

    CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT NOT NULL UNIQUE,
        file_name TEXT NOT NULL,
        file_size INTEGER NOT NULL DEFAULT 0,
        file_hash TEXT NOT NULL DEFAULT '',
        sample_type TEXT NOT NULL DEFAULT 'Other',
        instrument TEXT NOT NULL DEFAULT 'Other',
        genre TEXT NOT NULL DEFAULT 'Other',
        bpm REAL,
        key_root TEXT,
        key_scale TEXT,
        creator TEXT NOT NULL DEFAULT 'Other',
        duration_sec REAL NOT NULL DEFAULT 0.0,
        sample_rate INTEGER NOT NULL DEFAULT 44100,
        channels INTEGER NOT NULL DEFAULT 2,
        bit_depth INTEGER NOT NULL DEFAULT 16,
        format TEXT NOT NULL DEFAULT 'WAV',
        tags TEXT NOT NULL DEFAULT '',
        is_favorite INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """

    CREATE_INDEXES_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_samples_type ON samples(sample_type);",
        "CREATE INDEX IF NOT EXISTS idx_samples_instrument ON samples(instrument);",
        "CREATE INDEX IF NOT EXISTS idx_samples_genre ON samples(genre);",
        "CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);",
        "CREATE INDEX IF NOT EXISTS idx_samples_key ON samples(key_root, key_scale);",
        "CREATE INDEX IF NOT EXISTS idx_samples_creator ON samples(creator);",
        "CREATE INDEX IF NOT EXISTS idx_samples_favorite ON samples(is_favorite);",
        "CREATE INDEX IF NOT EXISTS idx_samples_hash ON samples(file_hash);",
    ]

    def __init__(self, db_path: str):
        self.db_path = str(Path(db_path).resolve())
        self._local = threading.local()
        self._lock = threading.Lock()
        self._ensure_db_dir()
        self.initialize_schema()

    def _ensure_db_dir(self) -> None:
        """Ensures the directory containing the database file exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Returns a thread-local SQLite connection configured with WAL mode."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                self.db_path,
                timeout=10.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            # Configure WAL mode and pragmas for performance and crash resilience
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA busy_timeout = 5000;")
            self._local.conn = conn
        return self._local.conn

    def close_connection(self) -> None:
        """Closes the current thread's SQLite connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager for executing transactions with automatic commit and rollback."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def initialize_schema(self) -> None:
        """Initializes database tables and performance indexes."""
        with self.transaction() as conn:
            conn.execute(self.CREATE_TABLE_SQL)
            for index_sql in self.CREATE_INDEXES_SQL:
                conn.execute(index_sql)

    def check_integrity(self) -> bool:
        """Runs PRAGMA integrity_check on the database.
        
        Returns:
            bool: True if integrity is OK.
        Raises:
            DatabaseCorruptedError: If database is corrupted.
        """
        conn = self.get_connection()
        cursor = conn.execute("PRAGMA integrity_check;")
        rows = cursor.fetchall()
        if not rows or rows[0][0].lower() != "ok":
            error_msg = "; ".join([r[0] for r in rows])
            raise DatabaseCorruptedError(f"Database corruption detected: {error_msg}")
        return True

    def create_snapshot_backup(self, backup_dir: str, max_generations: int = 5) -> str:
        """Creates a snapshot backup using SQLite online backup API and rotates older backups.
        
        Args:
            backup_dir: Directory where backups will be stored.
            max_generations: Maximum number of backup generations to retain.
            
        Returns:
            str: Path to the created backup file.
        """
        b_dir = Path(backup_dir)
        b_dir.mkdir(parents=True, exist_ok=True)
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_file = b_dir / f"library_backup_{timestamp_str}.db"

        # Safe online backup via sqlite3 backup API
        source_conn = self.get_connection()
        with sqlite3.connect(str(backup_file)) as dest_conn:
            source_conn.backup(dest_conn)

        self._rotate_backups(b_dir, max_generations)
        return str(backup_file)

    def _rotate_backups(self, backup_dir: Path, max_generations: int) -> None:
        """Removes oldest backups if count exceeds max_generations."""
        backup_files = sorted(
            backup_dir.glob("library_backup_*.db"),
            key=lambda p: p.stat().st_mtime
        )
        while len(backup_files) > max_generations:
            oldest = backup_files.pop(0)
            try:
                oldest.unlink()
            except OSError:
                pass

    def get_available_backups(self, backup_dir: str) -> List[BackupInfo]:
        """Lists available backup snapshot files sorted by newest first."""
        b_dir = Path(backup_dir)
        if not b_dir.exists():
            return []
        backup_files = sorted(
            b_dir.glob("library_backup_*.db"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        results = []
        for p in backup_files:
            stat = p.stat()
            created_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            results.append(BackupInfo(
                file_path=str(p.resolve()),
                file_name=p.name,
                file_size=stat.st_size,
                created_time=created_str
            ))
        return results

    def restore_from_backup(self, backup_file_path: str) -> bool:
        """Restores the database from a backup file."""
        src_path = Path(backup_file_path)
        if not src_path.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file_path}")

        # Close any open thread connections
        self.close_connection()

        # Copy backup over current db file
        shutil.copy2(str(src_path), self.db_path)

        # Remove WAL and SHM files if present
        for ext in ["-wal", "-shm"]:
            wal_file = Path(self.db_path + ext)
            if wal_file.exists():
                try:
                    wal_file.unlink()
                except OSError:
                    pass

        # Re-initialize and verify integrity
        self.initialize_schema()
        return self.check_integrity()

    def checkpoint_wal(self) -> None:
        """Executes a WAL checkpoint to truncate wal log file on shutdown."""
        try:
            conn = self.get_connection()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
        except Exception:
            pass
