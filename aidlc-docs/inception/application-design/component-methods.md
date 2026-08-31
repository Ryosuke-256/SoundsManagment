# Application Design: Component Methods Specification (component-methods.md)

## 1. Overview
各コンポーネントの主要メソッドのシグネチャ、引数、戻り値、および責務を定義します。（詳細なビジネスロジック・アルゴリズムはCONSTRUCTIONフェーズのFunctional Designにて定義）

---

## 2. Core & Database Layer

### `DatabaseManager`
- `initialize_database(db_path: str = None) -> sqlite3.Connection`:
  - DBスキーマの作成、テーブルおよびインデックス構築、WALモードの設定を実行。
- `perform_integrity_check() -> bool`:
  - `PRAGMA integrity_check` を実行し、DBの整合性を検証。
- `create_backup(backup_dir: str = None, max_generations: int = 5) -> str`:
  - 現在のDBファイルをバックアップフォルダへスナップショットコピーし、古い世代をローテーション削除。

### `SampleRepository`
- `insert_sample(sample: SampleItem) -> int`:
  - 新規音源レコードを追加し、割り当てられたIDを返却。
- `insert_samples_batch(samples: List[SampleItem]) -> int`:
  - 複数音源レコードを単一トランザクションで一括登録。
- `update_sample(sample: SampleItem) -> bool`:
  - 音源のメタデータ（タグ、BPM、Key、楽器等）を更新。
- `delete_sample(sample_id: int) -> bool`:
  - 指定IDのレコードを削除。
- `search_samples(filter_params: SearchFilter) -> List[SampleItem]`:
  - Type, Instrument, Genre, Key, BPM範囲, Creator, フリーワード、ソート順（カラム, 昇順/降順）に基づく高速検索クエリを実行。
- `get_facet_counts() -> Dict[str, Dict[str, int]]`:
  - 各属性（Type, Instrument, Genre, Key, Creator, Other）に属する音源数を集計して返却。

### `LibraryFileManager`
- `setup_library_structure(root_path: str) -> None`:
  - `Library/Loop/`, `Library/Oneshot/`, `Library/Other/`, `Database/`, `Backups/`, `Imports/` ディレクトリを作成。
- `import_file_to_library(src_path: str, metadata: SampleItem, move: bool = False) -> str`:
  - メタデータに基づき適切な管理サブフォルダ（`Library/[Type]/[Genre]/[Instrument]/`）を決定し、ファイルをコピー/移動。配置先パスを返却。
- `rename_library_file(sample_id: int, old_path: str, new_filename: str) -> str`:
  - 管理ライブラリ内のファイルをリネームし、新パスを返却。

---

## 3. Parser & Audio Signal Analyzer Layer

### `FilenameParser`
- `parse_filename(filepath_or_name: str) -> ParsedMetadata`:
  - ファイル名および拡張子から正規表現パターンを用いて Type, BPM, Key, Scale, Instrument, Genre, Creator を抽出。抽出不能な属性には `"Other"` または `None` をセット。
- `normalize_key(raw_key: str) -> Optional[Tuple[str, str]]`:
  - 抽出されたキー表記（例: `C♯minor`, `C#m`, `Dm`）を標準形式（音名: `C#`, 調性: `minor`）に正規化。
- `normalize_bpm(raw_bpm: str) -> Optional[float]`:
  - 抽出されたBPM文字列を浮動小数点数（例: `174.0`）に変換・検証。

### `AudioSignalAnalyzer`
- `analyze_audio_file(filepath: str) -> AudioAnalysisResult`:
  - 音声ファイルを読み込み、BPM（テンポ）およびKey（調性・スケール）を定量算出。
- `estimate_bpm(audio_data: np.ndarray, sample_rate: int) -> Optional[float]`:
  - 音声信号のオンセットエンベロープを計算し、自己相関（Autocorrelation）によりピーク周期からBPMを算出。
- `estimate_key(audio_data: np.ndarray, sample_rate: int) -> Optional[Tuple[str, str]]`:
  - STFTによる12音階クロマグラム（Chromagram）を計算し、Krumhansl-Schmucklerキープロファイルとの相関により主調（Key名, Major/Minor）を推定。

