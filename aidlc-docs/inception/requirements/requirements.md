# Requirements Document: Sound Sample Manager (音源管理ソフト)

## Intent Analysis Summary

- **User Request**: DAW（Cakewalk by BandLab, Sonar等）での音楽制作時に、欲しい音源をローカルファイル内から迅速に検索・プレビュー・配置できる音源管理ソフトを開発する。タイプ（Loop / Oneshot）、楽器、ジャンル、BPM、キー、制作者によるソート・絞り込み、波形表示・プレビュー試聴機能、DAWへの直接ドラッグ＆ドロップ、および継続的な利用を支える管理型フォルダ構成を実現する。未分類・振り分けられない音源に対しては「Other」タグ/カテゴリを自動付与し、後からの確認や再分類を容易にする。
- **Request Type**: New Project (Greenfield)
- **Scope Estimate**: Multiple Components (Desktop GUI, Audio Engine & Waveform Visualizer, Metadata Parser & Tagging Engine, Library File Manager, SQLite Database & Search Indexer)
- **Complexity Estimate**: Moderate
- **Requirements Depth**: Standard / Comprehensive

---

## 1. Functional Requirements (機能要件)

### 1.1 UI & ユーザーインターフェース (FR-1)
- **FR-1.1**: Python + PyQt6（またはPySide6）を用いたデスクトップGUIアプリケーション。音楽制作用途にマッチしたモダンなダークテーマUIを提供。
- **FR-1.2**: メイン画面構成：
  - 上部：グローバル検索バー、ライブラリスキャン/インポートボタン、設定ボタン
  - 左ペイン：ファセットフィルターパネル（Type、Instrument、Genre/Pack、Key、BPMスライダー、Creator）
  - 中央ペイン：音源一覧テーブル/リストビュー（ファイル名、Type、Instrument、Genre、BPM、Key、Creator、再生時間、フォーマット等を表示・ソート可能）
  - 下部ペイン：高機能オーディオプレビューバー（波形表示、シークバー、再生/一時停止/停止、音量、自動再生トグル、ループ再生トグル）

### 1.2 メタデータ自動解析 & タグ付け (FR-2)
- **FR-2.1**: **ファイル名パターン解析エンジン**:
  - `BandLab Sounds` をはじめとする一般的なサンプルパックの命名規則を自動抽出：
    - **Type**: Loop（`Loop`, `bar`, `FullLoop` などから判定） / Oneshot（`ONESHOT`, 単発楽器名などから判定） / 判定不能時は **`Other`**
    - **BPM**: 数字 + `BPM` または `_174_` などのテンポ表記を抽出・正規化（未検出時は `None`）
    - **Key**: `C#`, `C♯minor`, `Dm`, `Dminor`, `E1`, `C#m` 等を標準音名（例: `C# min`, `D min`）に正規化（未検出時は `None`）
    - **Instrument**: `guitar`, `synth`, `bass`, `808s`, `kick`, `clap`, `drums`, `beats` などの楽器種別を分類 / 判定不能時は **`Other`**
    - **Genre / Pack / Project**: `SS_Guitar_Snob`, `DW_DistArp`, `FRB_BKnockers`, `808Pressure`, `PwrClap` などのパック名を抽出 / 判定不能時は **`Other`**
    - **Creator / Provider**: `BANDLAB`, `HEAVEE` などの制作者・提供元情報を抽出 / 判定不能時は **`Other`**
- **FR-2.2**: **「Other」フォールバックタグ生成**:
  - 命名規則やタグ情報から特定の属性を特定できない場合、自動的に「Other」タグを割り当て。
  - ユーザーは「Other」で絞り込むことで、未分類の音源を一目で把握し、手動で属性を補完・再タグ付け可能。
- **FR-2.3**: **オーディオメタデータ解析**:
  - WAV（RIFF/BEXT/ID3タグ）、MP3（ID3v2）、FLAC/OGG（Vorbis Comment）に埋め込まれたメタデータの読み取り。
