# Unit 4 NFR Requirements: Tech Stack Decisions (`tech-stack-decisions.md`)

## 1. Technology Selections for Unit 4

### 1.1 Desktop GUI Framework: `PyQt6`
- **Components**: `QMainWindow`, `QTableView`, `QAbstractTableModel`, `QTreeView`, `QSplitter`, `QProgressBar`, `QDialog`, `QMessageBox`, `QThread`
- **Rationale**:
  - 高度なテーブル仮想化（`QTableView` + `QAbstractTableModel`）により、大量データでも超低メモリかつ高速描画。
  - Qt標準ドラッグ＆ドロップ（`QDrag` / `QMimeData`）によるWindowsネイティブDAW（Cakewalk / Sonar / Studio One 等）連携。
  - Unit 3 の `AudioPlayerService` / `WaveformWidget` とのシームレスな Qt シグナル・スロット結合。

### 1.2 Multi-Threading: `PyQt6.QtCore.QThread` + `pyqtSignal`
- **Rationale**:
  - GUIスレッドと完全に分離されたバックグラウンドスレッドで、Unit 1 のインポート処理や Unit 2 のバッチ音声解析を実行。
  - Qtシグナルによりスレッドセーフに進捗（`progress(int current, int total, str filename)`）をUIに伝達。

### 1.3 Trash Deletion: `send2trash`
- **Rationale**:
  - Windowsのごみ箱へファイルを安全に移動（BR-107 / BR-404）し、誤削除時の復元性を担保。

### 1.4 Test Framework: `pytest-qt`, `unittest`
- **Rationale**:
  - `QAbstractTableModel` のデータバインディング、フィルタ同期、ダイアログ操作の自動単体テスト。
