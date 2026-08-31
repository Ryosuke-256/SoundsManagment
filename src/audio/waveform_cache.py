"""
LRU In-Memory Cache for extracted waveform peak data.
Prevents repeated file decoding and ensures memory-bounded performance.
"""

from collections import OrderedDict
import threading
from typing import Optional

from src.audio.waveform_extractor import WaveformData


class WaveformCache:
    """Thread-safe LRU in-memory cache for WaveformData instances."""

    def __init__(self, max_size: int = 100):
        self._max_size = max_size
        self._cache: OrderedDict[str, WaveformData] = OrderedDict()
        self._lock = threading.Lock()

    @property
    def max_size(self) -> int:
        return self._max_size

    def __len__(self) -> int:
        with self._lock:
            return len(self._cache)

    def get(self, file_path: str) -> Optional[WaveformData]:
        """
        Retrieves cached WaveformData for the given file path.
        Moves the item to the end (most recently used).
        """
        if not file_path:
            return None
        with self._lock:
            if file_path in self._cache:
                self._cache.move_to_end(file_path)
                return self._cache[file_path]
            return None

    def put(self, file_path: str, data: WaveformData) -> None:
        """
        Inserts or updates WaveformData for the file path.
        Evicts least recently used items if size exceeds max_size.
        """
        if not file_path or data is None:
            return
        with self._lock:
            if file_path in self._cache:
                self._cache.move_to_end(file_path)
            self._cache[file_path] = data
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def get_or_extract(self, file_path: str, num_bins: Optional[int] = None) -> WaveformData:
        """
        Retrieves cached WaveformData or extracts it using WaveformExtractor if not cached.
        """
        cached = self.get(file_path)
        if cached is not None:
            return cached

        from src.audio.waveform_extractor import WaveformExtractor
        extractor = WaveformExtractor()
        data = extractor.extract_peaks(file_path, num_bins=num_bins)
        if data and data.is_valid:
            self.put(file_path, data)
        return data

    def clear(self) -> None:
        """Clears all cached waveform data."""
        with self._lock:
            self._cache.clear()

    def contains(self, file_path: str) -> bool:
        """Checks if file path is cached."""
        with self._lock:
            return file_path in self._cache
