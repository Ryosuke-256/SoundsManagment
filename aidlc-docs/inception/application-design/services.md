# Application Design: Services & Orchestration (services.md)

## 1. Overview
サービス層（`services/`）は、UI層とデータ/DSP層の間に位置し、業務シナリオ（インポート、検索、試聴、音声解析・リネーム）のビジネスロジックを統合・オーケストレーションします。

---

## 2. Service Definitions & Responsibilities

### 2.1 `LibraryService` (音源ライブラリ管理サービス)
- **Primary Responsibility**: 音源のインポート、フォルダ階層自動整理、データベース同期のオーケストレーション。
- **Collaborators**: `FilenameParser`, `LibraryFileManager`, `SampleRepository`, `DatabaseManager`
- **Key Flow - Import Workflow**:
  ```
  UI (Import Button Clicked)
    │
    ▼
  LibraryService.import_directory(path, progress_callback)
    │
    ├─► 1. 音声ファイル（.wav, .mp3, etc.）を再帰探索
    │
    ├─► 2. 各ファイルに対して FilenameParser.parse_filename() を実行
    │      （特定できない属性は "Other" としてタグ付け）
    │
    ├─► 3. LibraryFileManager.import_file_to_library() で
    │      SoundLibrary/Library/[Type]/[Genre]/[Instrument]/ へコピー
    │
    ├─► 4. SampleRepository.insert_samples_batch() でDBへ一括永続化
    │
    └─► 5. UIへインポート結果（件数、Other件数）を返却
  ```

### 2.2 `SearchService` (検索・フィルタリングサービス)
- **Primary Responsibility**: ファセット選択やテキスト入力に応じた検索クエリの構築、実行、キャッシュ、ファセット集計。
- **Collaborators**: `SampleRepository`
- **Key Flow - Search Workflow**:
  ```
  FacetFilterPanel / SearchBar (Filter Changed)
    │
    ▼
  SearchService.query_samples(SearchFilter)
    │
    ├─► 1. フィルターパラメータをSQL条件にマッピング
    ├─► 2. SampleRepository.search_samples() を実行（インデックス利用）
    ├─► 3. ファセット項目の件数集計（get_facets()）を並行取得
    └─► 4. UIテーブルビューへ結果リストをバインド
  ```

### 2.3 `AudioAnalysisService` (音声定量解析 & 自動リネームサービス)
- **Primary Responsibility**: 不明音源に対するBPM/Keyの自動算出、命名規則に沿ったファイル名候補のプレビュー生成、承認されたリネーム処理とライブラリ再配置の統合（Story 2.4 / FR-2.5）。
- **Collaborators**: `AudioSignalAnalyzer`, `AutoRenamer`, `LibraryFileManager`, `SampleRepository`
- **Key Flow - Analysis & Renaming Workflow**:
  ```
  UI (AudioAnalysisDialog: "BPM/Key解析実行")
    │
    ▼
  AudioAnalysisService.batch_analyze_unknown_samples(sample_ids)
    │
    ├─► 1. 対象音声ファイルをロード
    ├─► 2. AudioSignalAnalyzer.estimate_bpm() でテンポ算出
    ├─► 3. AudioSignalAnalyzer.estimate_key() で調性・スケール推定
    ├─► 4. AutoRenamer.generate_standard_filename() で新ファイル名候補を生成
    ├─► 5. 解析プレビュー一覧をダイアログへ返却し、ユーザーの承認を待機
    │
    ▼ ユーザーが「適用」をクリック
  AudioAnalysisService.apply_analysis_results(approved_items)
    │
    ├─► 6. LibraryFileManager.rename_library_file() で実ファイルをリネーム・再配置
    ├─► 7. SampleRepository.update_sample() でDBのBPM/Key/パスを更新
    └─► 8. UIへ成功通知およびリストのリフレッシュ
  ```

### 2.4 `PlaybackService` (再生・波形管理サービス)
- **Primary Responsibility**: UI操作とオーディオエンジン、波形抽出の連携調停。
- **Collaborators**: `AudioPlayer`, `WaveformExtractor`
- **Key Flow - Selection & Playback Workflow**:
  ```
  SampleTableView (Item Selected)
    │
    ▼
  PlaybackService.select_and_preview(sample)
    │
    ├─► 1. WaveformExtractor.extract_waveform_peaks(filepath) から波形取得
    ├─► 2. UIのWaveformWidgetへ波形データを渡し描画
    ├─► 3. Auto-Play設定がONの場合: AudioPlayer.load_and_play(filepath) を実行
    └─► 4. 再生タイマーにより再生位置（ms）をWaveformWidgetの再生ヘッドに同期
  ```

---
