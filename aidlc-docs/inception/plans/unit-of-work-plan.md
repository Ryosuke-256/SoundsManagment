# Unit of Work Plan (開発ユニット計画書)

## Purpose
要件定義、ユーザーストーリー、およびアプリケーション設計に基づき、システムを独立して実装・テスト可能な開発ユニット（Units of Work）へ分割・定義するための計画書です。

---

## Planning Questions (ユニット分割に関する確認事項)

### Question 1: 開発ユニットの分割粒度と実装順序 (Unit Decomposition & Sequence)
システムのユニット分割および実装進行順序について、どのアプローチを希望されますか？

A) 4ユニット順次構成（推奨：基盤層からUI層へと依存順にボトムアップで構築・テストする方式）
   - **Unit 1: Data Model, Database & Library File Manager**（音源モデル、SQLite WAL、自動バックアップ、`SoundLibrary/` フォルダ整理、「Other」隔離）
   - **Unit 2: Metadata Parser & Audio Signal Analyzer**（ファイル名規則解析、Key/BPM正規化、DSP音声解析によるBPM/Key自動算出、命名規則リネーム）
   - **Unit 3: Audio Engine & Waveform Visualizer**（低遅延プレビュー再生、Auto-Play、ループ再生、波形ピークデータ抽出）
   - **Unit 4: Desktop GUI & DAW Drag-and-Drop Integration**（PyQt6メイン画面、ファセット検索パネル、音源テーブル、波形バー、Cakewalk/SonarへのD&D、音声解析ダイアログ）

B) 2ユニット大分類構成
   - **Unit 1: Core Backend & Audio Processing**（データモデル、DB、ファイル管理、パーサー、DSP解析、オーディオエンジン）
   - **Unit 2: Frontend GUI & DAW Integration**（PyQt6 UI、波形描画、DAWドラッグ＆ドロップ）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2: ソースコードのディレクトリ構成 (Code Organization Structure)
`src/` 配下のパッケージ・モジュール構成について、どのアプローチを希望されますか？

A) レイヤードパッケージ構成（クリーンで明確な責務分離）
   ```
   SoundSampleManager/
   ├── src/
   │   ├── core/          # SampleItem, LibraryConfig 等の共通モデル・設定
   │   ├── database/      # DatabaseManager, SampleRepository (SQLite WAL)
   │   ├── storage/       # LibraryFileManager (フォルダ整理・同期・Other隔離)
   │   ├── parser/        # FilenameParser (正規表現・ルールベース解析)
   │   ├── analyzer/      # AudioSignalAnalyzer, AutoRenamer (DSP BPM/Key検出・リネーム)
   │   ├── audio/         # AudioPlayer, WaveformExtractor (低遅延再生・波形生成)
   │   ├── services/      # LibraryService, SearchService, AnalysisService, PlaybackService
   │   ├── ui/            # MainWindow, FacetFilterPanel, SampleTableView, WaveformWidget, AudioAnalysisDialog
   │   └── main.py        # アプリケーション起動エントリポイント
   ├── tests/             # ユニットテスト & Hypothesis PBTテスト
   ├── SoundLibrary/      # 管理型音源ライブラリ・DB・バックアップ保存先
   └── requirements.txt   # 依存ライブラリ一覧
   ```

B) フラット構成（`src/` 直下に最小限のファイル群を配置）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Execution Checklist (実行チェックリスト)

### Part 1: Planning
- [x] Step 1: Analyze context (`requirements.md`, `stories.md`, `application-design.md`)
- [x] Step 2: Create unit of work plan (`unit-of-work-plan.md`)
- [x] Step 3: Embed context-appropriate questions with `[Answer]:` tags
- [x] Step 6: Collect and analyze user answers
- [x] Step 9: Obtain user approval for Unit of Work Plan

### Part 2: Generation (ユニット成果物の作成)
- [x] Step 1: Generate `aidlc-docs/inception/application-design/unit-of-work.md` (ユニット定義・責務・コード構成戦略)
- [x] Step 2: Generate `aidlc-docs/inception/application-design/unit-of-work-dependency.md` (ユニット間依存関係マトリクス)
- [x] Step 3: Generate `aidlc-docs/inception/application-design/unit-of-work-story-map.md` (ユーザーストーリーとユニットのマッピング)
- [x] Step 4: Validate unit completeness and boundary consistency
- [x] Step 5: Final review and user approval of Units Generation
