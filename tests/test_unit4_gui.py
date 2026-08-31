"""Automated unit and integration tests for Unit 4: Desktop GUI & DAW Integration."""
import os
import sys
import wave
import struct
import tempfile
import pytest
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QModelIndex

from src.core.config import LibraryConfig
from src.core.models import SampleItem, SearchFilter
from src.database.db_manager import DatabaseManager
from src.database.repository import SampleRepository
from src.storage.file_manager import LibraryFileManager
from src.audio.player_service import AudioPlayerService
from src.audio.waveform_cache import WaveformCache
from src.ui.sample_table_model import SampleTableModel
from src.ui.sample_table_view import SampleTableView
from src.ui.facet_filter_widget import FacetFilterWidget
from src.ui.audio_analyzer_dialog import AudioAnalyzerDialog
from src.ui.main_window import MainWindow
from src.ui.workers import ImportWorker, BatchAnalyzeWorker


@pytest.fixture(scope="session")
def qapp():
    """Session-wide QApplication instance."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def temp_env():
    """Sets up an isolated temporary workspace for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        cfg = LibraryConfig(library_root=str(tmp_path / "SoundLibrary"), copy_mode="copy")
        file_mgr = LibraryFileManager(cfg)
        db_mgr = DatabaseManager(str(cfg.database_path))
        repo = SampleRepository(db_mgr)
        yield {
            "root": tmp_path,
            "config": cfg,
            "file_mgr": file_mgr,
            "db_mgr": db_mgr,
            "repo": repo,
        }
        db_mgr.close_connection()