- **FR-2.4**: **手動補完 & タグ編集**:
  - 「Other」に分類された音源やファイル名から取得できなかったメタデータ、カスタムタグをGUI上で個別または一括編集・追加可能。
- **FR-2.5**: **不明音源の定量音声解析 & 命名規則自動リネーム**:
  - BPMやキー情報が不明な音源（「Other」分類等）に対し、音声信号処理（Onset/Tempo検出・Chroma調性解析）を実行してBPMおよびKey（調性）を自動算出。
  - 算出された定量情報（例: `120BPM`, `Dminor`）を、標準の命名規則（例: `[元の名前]_[BPM]BPM_[Key].wav`）に沿ってファイル名へ付け足す（リネーム）機能を提供。
  - リネーム実行後、管理フォルダへの再配置およびSQLiteデータベースへの登録情報を自動同期。

### 1.3 フォルダ構成 & 持続的なライブラリ管理 (FR-3)
- **FR-3.1**: **管理型ライブラリフォルダ構成**:
  - 継続的な利用・整理のため、ソフト専用の管理ライブラリディレクトリ構造を定義・運用：
    ```
    SoundLibrary/
    ├── Library/
    │   ├── Loop/
    │   │   ├── [Genre_or_Pack]/
    │   │   │   └── [Instrument]/
    │   │   │       └── [BPM]_[Key]_[OriginalName].wav
    │   │   └── Other/                 # パック/ジャンル不明なループ音源
    │   ├── Oneshot/
    │   │   ├── [Instrument]/
    │   │   │   └── [Key]_[OriginalName].wav
    │   │   └── Other/                 # 楽器不明なワンショット音源
    │   └── Other/                     # Type判定不能な音源
    ├── Imports/                       # 新規音源投入用フォルダ
    ├── Database/
    │   └── library.db                 # SQLiteインデックスDB
    └── Backups/                       # データベース自動バックアップ
    ```
- **FR-3.2**: **インポート & 自動整理機能**:
  - 任意のフォルダ（例: 現在の `Loop/`, `Oneshot/` フォルダ）やZIPアーカイブを指定してインポートを実行すると、メタデータを解析した上で管理フォルダへ自動コピー・分類配置（未特定項目は `Other` サブディレクトリに安全に配置）。
- **FR-3.3**: **フォルダ監視 & 同期**:
  - ライブラリフォルダや特定フォルダの変更を再スキャンし、追加・削除をDBに同期。

### 1.4 音声プレビュー & 波形表示 (FR-4)
- **FR-4.1**: **オーディオ再生エンジン**:
  - 低レイテンシー再生（`PyQt6.QtMultimedia` / `sounddevice` 等による安定再生）。
  - 再生、一時停止、停止、シーク位置変更、マスター音量調整。
- **FR-4.2**: **波形（Waveform）描画**:
  - 音声データの振幅データを高速レンダリングし、現在再生位置を示す再生バーを表示。
  - 波形上をクリックして任意位置へジャンプ（シーク）。
- **FR-4.3**: **自動再生（Auto-Play）機能**:
  - リストで音源を選択した際、即座に試聴再生を開始する機能（ON/OFF切り替え可能）。
- **FR-4.4**: **ループ再生（Loop Playback）機能**:
  - Loop音源の試聴時に、終端に達したら先頭へシームレスにループ再生する機能（ON/OFF切り替え可能）。

### 1.5 DAW連携 & ドラッグ＆ドロップ (FR-5)
- **FR-5.1**: **DAWへの直接ドラッグ＆ドロップ**:
  - リスト上の音源アイテムをマウスでドラッグし、Cakewalk by BandLab, Sonar, Cubase, Studio One, FL Studio, Ableton Live等のDAWトラックやエクスプローラーへ直接ドロップ可能（OS標準の `application/x-qt-windows-mime` / `text/uri-list` ドロップターゲット対応）。
- **FR-5.2**: **エクスプローラー連携 & パスコピー**:
  - 右クリックメニューから「エクスプローラーで表示」「ファイルパスをコピー」を実行可能。

