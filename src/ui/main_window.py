"""Main application window uniting 3-pane layout, DAW drag-and-drop, audio engine, and signal analyzer."""
import logging
import os
from pathlib import Path
from typing import Optional, List
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QFileDialog,
    QMessageBox,
    QToolBar,
    QStatusBar,
    QLabel,
    QPushButton,
    QSlider,
    QProgressBar,
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence

from src.core.config import LibraryConfig
from src.core.models import SampleItem, SearchFilter
from src.database.repository import SampleRepository
from src.storage.file_manager import LibraryFileManager
from src.audio.player_service import AudioPlayerService, PlaybackState, PlaybackMode
from src.audio.waveform_cache import WaveformCache
from src.ui.sample_table_model import SampleTableModel
from src.ui.sample_table_view import SampleTableView
from src.ui.facet_filter_widget import FacetFilterWidget
from src.ui.waveform_widget import WaveformWidget
from src.ui.workers import ImportWorker, RescanWorker, ConsolidateDuplicatesWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary GUI Window for BandLab Sound Sample Manager."""

    def __init__(
        self,
        config: LibraryConfig,
        repo: SampleRepository,
        file_mgr: LibraryFileManager,
        player_service: Optional[AudioPlayerService] = None,
        waveform_cache: Optional[WaveformCache] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.config = config
        self.repo = repo
        self.file_mgr = file_mgr
        self.player = player_service or AudioPlayerService()
        self.waveform_cache = waveform_cache or WaveformCache()

        self._active_worker: Optional[ImportWorker] = None
        self._rescan_worker: Optional[RescanWorker] = None
        self._consolidate_worker: Optional[ConsolidateDuplicatesWorker] = None

        self.setWindowTitle("BandLab Sound Sample Manager")
        self.resize(1100, 720)
        self.setMinimumSize(800, 500)

        self._setup_ui()
        self._setup_menus_and_toolbars()
        self._setup_signals()
        self._refresh_data()

    def _setup_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Main horizontal splitter: Left = FacetSidebar, Right = (Table + Bottom Player)
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Facet Filter Sidebar
        self.facet_widget = FacetFilterWidget()
        self.main_splitter.addWidget(self.facet_widget)

        # Right Container: Table + Bottom Audio Player Panel
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        # Table Model & View
        self.table_model = SampleTableModel()
        self.table_view = SampleTableView()
        self.table_view.setModel(self.table_model)
        right_layout.addWidget(self.table_view, stretch=1)

        # Bottom Audio Preview Panel
        self.player_panel = QWidget()
        self.player_panel.setStyleSheet("background-color: #1a1a24; border-radius: 4px; padding: 4px;")
        player_layout = QVBoxLayout(self.player_panel)
        player_layout.setContentsMargins(6, 6, 6, 6)
        player_layout.setSpacing(4)

        # Waveform Widget
        self.waveform_widget = WaveformWidget()
        self.waveform_widget.setMinimumHeight(64)
        player_layout.addWidget(self.waveform_widget)

        # Transport & Volume Controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setFixedWidth(75)
        self.play_btn.clicked.connect(self._on_play_pause_clicked)
        controls_layout.addWidget(self.play_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFixedWidth(70)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        controls_layout.addWidget(self.stop_btn)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #b0bec5; font-family: monospace; font-size: 9.5pt;")
        controls_layout.addWidget(self.time_label)

        controls_layout.addStretch()

        self.autoplay_btn = QPushButton("Auto-Play: ON")
        self.autoplay_btn.setCheckable(True)
        self.autoplay_btn.setChecked(True)
        self.autoplay_btn.setStyleSheet("QPushButton:checked { background-color: #00838f; color: white; font-weight: bold; }")
        self.autoplay_btn.clicked.connect(self._on_autoplay_toggled)
        controls_layout.addWidget(self.autoplay_btn)

        self.loop_btn = QPushButton("Loop: ON")
        self.loop_btn.setCheckable(True)
        self.loop_btn.setChecked(True)
        self.loop_btn.setStyleSheet("QPushButton:checked { background-color: #4527a0; color: white; font-weight: bold; }")
        self.loop_btn.clicked.connect(self._on_loop_toggled)
        controls_layout.addWidget(self.loop_btn)

        controls_layout.addWidget(QLabel("Vol:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(int(self.player.volume * 100))
        self.volume_slider.setFixedWidth(90)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        controls_layout.addWidget(self.volume_slider)

        player_layout.addLayout(controls_layout)
        right_layout.addWidget(self.player_panel)

        self.main_splitter.addWidget(right_container)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([260, 840])

        main_layout.addWidget(self.main_splitter)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, stretch=1)

        self.status_progress = QProgressBar()
        self.status_progress.setMaximumWidth(200)
        self.status_progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.status_progress)

    def _setup_menus_and_toolbars(self):
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        import_act = QAction("📁 &Import Folder...", self)
        import_act.setShortcut(QKeySequence("Ctrl+O"))
        import_act.triggered.connect(self.action_import_folder)
        file_menu.addAction(import_act)

        rescan_act = QAction("🔄 &Rescan Library", self)
        rescan_act.setShortcut(QKeySequence("F5"))
        rescan_act.triggered.connect(self.action_rescan_library)
        file_menu.addAction(rescan_act)

        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        analyzer_act = QAction("🔍 &Audio Signal Analyzer & Auto-Rename (Story 2.4)...", self)
        analyzer_act.setShortcut(QKeySequence("Ctrl+A"))
        analyzer_act.triggered.connect(self.action_open_analyzer_dialog)
        tools_menu.addAction(analyzer_act)

        consolidate_act = QAction("🧹 &Consolidate Duplicate Samples (Latest Wins)...", self)
        consolidate_act.triggered.connect(self.action_consolidate_duplicates)
        tools_menu.addAction(consolidate_act)

        backup_act = QAction("💾 &Backup Database Snapshot...", self)
        backup_act.triggered.connect(self.action_backup_database)
        tools_menu.addAction(backup_act)

        # Help Menu
        help_menu = menubar.addMenu("&Help")
        about_act = QAction("&About BandLab Sound Manager", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

        # Top Toolbar
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        toolbar.addAction(import_act)
        toolbar.addAction(rescan_act)
        toolbar.addSeparator()
        toolbar.addAction(analyzer_act)
        toolbar.addAction(consolidate_act)

    def _setup_signals(self):
        # Facet filter changes
        self.facet_widget.filter_changed.connect(self._on_filter_changed)

        # Table interactions
        self.table_view.sample_selected.connect(self._on_sample_selected)
        self.table_view.sample_double_clicked.connect(self._on_sample_double_clicked)
        self.table_view.remove_from_db_requested.connect(self._on_remove_from_db_requested)
        self.table_view.delete_trash_requested.connect(self._on_delete_trash_requested)
        self.table_view.analyze_sample_requested.connect(self._on_analyze_samples_requested)

        # Waveform seek (ratio: 0.0 - 1.0)
        self.waveform_widget.seek_requested.connect(self._on_waveform_seek_requested)

        # Audio player signals
        self.player.state_changed.connect(self._on_player_state_changed)
        self.player.progress_changed.connect(self._on_player_progress_changed)

    def _refresh_data(self):
        """Reloads facet options and table samples matching current filter."""
        current_filter = self.facet_widget.get_current_filter()
        samples = self.repo.search_samples(current_filter)
        self.table_model.set_samples(samples)

        # Populate facet values from database
        insts = self.repo.get_all_instruments()
        genres = self.repo.get_all_genres()
        self.facet_widget.update_facets(insts, genres)

        total = self.repo.get_total_count()
        self.status_label.setText(f"Showing {len(samples)} samples (Total: {total})")

    def _on_filter_changed(self, search_filter: SearchFilter):
        samples = self.repo.search_samples(search_filter)
        self.table_model.set_samples(samples)
        total = self.repo.get_total_count()
        self.status_label.setText(f"Showing {len(samples)} samples (Total: {total})")

    def _on_sample_selected(self, sample: SampleItem):
        """Loads waveform and auto-plays if enabled."""
        if not os.path.exists(sample.file_path):
            return

        try:
            # Load waveform peaks
            wave_data = self.waveform_cache.get_or_extract(sample.file_path)
            self.waveform_widget.set_waveform_data(wave_data)

            # Auto-play if enabled
            if self.autoplay_btn.isChecked():
                is_loop = (sample.sample_type == "Loop") if self.loop_btn.isChecked() else False
                self.player.play_sample(sample.file_path, is_loop=is_loop)
        except Exception as e:
            logger.error("Error on sample selection: %s", e)

    def _on_sample_double_clicked(self, sample: SampleItem):
        """Plays sample immediately."""
        if not os.path.exists(sample.file_path):
            QMessageBox.warning(self, "File Not Found", f"Cannot find audio file:\n{sample.file_path}")
            return

        try:
            wave_data = self.waveform_cache.get_or_extract(sample.file_path)
            self.waveform_widget.set_waveform_data(wave_data)

            is_loop = (sample.sample_type == "Loop") if self.loop_btn.isChecked() else False
            self.player.play_sample(sample.file_path, is_loop=is_loop, force_play=True)
        except Exception as e:
            logger.error("Error on sample double click: %s", e)

    def _on_play_pause_clicked(self):
        if self.player.state == PlaybackState.PLAYING:
            self.player.pause()
        elif self.player.state == PlaybackState.PAUSED:
            self.player.resume()
        else:
            selected = self.table_view.get_selected_samples()
            if selected:
                self._on_sample_double_clicked(selected[0])

    def _on_stop_clicked(self):
        self.player.stop()
        self.waveform_widget.set_playback_progress(0, self.player.duration_ms)

    def _on_autoplay_toggled(self, checked: bool):
        self.autoplay_btn.setText(f"Auto-Play: {'ON' if checked else 'OFF'}")
        self.player.set_auto_play(checked)

    def _on_loop_toggled(self, checked: bool):
        self.loop_btn.setText(f"Loop: {'ON' if checked else 'OFF'}")
        self.player.set_loop_playback(checked)

    def _on_volume_changed(self, val: int):
        self.player.set_volume(val / 100.0)

    def _on_player_state_changed(self, state: PlaybackState):
        if state == PlaybackState.PLAYING:
            self.play_btn.setText("⏸ Pause")
        else:
            self.play_btn.setText("▶ Play")

    def _on_player_progress_changed(self, pos_ms: int, dur_ms: int):
        self.waveform_widget.set_playback_progress(pos_ms, dur_ms)
        cur_sec = pos_ms // 1000
        dur_sec = dur_ms // 1000
        self.time_label.setText(f"{cur_sec//60:02d}:{cur_sec%60:02d} / {dur_sec//60:02d}:{dur_sec%60:02d}")

    def _on_waveform_seek_requested(self, ratio: float):
        self.player.seek_ratio(ratio)

    def _on_remove_from_db_requested(self, samples: List[SampleItem]):
        """BR-107 / BR-404: Removes samples from database only, preserving files on disk."""
        reply = QMessageBox.question(
            self,
            "Remove from Library",
            f"Are you sure you want to remove {len(samples)} sample(s) from the library?\n\n(Files will NOT be deleted from your disk)",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            for s in samples:
                if s.id:
                    self.repo.delete_sample_by_id(s.id)
            self._refresh_data()

    def _on_delete_trash_requested(self, samples: List[SampleItem]):
        """BR-107 / BR-404: Moves files to Windows Recycle Bin and deletes DB records."""
        reply = QMessageBox.warning(
            self,
            "Move to Recycle Bin",
            f"Are you sure you want to delete {len(samples)} sample(s)?\n\nFiles will be moved to the Windows Recycle Bin and removed from library.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            deleted_count = 0
            for s in samples:
                self.file_mgr.delete_physical_file(s.file_path, use_recycle_bin=True)
                if s.id:
                    self.repo.delete_sample_by_id(s.id)
                deleted_count += 1
            self._refresh_data()
            QMessageBox.information(self, "Deleted", f"Moved {deleted_count} file(s) to Recycle Bin.")

    def _on_analyze_samples_requested(self, samples: List[SampleItem]):
        # Lazy import to keep application startup instantaneous
        from src.ui.audio_analyzer_dialog import AudioAnalyzerDialog
        dlg = AudioAnalyzerDialog(samples=samples, repo=self.repo, file_mgr=self.file_mgr, parent=self)
        dlg.renamed_completed.connect(self._refresh_data)
        dlg.exec()

    def action_import_folder(self):
        """Prompts user to select a folder and imports audio files in background thread."""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Import Sound Samples")
        if not folder:
            return

        self.status_progress.setVisible(True)
        self.status_progress.setRange(0, 0)
        self.status_label.setText(f"Scanning & importing from: {folder}...")

        self._active_worker = ImportWorker(
            source_folder=folder,
            repo=self.repo,
            file_mgr=self.file_mgr,
            copy_mode=True,
            parent=self,
        )
        self._active_worker.progress.connect(self._on_import_progress)
        self._active_worker.finished.connect(self._on_import_finished)
        self._active_worker.error.connect(self._on_import_error)
        self._active_worker.start()

    def _on_import_progress(self, current: int, total: int, filename: str):
        self.status_progress.setRange(0, total)
        self.status_progress.setValue(current)
        self.status_label.setText(f"Importing ({current}/{total}): {filename}")

    def _on_import_finished(self, summary):
        self.status_progress.setVisible(False)
        self._refresh_data()
        QMessageBox.information(
            self,
            "Import Complete",
            f"Import finished!\n\n"
            f"• Scanned: {summary.total_files_scanned}\n"
            f"• Imported: {summary.imported_count}\n"
            f"• Renamed Duplicates: {summary.duplicate_renamed_count}\n"
            f"• Errors: {summary.errors_count}",
        )

    def _on_import_error(self, err_msg: str):
        self.status_progress.setVisible(False)
        QMessageBox.critical(self, "Import Error", err_msg)

    def action_rescan_library(self):
        """Scans for missing/deleted files and updates database."""
        self.status_progress.setVisible(True)
        self.status_progress.setRange(0, 0)
        self.status_label.setText("Rescanning library integrity...")

        self._rescan_worker = RescanWorker(repo=self.repo, file_mgr=self.file_mgr, parent=self)
        self._rescan_worker.finished.connect(self._on_rescan_finished)
        self._rescan_worker.error.connect(self._on_import_error)
        self._rescan_worker.start()

    def _on_rescan_finished(self, synced: int):
        self.status_progress.setVisible(False)
        self._refresh_data()
        self.status_label.setText(f"Rescan complete. Synced {synced} records.")

    def action_open_analyzer_dialog(self):
        """Opens Audio Analyzer dialog for all unknown/Other samples or selected samples."""
        selected = self.table_view.get_selected_samples()
        if not selected:
            # Fallback to all samples with Other/None attributes or all library samples
            selected = self.repo.get_all_samples()

        if not selected:
            QMessageBox.information(self, "No Samples", "No sound samples available in library to analyze.")
            return

        self._on_analyze_samples_requested(selected)

    def action_consolidate_duplicates(self):
        """Scans for duplicate files (_1, _2...) and consolidates them to the latest file."""
        duplicate_groups = self.repo.find_duplicate_groups()
        if not duplicate_groups:
            QMessageBox.information(
                self,
                "No Duplicates Found",
                "重複している音源ファイルは見つかりませんでした。\nライブラリは正常に整理されています。",
            )
            return

        total_obsolete = sum(len(g["obsolete_samples"]) for g in duplicate_groups)
        reply = QMessageBox.question(
            self,
            "Consolidate Duplicate Samples",
            f"{len(duplicate_groups)} 組の重複音源グループ（計 {total_obsolete} 個の古い重複ファイル）が見つかりました。\n\n"
            f"最も更新日時が新しいファイルを残し、古い重複ファイルを Windows のごみ箱へ安全に移動して整理しますか？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.status_progress.setVisible(True)
            self.status_progress.setRange(0, len(duplicate_groups))
            self.status_label.setText("重複音源を最新ファイルへ統合中...")

            self._consolidate_worker = ConsolidateDuplicatesWorker(self.repo, self.file_mgr, parent=self)
            self._consolidate_worker.progress.connect(self._on_consolidate_progress)
            self._consolidate_worker.finished.connect(self._on_consolidate_finished)
            self._consolidate_worker.error.connect(self._on_import_error)
            self._consolidate_worker.start()

    def _on_consolidate_progress(self, current: int, total: int, desc: str):
        self.status_progress.setRange(0, total)
        self.status_progress.setValue(current)
        self.status_label.setText(f"統合処理中 ({current}/{total}): {desc}")

    def _on_consolidate_finished(self, groups_consolidated: int, files_cleaned: int):
        self.status_progress.setVisible(False)
        self._refresh_data()
        QMessageBox.information(
            self,
            "Consolidation Complete",
            f"重複ファイルの統合が完了しました！\n\n"
            f"• 統合されたグループ: {groups_consolidated} 組\n"
            f"• 整理された古いファイル: {files_cleaned} 個（ごみ箱へ移動済み）",
        )

    def action_backup_database(self):
        """Takes an immediate snapshot backup of the database."""
        try:
            backup_path = self.repo.create_snapshot_backup()
            QMessageBox.information(
                self,
                "Backup Successful",
                f"Database backup saved to:\n{backup_path}",
            )
        except Exception as e:
            QMessageBox.critical(self, "Backup Failed", str(e))

    def _show_about(self):
        QMessageBox.about(
            self,
            "About BandLab Sound Manager",
            "<h3>BandLab Sound Sample Manager</h3>"
            "<p>A desktop sound sample manager tailored for Cakewalk by BandLab / Sonar DAW workflows.</p>"
            "<p><b>Key Features:</b></p>"
            "<ul>"
            "<li>Faceted Filter Search (Type, Instrument, Genre, Key, BPM)</li>"
            "<li>Direct Drag-and-Drop to DAW Audio Tracks</li>"
            "<li>Waveform Display & Instant Auto-Play / Looping</li>"
            "<li>Quantitative DSP Audio Analysis & Standardized Renamer</li>"
            "<li>Safe 2-Step Deletion (Windows Recycle Bin)</li>"
            "</ul>",
        )
