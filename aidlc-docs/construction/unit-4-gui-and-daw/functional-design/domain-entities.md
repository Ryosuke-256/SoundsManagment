# Unit 4 Functional Design: Domain Entities (`domain-entities.md`)

## 1. GUI Domain Entities & Models

### 1.1 `SampleTableModel`
PyQt6 `QAbstractTableModel` を継承し、高速なテーブル描画・ソート・選択・ドラッグ操作を仲介するデータモデル。
- **Columns**:
  1. `Title` (ファイル名 / サンプル名)
  2. `Type` (Loop / Oneshot / Other)
  3. `Instrument` (Guitar, Synth, Drum, Bass, Other, etc.)
  4. `Genre` (Trap, Lofi, EDM, Pop, Other, etc.)
  5. `BPM` (数値または未設定)
  6. `Key` (C, Am, F#m, Other, etc.)
  7. `Creator` (BandLab, User, etc.)
  8. `Duration` (mm:ss 形式)
- **Roles**:
  - `Qt.ItemDataRole.DisplayRole`: テキスト表示
  - `Qt.ItemDataRole.UserRole`: `SampleRecord` オブジェクトまたは `file_path`
  - `Qt.ItemDataRole.TextAlignmentRole`: 数値・列ごとのアライメント調整

### 1.2 `FilterState` (GUI Filter Context)
サイドバーのファセット検索条件および検索バーの入力状態をカプセル化。
- **Attributes**:
  - `search_text: str` (キーワード検索)
  - `sample_types: Set[str]` (例: `{"Loop", "Oneshot"}`)
  - `instruments: Set[str]` (選択された楽器タグ)
  - `genres: Set[str]` (選択されたジャンルタグ)
  - `keys: Set[str]` (選択された調性タグ)
  - `bpm_min: Optional[float]`, `bpm_max: Optional[float]` (BPM範囲)
  - `favorite_only: bool` (お気に入り絞り込み)

### 1.3 `DragDropPayload`
音源行からDAWへ転送されるMIMEデータペイロード。
- **MIME Types**:
  - `text/uri-list`: `QUrl.fromLocalFile(abs_file_path)` (Cakewalk by BandLab, Sonar, Studio One, Reaper, Ableton Live 互換)
  - `application/x-sound-sample-id`: アプリ内ドラッグ追跡用ID

### 1.4 `AnalyzerDialogModel` (Story 2.4 / FR-2.5)
プロパティ不明音源の解析・リネームダイアログ用テーブルモデル。
- **Item Fields**:
  - `file_path: str`
  - `original_name: str`
  - `detected_bpm: Optional[float]`
  - `detected_key: Optional[str]`
  - `suggested_name: str`
  - `is_selected: bool`
  - `status: str` ("Ready", "Analyzing", "Renamed", "Failed")
