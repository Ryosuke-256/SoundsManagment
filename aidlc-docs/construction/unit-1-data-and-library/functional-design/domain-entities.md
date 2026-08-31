# Unit 1 Functional Design: Domain Entities (`domain-entities.md`)

## 1. Domain Model Entities

### 1.1 `SampleItem`
音源ライブラリ内の個々の音源ファイルを表現する主ドメインエンティティ。

| フィールド名 | 型 | NULL許可 | デフォルト値 | 説明・制約 |
|---|---|---|---|---|
| `id` | `Optional[int]` | Yes (新規時) | `None` | データベース主キー（Auto Increment） |
| `file_path` | `str` | No | - | 管理ライブラリ内の絶対ファイルパス（一意） |
| `file_name` | `str` | No | - | ファイル名（拡張子含む） |
| `file_size` | `int` | No | `0` | ファイルサイズ（バイト単位） |
| `file_hash` | `str` | No | `""` | SHA-256ハッシュ値（重複検知用） |
| `sample_type` | `str` | No | `"Other"` | 音源タイプ（`"Loop"` / `"Oneshot"` / `"Other"`） |
| `instrument` | `str` | No | `"Other"` | 楽器分類（例: `"guitar"`, `"bass"`, `"kick"`, `"Other"` 等） |
| `genre` | `str` | No | `"Other"` | ジャンル / パック名（例: `"SS_Guitar_Snob"`, `"Other"` 等） |
| `bpm` | `Optional[float]` | Yes | `None` | テンポ（BPM, 例: `174.0`）。不明時は `None` |
| `key_root` | `Optional[str]` | Yes | `None` | 主音（例: `"C#"`, `"D"`, `"E"`）。不明時は `None` |
| `key_scale` | `Optional[str]` | Yes | `None` | 調性（`"minor"` / `"major"`）。不明時は `None` |
| `creator` | `str` | No | `"Other"` | 制作者・提供元（例: `"BANDLAB"`, `"Other"`） |
| `duration_sec` | `float` | No | `0.0` | 再生時間（秒単位、浮動小数点） |
| `sample_rate` | `int` | No | `44100` | サンプリングレート（Hz, 例: 44100, 48000） |
| `channels` | `int` | No | `2` | チャンネル数（1: モノラル, 2: ステレオ） |
| `bit_depth` | `int` | No | `16` | ビット深度（16, 24, 32 bit） |
| `format` | `str` | No | `"WAV"` | 形式（`"WAV"`, `"MP3"`, `"FLAC"`, `"AIFF"`, `"OGG"`） |
| `tags` | `str` | No | `""` | カンマ区切りのカスタムタグ一覧 |
| `is_favorite` | `bool` | No | `False` | お気に入りフラグ |
| `created_at` | `str` | No | ISO 8601 | レコード作成日時 |
| `updated_at` | `str` | No | ISO 8601 | レコード更新日時 |

---

### 1.2 `LibraryConfig`
アプリケーションの環境設定およびライブラリ保存先パスを管理するモデル。

| フィールド名 | 型 | デフォルト値 | 説明 |
|---|---|---|---|
| `library_root` | `str` | `"<Workspace>/SoundLibrary"` | 管理型音源ライブラリのルートディレクトリ |
| `copy_mode` | `str` | `"copy"` | インポート時のファイル操作（`"copy"` または `"move"`） |
| `auto_backup_enabled` | `bool` | `True` | 起動時/終了時自動バックアップの有効化フラグ |
| `max_backup_generations`| `int` | `5` | 保持するバックアップDBの最大世代数 |
| `default_volume` | `float` | `0.8` | 起動時のマスター音量（0.0 〜 1.0） |
| `auto_play_default` | `bool` | `True` | 選択時自動再生のデフォルトON/OFF |
| `loop_playback_default` | `bool` | `True` | ループ再生のデフォルトON/OFF |

---

### 1.3 `SearchFilter`
UIからの多角的な検索・絞り込み要求を表すクエリオブジェクト。

| フィールド名 | 型 | デフォルト値 | 説明 |
|---|---|---|---|
| `query_text` | `Optional[str]` | `None` | フリーワード部分一致検索文字列 |
| `sample_types` | `List[str]` | `[]` | 選択されたType（例: `["Loop"]`） |
| `instruments` | `List[str]` | `[]` | 選択された楽器（例: `["bass", "guitar"]`） |
| `genres` | `List[str]` | `[]` | 選択されたジャンル/パック名 |
| `key_roots` | `List[str]` | `[]` | 選択されたキー主音（例: `["C#", "D"]`） |
| `key_scales` | `List[str]` | `[]` | 選択されたスケール（例: `["minor"]`） |
| `bpm_min` | `Optional[float]` | `None` | BPM下限値（例: `170.0`） |
| `bpm_max` | `Optional[float]` | `None` | BPM上限値（例: `180.0`） |
| `creators` | `List[str]` | `[]` | 選択された制作者 |
| `is_favorite_only` | `bool` | `False` | お気に入りのみ抽出フラグ |
| `sort_column` | `str` | `"file_name"` | ソート基準列 |
| `sort_direction` | `str` | `"ASC"` | ソート順（`"ASC"` または `"DESC"`） |

---

### 1.4 `ImportSummary`
インポート処理完了時に集計結果を返却するデータ構造。

- `total_files_scanned: int`（検出された総ファイル数）
- `imported_count: int`（新規インポート成功件数）
- `duplicate_renamed_count: int`（同名重複により連番リネーム追加された件数）
- `other_classified_count: int`（「Other」に分類された件数）
- `errors_count: int`（読み込み失敗・破損等エラー件数）
- `error_details: List[str]`（エラーメッセージ一覧）
