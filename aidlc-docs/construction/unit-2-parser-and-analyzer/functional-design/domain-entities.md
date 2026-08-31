# Unit 2 Functional Design: Domain Entities (`domain-entities.md`)

## 1. Domain Entities & Data Transfer Objects

### 1.1 `ParsedMetadata`
ファイル名およびタグから抽出されたメタデータ構造体。

| フィールド名 | 型 | NULL許可 | デフォルト値 | 説明 |
|---|---|---|---|---|
| `sample_type` | `str` | No | `"Other"` | 音源タイプ（`"Loop"` / `"Oneshot"` / `"Other"`） |
| `instrument` | `str` | No | `"Other"` | 楽器分類（例: `"guitar"`, `"bass"`, `"kick"` 等） |
| `genre` | `str` | No | `"Other"` | ジャンル / サウンドパック名 |
| `bpm` | `Optional[float]` | Yes | `None` | テンポ数値（例: `174.0`） |
| `key_root` | `Optional[str]` | Yes | `None` | 主音（`"C"`, `"C#"`, `"D"`, `"D#"`, `"E"`, `"F"`, `"F#"`, `"G"`, `"G#"`, `"A"`, `"A#"`, `"B"`） |
| `key_scale` | `Optional[str]` | Yes | `None` | 調性（`"minor"` または `"major"`） |
| `creator` | `str` | No | `"Other"` | 制作者・提供元（例: `"BANDLAB"`, `"Other"`） |
| `raw_tokens` | `List[str]` | No | `[]` | 分割されたトークン配列 |

---

### 1.2 `AudioAnalysisResult`
DSP音声信号処理によって算出された定量解析結果オブジェクト（Story 2.4 / FR-2.5）。

| フィールド名 | 型 | NULL許可 | デフォルト値 | 説明 |
|---|---|---|---|---|
| `file_path` | `str` | No | - | 対象音声ファイルの絶対パス |
| `estimated_bpm` | `Optional[float]` | Yes | `None` | オンセット自己相関により検出されたBPM（40〜240） |
| `estimated_key_root` | `Optional[str]` | Yes | `None` | クロマグラム解析により推定された主音（例: `"C#"`, `"D"`） |
| `estimated_key_scale` | `Optional[str]` | Yes | `None` | 推定された調性（`"minor"` または `"major"`） |
| `bpm_confidence` | `float` | No | `0.0` | BPM検出の信頼度スコア（0.0 〜 1.0） |
| `key_confidence` | `float` | No | `0.0` | Key推定の相関スコア（0.0 〜 1.0） |
| `suggested_filename` | `str` | No | `""` | 命名規則に基づき生成されたリネーム後ファイル名候補 |
| `is_loop_candidate` | `bool` | No | `False` | 音声の小節長・拍数からLoop音源と判定されるか |

---

### 1.3 `RenamePreviewItem`
UIダイアログに表示するリネーム前後の比較プレビュー項目。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `sample_id` | `int` | データベース内の対象音源ID |
| `current_path` | `str` | 現在のファイル絶対パス |
| `current_name` | `str` | 現在のファイル名（例: `sample_01.wav`） |
| `new_name` | `str` | リネーム後ファイル名（例: `sample_01_174BPM_C#minor.wav`） |
| `new_path` | `str` | 新しい管理サブディレクトリパス（`Library/Loop/...` 等） |
| `detected_bpm` | `Optional[float]` | 検出されたBPM値 |
| `detected_key` | `Optional[str]` | 検出されたKey表記（例: `"C# minor"`） |
| `is_approved` | `bool` | ユーザーによる適用選択チェック状態 |