### `AutoRenamer`
- `generate_standard_filename(original_filename: str, bpm: Optional[float], key: Optional[str], scale: Optional[str]) -> str`:
  - `[BaseName]_[BPM]BPM_[Key][Scale].[ext]` 形式の標準ファイル名文字列を生成。
- `apply_rename_and_move(sample: SampleItem, new_name: str) -> SampleItem`:
  - ファイルリネームを実行し、必要に応じて管理フォルダ内の新ディレクトリへ移動、SampleItemエンティティを更新。

---

## 4. Audio Engine Layer

### `AudioPlayer`
- `load_and_play(filepath: str, auto_play: bool = True) -> bool`:
  - 音声ファイルをロードし、自動再生が有効な場合は即座に再生を開始。
- `pause() -> None`: 再生を一時停止。
- `resume() -> None`: 一時停止を解除して再生再開。
- `stop() -> None`: 再生を停止し、再生ヘッドを先頭に戻す。
- `seek(position_ms: int) -> None`: 指定したミリ秒位置へ再生ヘッドをシーク。
- `set_volume(volume: float) -> None`: マスター音量（0.0 〜 1.0）を設定。
- `set_loop(enabled: bool) -> None`: ループ再生モード（ON/OFF）を切り替え。
- `get_playback_position() -> int`: 現在の再生位置（ms）を取得。
- `get_duration() -> int`: 音声ファイルの総再生時間（ms）を取得。

### `WaveformExtractor`
- `extract_waveform_peaks(filepath: str, num_peaks: int = 500) -> np.ndarray`:
  - 音声ファイルを高速デコードし、`num_peaks` 個の正規化振幅ピーク（Min/MaxまたはRMS配列）を抽出してキャッシュ。

---

## 5. Service Layer

### `LibraryService`
- `import_directory(dir_path: str, progress_callback: Callable = None) -> ImportSummary`:
  - 指定ディレクトリ内の全音源を走査、メタデータ解析、管理ライブラリへの分類配置、およびDB一括登録を実行。
- `rescan_library(progress_callback: Callable = None) -> SyncSummary`:
  - `Library/` ディレクトリとDBの差分を検知し、同期。
- `update_sample_metadata(sample_id: int, updates: Dict[str, Any]) -> bool`:
  - 音源のタグや属性を手動更新し、DBへ反映。

### `SearchService`
- `query_samples(filter_params: SearchFilter) -> List[SampleItem]`:
  - ファセット条件およびフリーワードから検索を実行し結果リストを返却。
- `get_facets() -> FacetData`:
  - フィルターUI描画用のファセット項目一覧と該当件数を取得。

### `AudioAnalysisService`
- `batch_analyze_unknown_samples(sample_ids: List[int], progress_callback: Callable = None) -> List[AnalysisPreviewItem]`:
  - 指定された不明音源群を順次DSP解析し、検出BPM、推定Key、新ファイル名候補を生成して返却。
- `apply_analysis_results(approved_items: List[AnalysisPreviewItem]) -> BatchResult`:
  - ユーザーが承認した解析結果を実ファイルおよびDBへ適用（リネーム・フォルダ移動・メタデータ更新）。

### `PlaybackService`
- `select_and_preview(sample: SampleItem) -> None`:
  - 選択された音源の波形抽出と再生を開始（Auto-Play設定に応じる）。
- `toggle_loop(enabled: bool) -> None`: ループ再生モードを設定。

---

## 6. UI Presentation Layer

### `MainWindow`
- `setup_ui()`: UIレイアウト、テーマ、各パネルの配置と接続。
- `on_filter_changed(filter_params: SearchFilter)`: 検索サービスを呼び出してテーブルビューを更新。
- `on_sample_selected(sample: SampleItem)`: 再生サービスに通知してプレビュー開始。

### `AudioAnalysisDialog`
- `show_analysis_queue(samples: List[SampleItem])`: 解析対象リストを表示。
- `start_analysis()`: バックグラウンドで解析を実行し、プログレスバーを更新。
- `apply_selected()`: 承認されたリネーム処理をサービス層へ指示。

### `DAWDragDropHandler`
- `start_drag(sample: SampleItem, event: QMouseEvent)`:
  - `QDrag` オブジェクトを作成し、`QMimeData` に `urls`（`file:///path/to/sample.wav`）をセットしてドラッグ操作を開始。
