"""Dedicated Audio Signal Analysis & Auto-Rename Preview Dialog (Story 2.4 / FR-2.5)."""
from pathlib import Path
from typing import List, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QProgressBar,
    QMessageBox,
    QHeaderView,
)

from src.core.models import SampleItem
from src.database.repository import SampleRepository
from src.storage.file_manager import LibraryFileManager
from src.analyzer.auto_renamer import AutoRenamer, RenamePreviewItem
from src.analyzer.audio_analyzer import AudioAnalysisResult
from src.ui.workers import BatchAnalyzeWorker


class AudioAnalyzerDialog(QDialog):
    """Dialog for inspecting, analyzing, and batch-renaming samples with estimated BPM & Key."""

    renamed_completed = pyqtSignal(int)

    def __init__(
        self,
        samples: List[SampleItem],
        repo: SampleRepository,
        file_mgr: LibraryFileManager,
        parent=None,
    ):
        super().__init__(parent)
        self.samples = samples
        self.repo = repo
        self.file_mgr = file_mgr
        self.analysis_results: List[AudioAnalysisResult] = []
        self.preview_items: List[RenamePreviewItem] = []
        self._worker: Optional[BatchAnalyzeWorker] = None

        self.setWindowTitle("Audio Signal Analyzer & Auto-Renamer (Story 2.4)")
        self.resize(850, 520)
        self._setup_ui()
        self._populate_initial_table()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header description
        desc_label = QLabel(
            "Quantitative Audio Signal Processing (Onset & Chroma) automatically estimates BPM and musical Key,\n"
            "formatting file names according to the naming convention '[BaseName]_[BPM]BPM_[Key].[ext]'."
        )
        desc_label.setStyleSheet("color: #b0bec5; font-size: 9.5pt;")
        layout.addWidget(desc_label)

        # Preview Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Select",
            "Original Filename",
            "Detected BPM",
            "Detected Key",
            "New Suggested Filename",
            "Status",
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Bottom Button Bar
        btn_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        btn_layout.addWidget(self.select_all_btn)

        self.deselect_all_btn = QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self._deselect_all)
        btn_layout.addWidget(self.deselect_all_btn)

        btn_layout.addStretch()

        self.start_btn = QPushButton("▶ Start Audio Analysis")
        self.start_btn.setStyleSheet("background-color: #0288d1; color: white; font-weight: bold; padding: 6px 14px;")
        self.start_btn.clicked.connect(self._start_analysis)
        btn_layout.addWidget(self.start_btn)

        self.apply_btn = QPushButton("✓ Apply Rename & Update DB")
        self.apply_btn.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold; padding: 6px 14px;")
        self.apply_btn.setEnabled(False)
        self.apply_btn.clicked.connect(self._apply_renames)
        btn_layout.addWidget(self.apply_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _populate_initial_table(self):
        self.table.setRowCount(len(self.samples))
        for row, sample in enumerate(self.samples):
            # Checkbox item
            cb_item = QTableWidgetItem()
            cb_item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            cb_item.setCheckState(Qt.CheckState.Checked)
            self.table.setItem(row, 0, cb_item)

            # Original Filename
            name_item = QTableWidgetItem(sample.file_name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 1, name_item)

            # BPM
            bpm_item = QTableWidgetItem(f"{int(sample.bpm)}" if sample.bpm is not None else "-")
            bpm_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))
            bpm_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 2, bpm_item)

            # Key
            key_item = QTableWidgetItem(f"{sample.key_root} {sample.key_scale}" if sample.key_root else "-")
            key_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))
            key_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 3, key_item)

            # Suggested Name
            sug_item = QTableWidgetItem("(Run Analysis)")
            sug_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 4, sug_item)

            # Status
            status_item = QTableWidgetItem("Ready")
            status_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter))
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.table.setItem(row, 5, status_item)

    def _select_all(self):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Checked)

    def _deselect_all(self):
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item:
                item.setCheckState(Qt.CheckState.Unchecked)

    def _start_analysis(self):
        file_paths = [s.file_path for s in self.samples]
        if not file_paths:
            return

        self.start_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(file_paths))
        self.progress_bar.setValue(0)

        for r in range(self.table.rowCount()):
            status_item = self.table.item(r, 5)
            if status_item:
                status_item.setText("Analyzing...")

        self._worker = BatchAnalyzeWorker(file_paths=file_paths, parent=self)
        self._worker.progress.connect(self._on_analysis_progress)
        self._worker.finished.connect(self._on_analysis_finished)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()

    def _on_analysis_progress(self, current: int, total: int, filename: str):
        self.progress_bar.setValue(current)
        if 0 <= current - 1 < self.table.rowCount():
            status_item = self.table.item(current - 1, 5)
            if status_item:
                status_item.setText("Processing...")

    def _on_analysis_finished(self, results: List[AudioAnalysisResult]):
        self.analysis_results = results
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        self.apply_btn.setEnabled(True)

        self.preview_items = AutoRenamer.create_rename_previews(
            samples=self.samples,
            analysis_results=self.analysis_results,
        )

        for row, preview in enumerate(self.preview_items):
            # Update BPM
            bpm_text = f"{int(preview.detected_bpm)}" if preview.detected_bpm is not None else "-"
            self.table.item(row, 2).setText(bpm_text)

            # Update Key
            key_text = preview.detected_key if preview.detected_key else "-"
            self.table.item(row, 3).setText(key_text)

            # Update Suggested Name
            self.table.item(row, 4).setText(preview.new_name)

            # Status
            self.table.item(row, 5).setText("Analyzed")

    def _on_analysis_error(self, err_msg: str):
        self.progress_bar.setVisible(False)
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "Analysis Error", err_msg)

    def _apply_renames(self, show_msg: bool = True):
        """Executes atomic rename and database synchronization for checked items."""
        renamed_count = 0
        errors = []

        for row, preview in enumerate(self.preview_items):
            cb = self.table.item(row, 0)
            if not cb or cb.checkState() != Qt.CheckState.Checked:
                continue

            if preview.current_name == preview.new_name:
                continue

            try:
                # 1. Rename physical file
                new_path = self.file_mgr.rename_library_file(preview.current_path, preview.new_name)
                final_name = Path(new_path).name

                # 2. Update Database record
                sample = self.samples[row]
                sample.file_path = new_path
                sample.file_name = final_name
                if preview.detected_bpm is not None:
                    sample.bpm = preview.detected_bpm
                if preview.detected_key:
                    parts = preview.detected_key.split()
                    sample.key_root = parts[0]
                    if len(parts) > 1:
                        sample.key_scale = parts[1]

                self.repo.update_sample(sample)
                renamed_count += 1

                self.table.item(row, 5).setText("Renamed ✓")

            except Exception as e:
                errors.append(f"{preview.current_name}: {str(e)}")
                self.table.item(row, 5).setText("Error ✗")

        if show_msg:
            if errors:
                QMessageBox.warning(
                    self,
                    "Partial Rename Warning",
                    f"Renamed {renamed_count} files.\nErrors occurred on {len(errors)} files:\n" + "\n".join(errors[:5]),
                )
            else:
                QMessageBox.information(
                    self,
                    "Rename Complete",
                    f"Successfully renamed and synchronized {renamed_count} sound samples in the library!",
                )

        self.renamed_completed.emit(renamed_count)
        self.apply_btn.setEnabled(False)