### 1.6 ソート・フィルタリング・検索 (FR-6)
- **FR-6.1**: **ファセットフィルター**:
  - Type（All / Loop / Oneshot / Other）
  - Instrument（All / Bass / Drums / Kick / Clap / Synth / Guitar / ... / Other）
  - Genre / Pack（動的リスト + Other）
  - Key（C, C#, D, D#, E, F, F#, G, G#, A, A#, B × Major/Minor / Unset）
  - BPM（最小値〜最大値スライダー、または特定BPM ±5 などの範囲指定）
  - Creator（BandLab, ... / Other）
- **FR-6.2**: **フリーワード検索**:
  - ファイル名、タグ、パック名、楽器名に対するインクリメンタル高速全文検索。
- **FR-6.3**: **マルチカラムソート**:
  - 各列（ファイル名、BPM、キー、楽器、日付等）をクリックして昇順・降順ソート。

### 1.7 対応オーディオフォーマット (FR-7)
- **FR-7.1**: WAV, MP3, FLAC, AIFF, OGG 形式の読み込み・プレビュー再生・メタデータ解析に対応。

---

## 2. Non-Functional Requirements (非機能要件)

### 2.1 パフォーマンス & 応答性 (NFR-1)
- **NFR-1.1**: 数万件規模のサンプルライブラリでもUIがフリーズしない仮想化リスト/テーブルレンダリング。
- **NFR-1.2**: プレビュー再生開始レイテンシー 50ms 未満。
- **NFR-1.3**: SQLiteインデックスによる検索クエリ応答時間 10ms 未満。

### 2.2 堅牢性 & 耐障害性 (NFR-2 / Resiliency Baseline)
- **RESILIENCY-01 (Workload Criticality)**: 
  - メタデータDBおよびライブラリファイル管理を最重要コンポーネントとして保護。
- **RESILIENCY-02 (Recovery Targets)**:
  - ローカルデスクトップ向けRTO/RPO: RTO < 1分（アプリ再起動・DB再インデックス）、RPO = 0〜数分（SQLite WALモードによる即時コミット、起動時自動バックアップ）。
- **RESILIENCY-10 (Failure Isolation)**:
  - 破損したオーディオファイルや未対応形式に遭遇してもアプリがクラッシュせず、エラーをスキップしてログに記録。
- **RESILIENCY-12 (Data Backup)**:
  - `library.db` の起動時/終了時自動バックアップ（直近5世代保持）および整合性チェック（`PRAGMA integrity_check`）。

### 2.3 テスト & 品質保証 (NFR-3 / Property-Based Testing)
- **PBT-02 (Round-Trip / Parser Properties)**:
  - ファイル名パーサー（`parse_sample_filename`）およびメタデータシリアライザに対する Hypothesis を用いたプロパティベーステスト。
- **PBT-03 (Invariant Properties)**:
  - BPM/Key正規化関数における不変条件テスト（BPMは常に正数またはNone、キー表記は常に規定の標準フォーマットに収まること、未分類属性は常に"Other"に収束すること）。
- **PBT-09 (Framework Selection)**:
  - Python標準 `unittest` / `pytest` + `hypothesis` を採用。

### 2.4 保守性 & 拡張性 (NFR-4)
- **NFR-4.1**: モジュール構造の分離（Core Engine, Database, Audio Player, UI Layers, Parser）。
- **NFR-4.2**: 設定ファイル（JSON形式）によるライブラリパスやオーディオデバイス設定の外部化。

---

## 3. Extension Compliance Summary

| Extension | Status | Rationale |
|---|---|---|
| Security Baseline | N/A (Opted Out) | 個人利用のローカルデスクトップアプリケーションのためスキップ |
| Resiliency Baseline | Compliant (Enforced) | ローカルDB保護、壊れたファイルへの耐性、自動バックアップ等の設計を反映 |
| Property-Based Testing | Compliant (Partial) | ファイル名解析・正規化関数に対するHypothesisテストを要件化 |

---
