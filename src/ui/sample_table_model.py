"""PyQt6 table model for virtualized high-performance sample browsing."""
import os
from typing import List, Optional, Any
from PyQt6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    Qt,
    QMimeData,
    QUrl,
)

from src.core.models import SampleItem


class SampleTableModel(QAbstractTableModel):
    """Virtualized QAbstractTableModel representing sound sample items."""

    COLUMNS = [
        "Name",
        "Type",
        "Instrument",
        "Genre",
        "BPM",
        "Key",
        "Creator",
        "Duration",
    ]

    def __init__(self, samples: Optional[List[SampleItem]] = None, parent=None):
        super().__init__(parent)
        self._samples: List[SampleItem] = samples or []

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._samples)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._samples)):
            return None

        sample = self._samples[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0:
                return sample.file_name
            elif col == 1:
                return sample.sample_type
            elif col == 2:
                return sample.instrument
            elif col == 3:
                return sample.genre
            elif col == 4:
                return f"{int(sample.bpm)}" if sample.bpm is not None else "-"
            elif col == 5:
                if sample.key_root:
                    scale = f" {sample.key_scale}" if sample.key_scale else ""
                    return f"{sample.key_root}{scale}"
                return "-"
            elif col == 6:
                return sample.creator
            elif col == 7:
                mins = int(sample.duration_sec // 60)
                secs = sample.duration_sec % 60
                return f"{mins:02d}:{secs:04.1f}"

        elif role == Qt.ItemDataRole.UserRole:
            return sample

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in (1, 4, 5, 7):
                return int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            return int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        elif role == Qt.ItemDataRole.ToolTipRole:
            return f"Path: {sample.file_path}\nSize: {sample.file_size:,} bytes\nFormat: {sample.format} ({sample.sample_rate}Hz / {sample.bit_depth}bit)"

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self.COLUMNS):
                return self.COLUMNS[section]
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        default_flags = super().flags(index)
        if index.isValid():
            return default_flags | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return default_flags

    def set_samples(self, samples: List[SampleItem]):
        """Replaces the active sample list with animation-safe beginResetModel."""
        self.beginResetModel()
        self._samples = list(samples)
        self.endResetModel()

    def get_sample(self, row: int) -> Optional[SampleItem]:
        """Returns the SampleItem at the specified row index."""
        if 0 <= row < len(self._samples):
            return self._samples[row]
        return None

    def get_samples(self) -> List[SampleItem]:
        """Returns copy of all active sample items."""
        return list(self._samples)

    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        """Constructs QMimeData for external DAW drag and drop (text/uri-list)."""
        mime_data = QMimeData()
        urls: List[QUrl] = []
        paths: List[str] = []

        seen_rows = set()
        for idx in indexes:
            row = idx.row()
            if row not in seen_rows and 0 <= row < len(self._samples):
                seen_rows.add(row)
                sample = self._samples[row]
                abs_p = os.path.abspath(sample.file_path)
                urls.append(QUrl.fromLocalFile(abs_p))
                paths.append(abs_p)

        mime_data.setUrls(urls)
        mime_data.setText("\n".join(paths))
        return mime_data
