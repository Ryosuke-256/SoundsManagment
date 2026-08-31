# Unit 4 NFR Design: Logical Components (`logical-components.md`)

## 1. Logical Component Architecture

Unit 4 における GUI および DAW 連携の論理コンポーネント構成：

```
+-------------------------------------------------------------------------------+
| [Unit 4: Desktop GUI & DAW Drag-and-Drop Integration]                         |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | MainWindow (PyQt6 QMainWindow)                                          |  |
|  |  - Coordinates FacetTree, SampleTable, WaveformWidget, & AudioPlayer   |  |
|  |  - MenuBar & ToolBar (Import, Re-index, Auto-Play, Loop, Volume)       |  |
|  |  - StatusBar with async task progress and message notifications         |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | FacetFilterWidget (PyQt6 QWidget / QTreeWidget)                         |  |
|  |  - Categorized tag filters (Type, Instrument, Genre, Key, BPM Slider)  |  |
|  |  - Emits filterChanged(FilterState) on any tag selection change         |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | SampleTableView & SampleTableModel (PyQt6 QTableView / QAbstractModel) |  |
|  |  - Virtualized rendering with column sorting & multi-selection         |  |
|  |  - OLE / QDrag initiate for Cakewalk/Sonar DAW track drop               |  |
|  |  - ContextMenu for Safe 2-Step Deletion (BR-107 / BR-404)               |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | AudioAnalyzerDialog (PyQt6 QDialog) (Story 2.4 / FR-2.5)                |  |
|  |  - Batch audio signal analysis (BPM & Key) progress table              |  |
|  |  - Diff preview of suggested file renames & atomic DB sync update      |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | Async Workers (ImportWorker, BatchAnalyzeWorker, RescanWorker)         |  |
|  |  - QThread based non-blocking background workers with cancelation       |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 2. Component Detailed Specifications

### 2.1 `SampleTableModel`
- **File**: `src/ui/sample_table_model.py`
- **Responsibility**: `SampleRecord` のリストを `QTableView` 向けにバインド。ソート、行選択、データ提供。

### 2.2 `SampleTableView`
- **File**: `src/ui/sample_table_view.py`
- **Responsibility**: DAWドラッグ＆ドロップ（`startDrag`）、コンテキストメニュー（2段階削除、リネームダイアログ起動、エクスプローラーで表示）。

### 2.3 `FacetFilterWidget`
- **File**: `src/ui/facet_filter_widget.py`
- **Responsibility**: タイプ/楽器/ジャンル/キー/BPMのファセット検索サイドバー。

### 2.4 `AudioAnalyzerDialog`
- **File**: `src/ui/audio_analyzer_dialog.py`
- **Responsibility**: Story 2.4 音声解析＆自動リネーム用プレビューDiffダイアログ。

### 2.5 `MainWindow`
- **File**: `src/ui/main_window.py`
- **Responsibility**: メインウィンドウ、UIレイアウト結合、サービス間シグナル・スロット統括。
