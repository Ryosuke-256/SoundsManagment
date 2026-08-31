"""Application entry point for BandLab Sound Sample Manager."""
import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.core.config import LibraryConfig
from src.database.db_manager import DatabaseManager
from src.database.repository import SampleRepository
from src.storage.file_manager import LibraryFileManager
from src.audio.player_service import AudioPlayerService
from src.audio.waveform_cache import WaveformCache
from src.ui.main_window import MainWindow

DARK_THEME_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #1a1a24;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 9.5pt;
}

QTableView {
    background-color: #121218;
    alternate-background-color: #181822;
    gridline-color: #2a2a38;
    selection-background-color: #0288d1;
    selection-color: #ffffff;
    border: 1px solid #2a2a38;
    border-radius: 4px;
}

QHeaderView::section {
    background-color: #242434;
    color: #00d2ff;
    font-weight: bold;
    padding: 5px;
    border: 1px solid #2a2a38;
}

QGroupBox {
    border: 1px solid #2e2e42;
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 10px;
    font-weight: bold;
    color: #b0bec5;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

QLineEdit, QSpinBox {
    background-color: #242434;
    color: #ffffff;
    border: 1px solid #3d3d56;
    border-radius: 4px;
    padding: 4px 8px;
}

QLineEdit:focus, QSpinBox:focus {
    border: 1px solid #00d2ff;
}

QPushButton {
    background-color: #2a2a3e;
    color: #ffffff;
    border: 1px solid #3d3d56;
    border-radius: 4px;
    padding: 5px 12px;
}

QPushButton:hover {
    background-color: #35354e;
    border: 1px solid #00d2ff;
}

QPushButton:pressed {
    background-color: #00838f;
}

QListWidget {
    background-color: #121218;
    border: 1px solid #2e2e42;
    border-radius: 4px;
}

QListWidget::item:selected {
    background-color: #0288d1;
    color: white;
}

QScrollBar:vertical {
    border: none;
    background: #121218;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #3d3d56;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #00d2ff;
}

QProgressBar {
    background-color: #242434;
    border: 1px solid #3d3d56;
    border-radius: 4px;
    text-align: center;
    color: white;
}

QProgressBar::chunk {
    background-color: #00d2ff;
    border-radius: 3px;
}

QSlider::groove:horizontal {
    height: 6px;
    background: #242434;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #00d2ff;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #ffffff;
    width: 14px;
    margin-top: -4px;
    margin-bottom: -4px;
    border-radius: 7px;
}
"""


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_THEME_QSS)

    # Initialize library configuration & storage hierarchy
    config = LibraryConfig()
    file_mgr = LibraryFileManager(config)

    # Initialize SQLite database manager & repository
    db_mgr = DatabaseManager(str(config.database_path))
    repo = SampleRepository(db_mgr)

    # Initialize Audio engine & waveform cache
    player_service = AudioPlayerService()
    waveform_cache = WaveformCache()

    # Create & display main window
    window = MainWindow(
        config=config,
        repo=repo,
        file_mgr=file_mgr,
        player_service=player_service,
        waveform_cache=waveform_cache,
    )
    window.show()

    exit_code = app.exec()

    # Graceful cleanup
    player_service.stop()
    db_mgr.close_connection()

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
