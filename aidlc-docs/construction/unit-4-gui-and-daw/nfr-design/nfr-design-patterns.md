# Unit 4 NFR Design: Non-Functional Design Patterns (`nfr-design-patterns.md`)

## 1. Architectural Patterns

### 1.1 Clean Model-View Separation Pattern
- **Problem**: GUI ウィジェット内で直接データベースクエリや音声解析を実行すると、UI がフリーズしテストが困難になる。
- **Pattern**:
  - `SampleTableModel`（`QAbstractTableModel` 継承）が `SampleRepository` から取得したデータ行をカプセル化。
  - `MainWindow` は各ウィジェット（検索ツリー、テーブル、波形プレイヤー、ツールバー）とバックエンドサービス（`AudioPlayerService`, `FileManager`, `SampleRepository`）をシグナル・スロットで疎結合に調停。

---

## 2. Concurrency & Worker Patterns (RESILIENCY-10)

### 2.1 `QThread` Async Worker Pattern with Cancelation
- **Problem**: 1,000 ファイル以上のフォルダインポートやバッチ音声解析を同期実行すると、UI メインスレッドがフリーズして「応答なし」状態になる。
- **Pattern**:
  ```python
  class ImportWorker(QThread):
      progress = pyqtSignal(int, int, str)  # current, total, filename
      finished = pyqtSignal(int)            # total imported
      error = pyqtSignal(str)

      def __init__(self, folder_path: str, repo: SampleRepository, file_mgr: FileManager):
          super().__init__()
          self.folder_path = folder_path
          self.repo = repo
          self.file_mgr = file_mgr
          self._is_cancelled = False

      def cancel(self):
          self._is_cancelled = True

      def run(self):
          # Scan & import loop with self._is_cancelled checks
          ...
  ```
- **Benefits**: UI は常に 60 FPS で応答し、ユーザーは必要に応じて処理を中断可能。

---

## 3. Integration & Interaction Patterns

### 3.1 Pre-Flight Drag Validation Pattern
- **Problem**: 削除済みまたは移動済みのファイルを DAW にドラッグした場合、DAW 側でクリップ読み込みエラーやクラッシュが発生する。
- **Pattern**:
  - `SampleTableView` の `startDrag` 実行直前に `os.path.isfile(file_path)` を検証。
  - ファイルが存在しない場合はドラッグセッションを即座に破棄し、ステータスバーまたはツールチップに「File not found: {path}」を表示。
