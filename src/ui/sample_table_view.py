"""Custom QTableView with DAW OLE Drag & Drop and Context Menus."""
import logging
import os
import subprocess
import sys
from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import (
    QTableView,
    QMenu,
    QMessageBox,
    QAbstractItemView,
    QHeaderView,
)
from PyQt6.QtGui import QDrag, QCursor

from src.core.models import SampleItem
from src.ui.sample_table_model import SampleTableModel

logger = logging.getLogger(__name__)


class SampleTableView(QTableView):
    """QTableView customized for DAW drag-and-drop and audio sample operations."""

    sample_selected = pyqtSignal(SampleItem)
    sample_double_clicked = pyqtSignal(SampleItem)
    remove_from_db_requested = pyqtSignal(list)      # List[SampleItem]
    delete_trash_requested = pyqtSignal(list)        # List[SampleItem]
    analyze_sample_requested = pyqtSignal(list)      # List[SampleItem]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_view()

    def _setup_view(self):
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(False)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)
        self.setSortingEnabled(True)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(False)
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Context menu policy
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.doubleClicked.connect(self._on_double_clicked)

    def selectionChanged(self, selected, deselected):
        super().selectionChanged(selected, deselected)
        try:
            selected_samples = self.get_selected_samples()
            if selected_samples:
                self.sample_selected.emit(selected_samples[0])
        except Exception as e:
            logger.debug("Error in selectionChanged: %s", e)

    def _on_double_clicked(self, index):
        model: Optional[SampleTableModel] = self.model()  # type: ignore
        if model and index.isValid():
            sample = model.get_sample(index.row())
            if sample:
                self.sample_double_clicked.emit(sample)

    def get_selected_samples(self) -> List[SampleItem]:
        """Returns list of currently selected SampleItems."""
        model: Optional[SampleTableModel] = self.model()  # type: ignore
        if not model:
            return []

        indexes = self.selectionModel().selectedRows()
        samples = []
        for idx in indexes:
            sample = model.get_sample(idx.row())
            if sample:
                samples.append(sample)
        return samples

    def startDrag(self, supportedActions: Qt.DropAction):
        """Initiates Windows OLE drag to Cakewalk / Sonar DAW with pre-flight check."""
        try:
            selected_samples = self.get_selected_samples()
            if not selected_samples:
                return

            # Pre-flight check: ensure files exist (RESILIENCY-10)
            valid_samples = [s for s in selected_samples if os.path.isfile(os.path.abspath(s.file_path))]
            if not valid_samples:
                return

            model: Optional[SampleTableModel] = self.model()  # type: ignore
            if not model:
                return

            selected_indexes = self.selectionModel().selectedRows()
            mime_data = model.mimeData(selected_indexes)

            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.DropAction.CopyAction | Qt.DropAction.LinkAction, Qt.DropAction.CopyAction)
        except Exception as e:
            logger.error("Failed to execute drag and drop: %s", e)

    def _show_context_menu(self, pos: QPoint):
        """Displays right-click context menu for selected audio samples."""
        selected = self.get_selected_samples()
        if not selected:
            return

        menu = QMenu(self)

        play_act = menu.addAction("▶ Play")
        reveal_act = menu.addAction("📁 Reveal in Explorer")
        analyze_act = menu.addAction("🔍 Analyze BPM & Key (Story 2.4)...")
        menu.addSeparator()
        remove_act = menu.addAction("❌ Remove from Library (Keep File)")
        trash_act = menu.addAction("🗑 Move to Recycle Bin & Delete")

        action = menu.exec(self.viewport().mapToGlobal(pos))
        if not action:
            return

        if action == play_act:
            self.sample_double_clicked.emit(selected[0])
        elif action == reveal_act:
            self._reveal_in_explorer(selected[0].file_path)
        elif action == analyze_act:
            self.analyze_sample_requested.emit(selected)
        elif action == remove_act:
            self.remove_from_db_requested.emit(selected)
        elif action == trash_act:
            self.delete_trash_requested.emit(selected)

    def _reveal_in_explorer(self, file_path: str):
        """Reveals file in Windows Explorer."""
        norm_path = os.path.abspath(file_path)
        if not os.path.exists(norm_path):
            QMessageBox.warning(self, "File Not Found", f"The file cannot be found:\n{norm_path}")
            return

        if sys.platform == "win32":
            subprocess.run(["explorer", f"/select,{norm_path}"], check=False)
        else:
            folder = os.path.dirname(norm_path)
            subprocess.run(["open", folder], check=False)
