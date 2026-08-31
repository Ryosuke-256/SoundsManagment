"""Faceted search sidebar widget for sound sample library filtering with individual section reset buttons."""
from typing import Dict, List, Optional
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QScrollArea,
    QSpinBox,
    QPushButton,
    QFrame,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)

from src.core.models import SearchFilter


class FacetFilterWidget(QWidget):
    """Sidebar widget providing compact faceted filter controls (Type, Key, BPM, Instrument, Genre)."""

    filter_changed = pyqtSignal(SearchFilter)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self._emit_filter)

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(6)

        # Top Header
        top_header_layout = QHBoxLayout()
        header_label = QLabel("LIBRARY FILTERS")
        header_label.setStyleSheet("font-weight: bold; color: #00d2ff; font-size: 11pt; padding: 2px;")
        top_header_layout.addWidget(header_label, stretch=1)

        main_layout.addLayout(top_header_layout)

        # Keyword Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search filename or tags...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        main_layout.addWidget(self.search_input)

        # Scroll area for facet sections
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        content = QWidget()
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(2, 2, 2, 2)
        self.content_layout.setSpacing(10)

        # 1. Type Facet (Loop / Oneshot)
        type_section = QWidget()
        type_vbox = QVBoxLayout(type_section)
        type_vbox.setContentsMargins(0, 0, 0, 0)
        type_vbox.setSpacing(3)
        type_header = self._create_section_header("Sample Type", self.reset_type_filter)
        type_vbox.addWidget(type_header)

        type_cb_layout = QHBoxLayout()
        self.type_loop_cb = QCheckBox("Loop")
        self.type_oneshot_cb = QCheckBox("Oneshot")
        for cb in (self.type_loop_cb, self.type_oneshot_cb):
            cb.stateChanged.connect(self._on_filter_control_changed)
            type_cb_layout.addWidget(cb)
        type_vbox.addLayout(type_cb_layout)
        self.content_layout.addWidget(type_section)

        # 2. Key Root Facet
        key_section = QWidget()
        key_vbox = QVBoxLayout(key_section)
        key_vbox.setContentsMargins(0, 0, 0, 0)
        key_vbox.setSpacing(3)
        key_header = self._create_section_header("Musical Key", self.reset_key_filter)
        key_vbox.addWidget(key_header)

        self.key_list = QListWidget()
        self.key_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.key_list.setMaximumHeight(110)
        self.key_list.itemSelectionChanged.connect(self._on_filter_control_changed)
        for k in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
            self.key_list.addItem(k)
        key_vbox.addWidget(self.key_list)
        self.content_layout.addWidget(key_section)

        # 3. BPM Range Facet
        bpm_section = QWidget()
        bpm_vbox = QVBoxLayout(bpm_section)
        bpm_vbox.setContentsMargins(0, 0, 0, 0)
        bpm_vbox.setSpacing(3)
        bpm_header = self._create_section_header("BPM Range", self.reset_bpm_filter)
        bpm_vbox.addWidget(bpm_header)

        bpm_h_layout = QHBoxLayout()
        self.bpm_min_spin = QSpinBox()
        self.bpm_min_spin.setRange(0, 300)
        self.bpm_min_spin.setValue(0)
        self.bpm_min_spin.setSpecialValueText("Min")
        self.bpm_min_spin.valueChanged.connect(self._on_filter_control_changed)

        self.bpm_max_spin = QSpinBox()
        self.bpm_max_spin.setRange(0, 300)
        self.bpm_max_spin.setValue(0)
        self.bpm_max_spin.setSpecialValueText("Max")
        self.bpm_max_spin.valueChanged.connect(self._on_filter_control_changed)

        bpm_h_layout.addWidget(self.bpm_min_spin)
        bpm_h_layout.addWidget(QLabel("-"))
        bpm_h_layout.addWidget(self.bpm_max_spin)
        bpm_vbox.addLayout(bpm_h_layout)
        self.content_layout.addWidget(bpm_section)

        # 4. Instrument Facet (Includes 'Other' in list)
        inst_section = QWidget()
        inst_vbox = QVBoxLayout(inst_section)
        inst_vbox.setContentsMargins(0, 0, 0, 0)
        inst_vbox.setSpacing(3)
        inst_header = self._create_section_header("Instruments", self.reset_instrument_filter)
        inst_vbox.addWidget(inst_header)

        self.inst_list = QListWidget()
        self.inst_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.inst_list.setMaximumHeight(130)
        self.inst_list.itemSelectionChanged.connect(self._on_filter_control_changed)
        inst_vbox.addWidget(self.inst_list)
        self.content_layout.addWidget(inst_section)

        # 5. Genre / Pack Facet (Includes 'Other' in list)
        genre_section = QWidget()
        genre_vbox = QVBoxLayout(genre_section)
        genre_vbox.setContentsMargins(0, 0, 0, 0)
        genre_vbox.setSpacing(3)
        genre_header = self._create_section_header("Genres / Packs", self.reset_genre_filter)
        genre_vbox.addWidget(genre_header)

        self.genre_list = QListWidget()
        self.genre_list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.genre_list.setMaximumHeight(130)
        self.genre_list.itemSelectionChanged.connect(self._on_filter_control_changed)
        genre_vbox.addWidget(self.genre_list)
        self.content_layout.addWidget(genre_section)

        self.content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Global Reset All Button
        self.reset_btn = QPushButton("↺ Reset All Filters")
        self.reset_btn.setStyleSheet(
            "QPushButton { background-color: #2a2a3e; border: 1px solid #3d3d56; padding: 6px; font-weight: bold; border-radius: 4px; } "
            "QPushButton:hover { background-color: #3d3d5c; border-color: #00d2ff; color: #00d2ff; }"
        )
        self.reset_btn.clicked.connect(self.reset_filters)
        main_layout.addWidget(self.reset_btn)

    def _create_section_header(self, title: str, reset_callback) -> QWidget:
        """Creates section header label with an individual reset button."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 2)
        layout.setSpacing(4)

        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; color: #b0bec5; font-size: 9.5pt;")
        layout.addWidget(lbl, stretch=1)

        btn = QPushButton("↺")
        btn.setToolTip(f"Reset {title}")
        btn.setFixedSize(22, 20)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton { background-color: #242434; border: 1px solid #38384f; color: #90a4ae; font-size: 10pt; font-weight: bold; border-radius: 3px; } "
            "QPushButton:hover { background-color: #32324a; color: #00d2ff; border-color: #00d2ff; } "
            "QPushButton:pressed { background-color: #0288d1; color: #ffffff; }"
        )
        btn.clicked.connect(reset_callback)
        layout.addWidget(btn)
        return container

    def _on_search_text_changed(self):
        self._search_timer.start()

    def _on_filter_control_changed(self):
        self._emit_filter()

    def get_current_filter(self) -> SearchFilter:
        """Constructs SearchFilter object from active UI controls."""
        sample_types = []
        if self.type_loop_cb.isChecked():
            sample_types.append("Loop")
        if self.type_oneshot_cb.isChecked():
            sample_types.append("Oneshot")

        selected_keys = [item.text() for item in self.key_list.selectedItems()]
        selected_insts = [item.text() for item in self.inst_list.selectedItems()]
        selected_genres = [item.text() for item in self.genre_list.selectedItems()]

        bpm_min = float(self.bpm_min_spin.value()) if self.bpm_min_spin.value() > 0 else None
        bpm_max = float(self.bpm_max_spin.value()) if self.bpm_max_spin.value() > 0 else None

        query_text = self.search_input.text().strip() or None

        return SearchFilter(
            query_text=query_text,
            sample_types=sample_types,
            instruments=selected_insts,
            genres=selected_genres,
            key_roots=selected_keys,
            bpm_min=bpm_min,
            bpm_max=bpm_max,
        )

    def _emit_filter(self):
        filt = self.get_current_filter()
        self.filter_changed.emit(filt)

    def reset_search(self):
        """Resets search query text."""
        self._search_timer.stop()
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._emit_filter()

    def reset_type_filter(self):
        """Resets Type filter selection."""
        self.type_loop_cb.blockSignals(True)
        self.type_oneshot_cb.blockSignals(True)
        self.type_loop_cb.setChecked(False)
        self.type_oneshot_cb.setChecked(False)
        self.type_loop_cb.blockSignals(False)
        self.type_oneshot_cb.blockSignals(False)
        self._emit_filter()

    def reset_key_filter(self):
        """Resets Key filter selection."""
        self.key_list.blockSignals(True)
        self.key_list.clearSelection()
        self.key_list.blockSignals(False)
        self._emit_filter()

    def reset_bpm_filter(self):
        """Resets BPM range spinboxes."""
        self.bpm_min_spin.blockSignals(True)
        self.bpm_max_spin.blockSignals(True)
        self.bpm_min_spin.setValue(0)
        self.bpm_max_spin.setValue(0)
        self.bpm_min_spin.blockSignals(False)
        self.bpm_max_spin.blockSignals(False)
        self._emit_filter()

    def reset_instrument_filter(self):
        """Resets Instrument filter selection."""
        self.inst_list.blockSignals(True)
        self.inst_list.clearSelection()
        self.inst_list.blockSignals(False)
        self._emit_filter()

    def reset_genre_filter(self):
        """Resets Genre filter selection."""
        self.genre_list.blockSignals(True)
        self.genre_list.clearSelection()
        self.genre_list.blockSignals(False)
        self._emit_filter()

    def reset_filters(self):
        """Clears all search inputs and tag selections."""
        self._search_timer.stop()
        self.search_input.blockSignals(True)
        self.type_loop_cb.blockSignals(True)
        self.type_oneshot_cb.blockSignals(True)
        self.key_list.blockSignals(True)
        self.inst_list.blockSignals(True)
        self.genre_list.blockSignals(True)
        self.bpm_min_spin.blockSignals(True)
        self.bpm_max_spin.blockSignals(True)

        self.search_input.clear()
        self.type_loop_cb.setChecked(False)
        self.type_oneshot_cb.setChecked(False)
        self.key_list.clearSelection()
        self.inst_list.clearSelection()
        self.genre_list.clearSelection()
        self.bpm_min_spin.setValue(0)
        self.bpm_max_spin.setValue(0)

        self.search_input.blockSignals(False)
        self.type_loop_cb.blockSignals(False)
        self.type_oneshot_cb.blockSignals(False)
        self.key_list.blockSignals(False)
        self.inst_list.blockSignals(False)
        self.genre_list.blockSignals(False)
        self.bpm_min_spin.blockSignals(False)
        self.bpm_max_spin.blockSignals(False)

        self._emit_filter()

    def update_facets(self, instruments: List[str], genres: List[str]):
        """Populates dynamic instrument and genre facet lists while preserving selections and supporting 'Other'."""
        sel_insts = set(item.text() for item in self.inst_list.selectedItems())
        sel_genres = set(item.text() for item in self.genre_list.selectedItems())

        # Expand comma-separated instruments into individual items
        individual_insts = set()
        has_other_inst = False
        for inst_str in instruments:
            if inst_str:
                for part in inst_str.split(","):
                    clean = part.strip()
                    if clean:
                        if clean == "Other":
                            has_other_inst = True
                        else:
                            individual_insts.add(clean)

        self.inst_list.blockSignals(True)
        self.inst_list.clear()

        # Place known instruments in alphabetical order
        for inst in sorted(individual_insts):
            item = QListWidgetItem(inst)
            self.inst_list.addItem(item)
            if inst in sel_insts:
                item.setSelected(True)

        # Append 'Other' option at the end if present or by default
        if has_other_inst or True:
            other_item = QListWidgetItem("Other")
            self.inst_list.addItem(other_item)
            if "Other" in sel_insts:
                other_item.setSelected(True)

        self.inst_list.blockSignals(False)

        # Genres
        genre_set = set()
        has_other_genre = False
        for gen in genres:
            if gen:
                clean = gen.strip()
                if clean:
                    if clean == "Other":
                        has_other_genre = True
                    else:
                        genre_set.add(clean)

        self.genre_list.blockSignals(True)
        self.genre_list.clear()

        for gen in sorted(genre_set):
            item = QListWidgetItem(gen)
            self.genre_list.addItem(item)
            if gen in sel_genres:
                item.setSelected(True)

        if has_other_genre or True:
            other_gen_item = QListWidgetItem("Other")
            self.genre_list.addItem(other_gen_item)
            if "Other" in sel_genres:
                other_gen_item.setSelected(True)

        self.genre_list.blockSignals(False)
