# Units of Work Specification (unit-of-work.md)

## 1. Overview
本ドキュメントでは、音源管理ソフト（Sound Sample Manager）を段階的に開発・テストするための4つの開発ユニット（Unit 1〜Unit 4）の定義、責務、パッケージ配置、およびコード構成戦略を定義します。

---

## 2. Unit Definitions

### Unit 1: Data Model, Database & Library Manager (`unit-1-data-and-library`)
- **Focus**: データモデル定義、SQLiteデータベース管理、および管理型ファイルシステム構造の確立。
- **Package Location**: `src/core/`, `src/database/`, `src/storage/`
- **Components Included**:
  - `SampleItem`, `LibraryConfig`, `SearchFilter`
  - `DatabaseManager` (SQLiteスキーマ、WALモード、整合性チェック、自動バックアップ世代管理)
  - `SampleRepository` (CRUD、ファセット検索、ソート、ファセット集計)
  - `LibraryFileManager` (`SoundLibrary/` フォルダ階層作成、ファイル分類コピー、同期、「Other」隔離)
- **Applicable Rules / Extensions**:
  - RESILIENCY-01: クリティカルワークロード（DB・ライブラリ）の保護
  - RESILIENCY-12: SQLiteデータベースの自動バックアップ（直近5世代保持）

### Unit 2: Metadata Parser & Audio Signal Analyzer (`unit-2-parser-and-analyzer`)
- **Focus**: ファイル名からのメタデータ抽出、および未知音源に対するDSP音声信号解析（BPM/Key自動算出）と自動リネーム。
- **Package Location**: `src/parser/`, `src/analyzer/`
- **Components Included**:
  - `FilenameParser` (正規表現・ルールベース解析、BPM/Key正規化、「Other」タグ付与)
  - `AudioSignalAnalyzer` (NumPy/SciPyによるオンセット自己相関BPM検出、クロマ特徴量Key推定)
  - `AutoRenamer` (標準命名規則 `[Base]_[BPM]BPM_[Key].[ext]` 生成とリネーム実行)
- **Applicable Rules / Extensions**:
  - PBT-02: ファイル名解析・正規化のラウンドトリッププロパティテスト
  - PBT-03: BPM/Key正規化における不変条件テスト（BPM正数、Key標準表記、「Other」収束）
  - PBT-07 / PBT-08 / PBT-09: Hypothesisフレームワークによるテスト生成・シュリンク

### Unit 3: Audio Engine & Waveform Visualizer (`unit-3-audio-and-waveform`)
- **Focus**: 低レイテンシープレビュー再生エンジン、および高速波形ピークデータ抽出。
- **Package Location**: `src/audio/`, `src/services/playback_service.py`
- **Components Included**:
  - `AudioPlayer` (PyQt6.QtMultimedia / オーディオバックエンド、再生/停止/シーク/音量/Loop再生)
  - `WaveformExtractor` (音声ファイルの高速デコード、ピーク値配列抽出・キャッシュ)
  - `PlaybackService` (音源選択時のAuto-Play・波形描画・再生タイマー調停)
- **Applicable Rules / Extensions**:
  - RESILIENCY-10: 破損オーディオファイル・未対応形式の例外隔離とスキップ処理

### Unit 4: Desktop GUI & DAW Drag-and-Drop Integration (`unit-4-gui-and-daw-integration`)
- **Focus**: PyQt6デスクトップGUI画面、ファセット検索UI、DAWドラッグ＆ドロップ連携、および音声解析ダイアログの統合。
- **Package Location**: `src/ui/`, `src/services/`, `src/main.py`
- **Components Included**:
  - `MainWindow`, `FacetFilterPanel`, `SampleTableView`, `WaveformWidget`, `AudioControlBar`
  - `AudioAnalysisDialog` (未知音源のバッチ解析・プレビュー・リネーム適用ダイアログ)
  - `DAWDragDropHandler` (`QDrag` / `text/uri-list` による Cakewalk by BandLab / Sonar へのネイティブD&D)
  - `LibraryService`, `SearchService`, `AudioAnalysisService`
  - `main.py` (エントリポイント、ダークテーマ適用、依存性注入)

---

## 3. Code Organization Strategy (ディレクトリ構成戦略)

```
SoundSampleManager/
├── src/
│   ├── __init__.py
│   ├── main.py                     # アプリケーション起動エントリポイント
│   ├── core/                       # [Unit 1] ドメインモデル & 設定
│   │   ├── __init__.py
│   │   ├── models.py               # SampleItem, SearchFilter, AudioAnalysisResult
│   │   └── config.py               # LibraryConfig
│   ├── database/                   # [Unit 1] データベース層
│   │   ├── __init__.py
│   │   ├── db_manager.py           # DatabaseManager (SQLite WAL, Backup)
│   │   └── repository.py           # SampleRepository (Faceted Search, CRUD)
│   ├── storage/                    # [Unit 1] ファイル管理層
│   │   ├── __init__.py
│   │   └── file_manager.py         # LibraryFileManager (Folder Tree, Copy, Sync)
│   ├── parser/                     # [Unit 2] メタデータ解析層
│   │   ├── __init__.py
│   │   └── filename_parser.py      # FilenameParser (Regex, Normalization, Other tag)
│   ├── analyzer/                   # [Unit 2] DSP音声解析 & リネーム層
│   │   ├── __init__.py
│   │   ├── audio_analyzer.py       # AudioSignalAnalyzer (BPM/Key detection)
│   │   └── auto_renamer.py         # AutoRenamer (Standard Naming & Move)
│   ├── audio/                      # [Unit 3] オーディオエンジン層
│   │   ├── __init__.py
│   │   ├── player.py               # AudioPlayer (Low Latency, Loop, Seek)
│   │   └── waveform.py             # WaveformExtractor (Peaks generation)
│   ├── services/                   # [Unit 1-4] サービス層
│   │   ├── __init__.py
│   │   ├── library_service.py      # LibraryService (Import, Sync)
│   │   ├── search_service.py       # SearchService (Query, Facets)
│   │   ├── analysis_service.py     # AudioAnalysisService (Batch DSP Analysis)
│   │   └── playback_service.py     # PlaybackService (Play, Waveform, Loop)
│   └── ui/                         # [Unit 4] PyQt6 GUIプレゼンテーション層
│       ├── __init__.py
│       ├── main_window.py          # MainWindow (Layout, Dark Theme)
│       ├── facet_panel.py          # FacetFilterPanel (Chips, Sliders, Dropdowns)
│       ├── sample_table.py         # SampleTableView (Sortable Table, Context Menu)
│       ├── waveform_widget.py      # WaveformWidget (Custom Painter, Playhead, Seek)
│       ├── audio_bar.py            # AudioControlBar (Play Controls, Volume, Loop)
│       ├── analysis_dialog.py      # AudioAnalysisDialog (BPM/Key Batch Dialog)
│       └── drag_drop.py            # DAWDragDropHandler (QDrag text/uri-list)
├── tests/                          # ユニットテスト & Hypothesis PBT
│   ├── test_unit1_database.py
│   ├── test_unit1_storage.py
│   ├── test_unit2_parser.py        # PBT Hypothesis test
│   ├── test_unit2_analyzer.py
│   ├── test_unit3_audio.py
│   └── test_unit4_services.py
├── SoundLibrary/                   # [Runtime] 管理型音源ライブラリ
│   ├── Library/
│   │   ├── Loop/
│   │   ├── Oneshot/
│   │   └── Other/
│   ├── Database/
│   │   └── library.db
│   ├── Backups/
│   └── Imports/
├── requirements.txt                # 依存ライブラリ一覧
└── README.md
```

---
