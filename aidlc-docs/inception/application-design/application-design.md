# Consolidated Application Design: Sound Sample Manager (音源管理ソフト)

## Executive Summary
本ドキュメントは、音源管理ソフト（Sound Sample Manager）の全体アーキテクチャ、コンポーネント構成、サービス層オーケストレーション、およびデータフローを統合したアプリケーション設計書です。

---

## 1. Architectural Style: Layered Architecture

```
+-----------------------------------------------------------------------+
| 🖥️ UI Presentation Layer (PyQt6)                                      |
| MainWindow, FacetFilterPanel, SampleTableView, WaveformWidget,        |
| AudioControlBar, AudioAnalysisDialog, DAWDragDropHandler              |
+-----------------------------------------------------------------------+
                                  │ (Invokes)
                                  ▼
+-----------------------------------------------------------------------+
| ⚙️ Service Layer                                                       |
| LibraryService, SearchService, AudioAnalysisService, PlaybackService  |
+-----------------------------------------------------------------------+
                                  │ (Orchestrates)
                  ┌───────────────┴───────────────┐
                  ▼                               ▼
+-----------------------------------+ +---------------------------------+
| 🗄️ Database & Storage Layer       | | 🎧 Audio & DSP Layer            |
| DatabaseManager (SQLite WAL)      | | AudioPlayer (Low Latency)       |
| SampleRepository (Faceted Search) | | WaveformExtractor (Peaks Cache) |
| LibraryFileManager (Folder Tree)  | | FilenameParser (Regex/Rule)     |
|                                   | | AudioSignalAnalyzer (BPM/Key)   |
|                                   | | AutoRenamer (Standard Naming)   |
+-----------------------------------+ +---------------------------------+
                  │                               │
                  └───────────────┬───────────────┘
                                  ▼
+-----------------------------------------------------------------------+
| 📦 Core Domain Models                                                 |
| SampleItem, LibraryConfig, SearchFilter, AudioAnalysisResult          |
+-----------------------------------------------------------------------+
```

---

## 2. Key Components & Responsibilities

### 2.1 Core Domain
- **`SampleItem`**: 音源エンティティ（ID, パス, ファイル名, Type, 楽器, ジャンル/パック, BPM, Key, Scale, Creator, 再生時間, フォーマット, タグ, お気に入り）。
- **`LibraryConfig`**: アプリケーション設定（ライブラリ保存先ルート `SoundLibrary/`、DBパス、バックアップ世代数、音量設定）。

### 2.2 Database & Storage
- **`DatabaseManager`**: SQLite初期化、インデックス最適化、WALモード設定、起動時整合性チェック、自動バックアップ世代管理（直近5世代保持）。
- **`SampleRepository`**: 高速ファセット検索クエリ、CRUD、フリーワード検索、マルチカラムソート。
- **`LibraryFileManager`**: 管理型フォルダ（`Library/Loop/`, `Library/Oneshot/`, `Library/Other/`）への物理ファイルコピー・整理配置、リネーム、同期。

### 2.3 Metadata & DSP Analysis
- **`FilenameParser`**: BandLab Sounds等の命名規則解析（BPM, Key, Type, 楽器, パック名, 制作者）、判定不能項目の「Other」フォールバック付与。
- **`AudioSignalAnalyzer`**: プロパティ不明音源の定量音声信号解析（オンセット自己相関によるBPM算出、クロマ特徴量STFTによるKey/Scale推定）。
- **`AutoRenamer`**: 算出されたBPM・Keyを標準命名規則（`[BaseName]_[BPM]BPM_[Key].[ext]`）に沿ってフォーマットし安全にファイル名更新。

### 2.4 Audio & UI Presentation
- **`AudioPlayer`**: 低レイテンシー再生、ループ再生（ON/OFF）、Auto-Play、シーク、音量調整。
- **`WaveformExtractor` & `WaveformWidget`**: 波形ピークデータ抽出とQtカスタムウィジェットによる描画、再生ヘッド同期、クリックシーク。
- **`DAWDragDropHandler`**: Cakewalk by BandLab / Sonar 等のDAWトラックへ音源を直接ドラッグ＆ドロップ配置するためのネイティブ `QDrag` / `text/uri-list` 連携。
- **`AudioAnalysisDialog`**: 不明音源のバッチ解析実行、検出結果プレビュー、リネーム承認ダイアログ。

---

## 3. Key Operational Workflows

### 3.1 音楽制作ワークフロー（検索 → 試聴 → DAW配置）
1. ユーザーが左側 `FacetFilterPanel` で Type（Loop/Oneshot/Other）、楽器、Key、BPMスライダーを選択。
2. `SearchService` が `SampleRepository` を介してSQLiteから条件に合致する音源を高速抽出。
3. リストで音源を選択すると、`PlaybackService` が波形を描画し、Auto-PlayがONなら即座に試聴再生を開始。
4. ユーザーがリスト行をマウスでドラッグし、起動中の **Cakewalk / Sonar** のトラックへドロップすると、オーディオクリップとして直接貼り付け完了。

### 3.2 ライブラリ管理 & 「Other」フォールバック
1. ユーザーが任意の音源フォルダ（例: `Loop/`, `Oneshot/`）をインポート。
2. `FilenameParser` がファイル名を解析し、判別できた音源は `Library/[Type]/[Genre]/[Instrument]/` へ分類配置。
3. 判別不能な音源は安全に `Library/[Type]/Other/` または `Library/Other/` へ配置され、「Other」タグが付与される。

### 3.3 不明音源の定量解析 & 自動リネーム (Story 2.4 / FR-2.5)
1. ユーザーが「Other」分類音源を選択し、「音声解析・自動リネーム」を実行。
2. `AudioSignalAnalyzer` が音声信号からBPM（テンポ）およびKey（調性）を自動算出。
3. ダイアログで新ファイル名候補（例: `Sample_174BPM_Dminor.wav`）をプレビュー表示。
4. ユーザー承認後、`AutoRenamer` が実ファイルをリネームし、管理フォルダ内の適切なサブディレクトリへ移動、DBを同期更新。

---
