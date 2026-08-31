# Application Design: Component Definitions (components.md)

## 1. Overview
音源管理ソフト（Sound Sample Manager）は、レイヤード・アーキテクチャ（Layered Architecture）を採用し、UI層、サービス層、リポジトリ/データ層、オーディオ/DSP層、コアモデル層の5つの層に明確に分離して設計されます。

---

## 2. Component Inventory

### 2.1 Core Domain Layer (`core/`)
- **`SampleItem`**:
  - **Purpose**: 単一の音源ファイルを表現するドメインエンティティ。
  - **Responsibilities**: 音源のパス、ファイル名、Type（Loop/Oneshot/Other）、Instrument（楽器）、Genre/Pack（ジャンル/パック名）、BPM、Key（調性）、Scale（Major/Minor）、Creator（制作者）、再生時間、フォーマット、タグ、お気に入りフラグ、更新日時等の保持。
- **`LibraryConfig`**:
  - **Purpose**: アプリケーション設定およびライブラリパスを管理するモデル。
  - **Responsibilities**: ライブラリ保存先ルート（`SoundLibrary/`）、データベースパス、自動バックアップ設定、音量、Auto-Playデフォルト設定の保持・永続化。

### 2.2 Database & Storage Layer (`database/`, `storage/`)
- **`DatabaseManager`**:
  - **Purpose**: SQLiteデータベースの接続・ライフサイクル管理。
  - **Responsibilities**: SQLiteスキーマの作成・初期化、WAL（Write-Ahead Logging）モードの有効化、整合性チェック（Integrity Check）、起動時/終了時の自動バックアップ世代管理（RESILIENCY-12）。
- **`SampleRepository`**:
  - **Purpose**: `SampleItem` の永続化および高速検索クエリ実行。
  - **Responsibilities**: CRUD操作（追加・更新・削除）、多角的なファセット検索（Type, 楽器, ジャンル, BPM範囲, キー, 制作者, フリーワード）、マルチカラムソートクエリの実行。
- **`LibraryFileManager`**:
  - **Purpose**: 管理型フォルダ構造（`SoundLibrary/Library/`）の物理ファイル操作。
  - **Responsibilities**: インポート元からのファイルコピー・整理配置（`Loop/`, `Oneshot/`, `Other/` 各サブディレクトリ）、ファイルリネーム、フォルダスキャン、削除・同期。

### 2.3 Metadata & DSP Engine Layer (`parser/`, `analyzer/`)
- **`FilenameParser`**:
  - **Purpose**: ファイル名および埋め込みタグからのメタデータ抽出。
  - **Responsibilities**: BandLab Sounds等の命名規則に合わせた正規表現・ルールベース解析（BPM, Key, Type, Instrument, Genre, Creator）。判定不能な属性に対する「Other」タグ/フォールバックの割り当て。
- **`AudioSignalAnalyzer`**:
  - **Purpose**: プロパティ不明音源（「Other」等）の定量音声信号解析（Story 2.4 / FR-2.5）。
  - **Responsibilities**: 軽量NumPy/SciPyを用いた音声波形解析。オンセットエネルギー・自己相関によるBPM（テンポ）検出、クロマ特徴量（STFT）によるKey（調性・主音・スケール）の自動推定。
- **`AutoRenamer`**:
  - **Purpose**: 解析結果に基づくファイル名整形とリネーム実行。
  - **Responsibilities**: 検出されたBPM・Keyを標準命名規則（`[OriginalName]_[BPM]BPM_[Key].[ext]`）に沿ってフォーマットし、ファイルシステムおよびDBのパスを安全に更新。

### 2.4 Audio Engine Layer (`audio/`)
- **`AudioPlayer`**:
  - **Purpose**: 音声ファイルの低レイテンシープレビュー再生。
  - **Responsibilities**: 再生（Play）、一時停止（Pause）、停止（Stop）、シーク（Seek）、音量調整、ループ再生（Loop Playback ON/OFF）の制御。破損ファイル検出時のエラー隔離（RESILIENCY-10）。
- **`WaveformExtractor`**:
  - **Purpose**: 波形描画用ピークデータの高速抽出とキャッシュ。
  - **Responsibilities**: 音声ファイルから振幅データを読み込み、UI描画用のダウンサンプリングされたピーク値配列を生成。

### 2.5 Service Layer (`services/`)
- **`LibraryService`**:
  - **Purpose**: 音源のインポート・ファイル整理・DB登録の一連のワークフローを統合。
- **`SearchService`**:
  - **Purpose**: UIからの検索・フィルタリング・ソート要求を解釈し、リポジトリへ問い合わせて結果を返却。
- **`AudioAnalysisService`**:
  - **Purpose**: 未知音源のバッチ音声解析、推定結果プレビュー、自動リネームおよび管理フォルダ移動のオーケストレーション。
- **`PlaybackService`**:
  - **Purpose**: 音源選択時のAuto-Play、再生状態管理、波形データの取得をUIへ調停。

### 2.6 UI Presentation Layer (`ui/`)
- **`MainWindow`**: アプリケーションメインウィンドウ（ダークテーマ、レイアウト統括）。
- **`FacetFilterPanel`**: 左側ファセット検索パネル（Type, 楽器, ジャンル, BPMスライダー, Keyドロップダウン, 制作者, Other）。
- **`SampleTableView`**: 中央音源一覧テーブル（ソート対応、複数選択、右クリックメニュー）。
- **`WaveformWidget`**: 波形表示・再生ヘッド・クリックシーク対応のカスタムQtウィジェット。
- **`AudioControlBar`**: 下部再生コントロールバー（再生/停止、音量、Auto-Play/Loopトグル、波形）。
- **`AudioAnalysisDialog`**: 不明音源の解析実行・推定結果確認・リネーム適用を行う専用ダイアログ。
- **`DAWDragDropHandler`**: テーブル行のマウスドラッグ時に `QDrag` と `text/uri-list` を構築し、Cakewalk/Sonar等のDAWトラックやエクスプローラーへファイルを渡すハンドラー。
