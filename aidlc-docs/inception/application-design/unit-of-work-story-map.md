# Unit of Work Story Map (unit-of-work-story-map.md)

## 1. Overview
本ドキュメントでは、INCEPTIONフェーズで定義された7つのユーザーストーリー（`stories.md`）を4つの開発ユニット（Unit 1〜Unit 4）へマッピングし、受入基準（Acceptance Criteria）のトレーサビリティを確立します。

---

## 2. Story to Unit Mapping

| Story ID | ストーリー名 | 担当開発ユニット | 主要実装コンポーネント |
|---|---|---|---|
| **Story 1.1** | 多角的なファセット絞り込みとソートによる音源検索 | **Unit 1** (クエリ基盤) & **Unit 4** (UI) | `SampleRepository.search_samples()`, `FacetFilterPanel`, `SampleTableView`, `SearchService` |
| **Story 1.2** | 波形表示と自動再生・ループ試聴プレビュー | **Unit 3** (再生・波形) & **Unit 4** (UI) | `AudioPlayer`, `WaveformExtractor`, `PlaybackService`, `WaveformWidget`, `AudioControlBar` |
| **Story 1.3** | DAW（Cakewalk/Sonar等）への直接ドラッグ＆ドロップ連携 | **Unit 4** (GUI & D&D) | `DAWDragDropHandler`, `SampleTableView` |
| **Story 2.1** | 音源インポート・自動フォルダ整理 & 「Other」フォールバック | **Unit 1** (ファイル/DB) & **Unit 2** (パーサー) | `LibraryFileManager`, `FilenameParser`, `LibraryService`, `DatabaseManager` |
| **Story 2.2** | 「Other」音源の確認と手動メタデータ編集・タグ付け | **Unit 1** (更新API) & **Unit 4** (編集UI) | `SampleRepository.update_sample()`, `SampleTableView`, `LibraryService` |
| **Story 2.3** | データベース永続化・高速検索同期・自動バックアップ | **Unit 1** (DB & 整合性) | `DatabaseManager` (WAL, backup), `SampleRepository` |
| **Story 2.4** | 不明音源の定量音声解析（BPM/Key算出）と命名規則リネーム | **Unit 2** (DSP解析/リネーム) & **Unit 4** (ダイアログ) | `AudioSignalAnalyzer`, `AutoRenamer`, `AudioAnalysisService`, `AudioAnalysisDialog` |

---

## 3. Unit-by-Unit Story Coverage & Validation

### Unit 1: Data Model, Database & Library Manager
- **Mapped Stories**:
  - Story 2.1 (Partially: フォルダ階層作成、ファイル移動・コピー、「Other」ディレクトリ隔離)
  - Story 2.2 (Partially: メタデータ更新・タグ更新クエリ)
  - Story 2.3 (Fully: SQLite WAL、Integrity Check、自動バックアップ、永続化)
  - Story 1.1 (Partially: ファセット検索・ソートSQLクエリ)
- **Unit Verification Criteria**:
  - SQLiteデータベースの作成、WALモード設定、起動時バックアップが正常に機能すること
  - `SoundLibrary/Library/Loop/`, `Oneshot/`, `Other/` のディレクトリ構造が自動生成・管理されること
  - ファセット検索クエリが10ms未満で実行できること

### Unit 2: Metadata Parser & Audio Signal Analyzer
- **Mapped Stories**:
  - Story 2.1 (Partially: BandLab命名規則解析、Key/BPM正規化、「Other」タグ付与)
  - Story 2.4 (Fully: 音声信号からのBPM検出・Key推定、標準命名規則生成、ファイルリネーム)
- **Unit Verification Criteria**:
  - BandLab音源ファイル名（例: `03_SS_Guitar_Snob_174_4_bar_Loop_C#_guitar_174BPM_C♯minor_BANDLAB.wav`）から全属性が正確に抽出されること
  - 不明音源に対してDSP解析が動作し、妥当なBPM（テンポ）およびKey（調性）が算出されること
  - HypothesisによるPBTテスト（ラウンドトリップ・不変条件）が合格すること

### Unit 3: Audio Engine & Waveform Visualizer
- **Mapped Stories**:
  - Story 1.2 (Fully: 低遅延再生、Auto-Play、ループ再生、波形ピークデータ生成)
- **Unit Verification Criteria**:
  - プレビュー再生開始レイテンシーが50ms未満であること
  - ループ再生がシームレスに動作すること
  - 壊れたWAVファイルが与えられてもクラッシュせず例外を安全に処理すること（RESILIENCY-10）

### Unit 4: Desktop GUI & DAW Drag-and-Drop Integration
- **Mapped Stories**:
  - Story 1.1 (Fully: ファセット検索UI、BPMスライダー、Key選択、カラムソート)
  - Story 1.2 (Fully: 波形描画ウィジェット、再生バー、Auto-Play/Loopトグル)
  - Story 1.3 (Fully: Cakewalk / Sonar 等のDAWトラックへのドラッグ＆ドロップ配置)
  - Story 2.2 (Fully: 「Other」絞り込みとメタデータ編集ダイアログ/パネル)
  - Story 2.4 (Fully: 音声解析ダイアログ、推定結果プレビュー、リネーム実行)
- **Unit Verification Criteria**:
  - Cakewalk / Sonarのトラック上へ音源アイテムをマウスドラッグ＆ドロップして配置できること
  - 全体のワークフロー（インポート → 検索 → 試聴 → DAW配置）がGUI上でスムーズに完結すること