def create_test_wav(file_path: Path, duration_sec: float = 1.0, sample_rate: int = 44100):
    """Generates a dummy 16-bit PCM WAV file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    num_samples = int(duration_sec * sample_rate)
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        frames = bytearray()
        for i in range(num_samples):
            val = int(16000 * (1 if (i // 50) % 2 == 0 else -1))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)


class TestSampleTableModel:
    """Tests for SampleTableModel virtualized table model."""

    def test_model_data_and_columns(self, qapp):
        sample = SampleItem(
            id=1,
            file_path="C:/music/Kick_120BPM_C.wav",
            file_name="Kick_120BPM_C.wav",
            file_size=1024,
            sample_type="Loop",
            instrument="Drum",
            genre="Trap",
            bpm=120.0,
            key_root="C",
            key_scale="major",
            creator="BandLab",
            duration_sec=4.5,
        )

        model = SampleTableModel([sample])
        assert model.rowCount() == 1
        assert model.columnCount() == len(SampleTableModel.COLUMNS)

        # Name
        idx0 = model.index(0, 0)
        assert model.data(idx0, Qt.ItemDataRole.DisplayRole) == "Kick_120BPM_C.wav"

        # Type
        idx1 = model.index(0, 1)
        assert model.data(idx1, Qt.ItemDataRole.DisplayRole) == "Loop"

        # Instrument
        idx2 = model.index(0, 2)
        assert model.data(idx2, Qt.ItemDataRole.DisplayRole) == "Drum"

        # Genre
        idx3 = model.index(0, 3)
        assert model.data(idx3, Qt.ItemDataRole.DisplayRole) == "Trap"

        # BPM
        idx4 = model.index(0, 4)
        assert model.data(idx4, Qt.ItemDataRole.DisplayRole) == "120"

        # Key
        idx5 = model.index(0, 5)
        assert model.data(idx5, Qt.ItemDataRole.DisplayRole) == "C major"

        # Duration
        idx7 = model.index(0, 7)
        assert "00:04" in model.data(idx7, Qt.ItemDataRole.DisplayRole)

    def test_model_mime_data_drag_drop(self, qapp):
        sample = SampleItem(
            id=1,
            file_path="C:/music/Sample.wav",
            file_name="Sample.wav",
        )
        model = SampleTableModel([sample])
        idx = model.index(0, 0)
        mime = model.mimeData([idx])

        assert mime.hasUrls()
        urls = mime.urls()
        assert len(urls) == 1
        assert os.path.normpath(urls[0].toLocalFile()) == os.path.normpath("C:/music/Sample.wav")
        assert os.path.normpath("C:/music/Sample.wav") in mime.text()


class TestFacetFilterWidget:
    """Tests for FacetFilterWidget controls and signal emission."""

    def test_filter_controls_and_reset(self, qapp):
        widget = FacetFilterWidget()

        # Set search input & checkboxes
        widget.search_input.blockSignals(True)
        widget.search_input.setText("guitar")
        widget.search_input.blockSignals(False)
        widget.type_loop_cb.setChecked(True)
        widget.bpm_min_spin.setValue(100)
        widget.bpm_max_spin.setValue(140)

        filt = widget.get_current_filter()
        assert filt.query_text == "guitar"
        assert filt.sample_types == ["Loop"]
        assert filt.bpm_min == 100.0
        assert filt.bpm_max == 140.0

        # Reset
        widget.reset_filters()
        filt_reset = widget.get_current_filter()
        assert filt_reset.query_text is None
        assert filt_reset.sample_types == []
        assert filt_reset.bpm_min is None
        assert filt_reset.bpm_max is None

    def test_filter_individual_section_resets(self, qapp):
        widget = FacetFilterWidget()

        # 1. Type reset
        widget.type_loop_cb.setChecked(True)
        assert widget.get_current_filter().sample_types == ["Loop"]
        widget.reset_type_filter()
        assert widget.get_current_filter().sample_types == []

        # 2. Key reset
        widget.key_list.item(0).setSelected(True)
        assert len(widget.get_current_filter().key_roots) == 1
        widget.reset_key_filter()
        assert len(widget.get_current_filter().key_roots) == 0

        # 3. BPM reset
        widget.bpm_min_spin.setValue(120)
        widget.bpm_max_spin.setValue(140)
        assert widget.get_current_filter().bpm_min == 120.0
        widget.reset_bpm_filter()
        assert widget.get_current_filter().bpm_min is None

        # 4. Search reset
        widget.search_input.setText("test")
        assert widget.get_current_filter().query_text == "test"
        widget.reset_search()
        assert widget.get_current_filter().query_text is None


class TestAsyncWorkers:
    """Tests for ImportWorker and BatchAnalyzeWorker."""

    def test_import_worker_execution(self, qapp, temp_env):
        # Create dummy source folder with 2 samples
        src_folder = temp_env["root"] / "src_samples"
        src_folder.mkdir()
        create_test_wav(src_folder / "Lead_120BPM_C.wav", duration_sec=0.5)
        create_test_wav(src_folder / "Kick_Punch.wav", duration_sec=0.5)

        worker = ImportWorker(
            source_folder=str(src_folder),
            repo=temp_env["repo"],
            file_mgr=temp_env["file_mgr"],
            copy_mode=True,
        )

        results = []
        worker.finished.connect(lambda summary: results.append(summary))

        # Run synchronously via run() for testing
        worker.run()

        assert len(results) == 1
        summary = results[0]
        assert summary.total_files_scanned == 2
        assert summary.imported_count == 2
        assert temp_env["repo"].get_total_count() == 2


class TestAudioAnalyzerDialog:
    """Tests for AudioAnalyzerDialog preview and rename operations."""

    def test_dialog_populate_and_rename(self, qapp, temp_env):
        # Create physical sample
        sample_path = temp_env["config"].library_dir / "Oneshot" / "Mystery_Audio.wav"
        create_test_wav(sample_path, duration_sec=1.0)

        item = SampleItem(
            file_path=str(sample_path),
            file_name="Mystery_Audio.wav",
            sample_type="Oneshot",
        )
        item_id = temp_env["repo"].insert_sample(item)
        item.id = item_id

        dialog = AudioAnalyzerDialog(
            samples=[item],
            repo=temp_env["repo"],
            file_mgr=temp_env["file_mgr"],
        )

        assert dialog.table.rowCount() == 1
        assert dialog.table.item(0, 1).text() == "Mystery_Audio.wav"

        # Execute analysis synchronously
        worker = BatchAnalyzeWorker(file_paths=[item.file_path])
        results = []
        worker.finished.connect(lambda res: results.extend(res))
        worker.run()
        dialog._on_analysis_finished(results)

        assert len(dialog.preview_items) == 1
        # Trigger renames without blocking message box
        dialog._apply_renames(show_msg=False)

        # Verify DB updated
        updated = temp_env["repo"].get_sample_by_id(item_id)
        assert updated is not None
        assert updated.file_name.endswith(".wav")


class TestMainWindowIntegration:
    """Tests for MainWindow UI assembly and data flow."""

    def test_main_window_assembly(self, qapp, temp_env):
        # Insert sample
        sample_path = temp_env["config"].library_dir / "Loop" / "Guitar_120BPM_C.wav"
        create_test_wav(sample_path, duration_sec=1.0)
        item = SampleItem(
            file_path=str(sample_path),
            file_name="Guitar_120BPM_C.wav",
            sample_type="Loop",
            instrument="Guitar",
            genre="Pop",
            bpm=120.0,
            key_root="C",
            key_scale="major",
        )
        temp_env["repo"].insert_sample(item)

        player = AudioPlayerService(headless=True)
        player.set_auto_play(False)
        cache = WaveformCache()

        window = MainWindow(
            config=temp_env["config"],
            repo=temp_env["repo"],
            file_mgr=temp_env["file_mgr"],
            player_service=player,
            waveform_cache=cache,
        )

        assert window.table_model.rowCount() == 1
        assert window.facet_widget.inst_list.count() == 1

        # Test sample selection without crash
        window._on_sample_selected(item)
        assert window.waveform_widget._waveform_data is not None

        # Test waveform seek
        window._on_waveform_seek_requested(0.5)

        # Test filter search
        filt = SearchFilter(query_text="Guitar")
        window._on_filter_changed(filt)
        assert window.table_model.rowCount() == 1

        filt_none = SearchFilter(query_text="NonExistent")
        window._on_filter_changed(filt_none)
        assert window.table_model.rowCount() == 0

        window.close()
