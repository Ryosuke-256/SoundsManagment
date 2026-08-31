# Unit 1 Tech Stack Decisions: Data Model, Database & Library Manager (`tech-stack-decisions.md`)

## 1. Selected Technologies & Libraries

| 領域 | 選定技術 / ライブラリ | バージョン / 要件 | 選定理由・トレードオフ |
|---|---|---|---|
| **言語・ランタイム** | **Python 3.10+** | 3.10 / 3.11 / 3.12 | 型ヒント、`dataclass`、および最新の標準ライブラリ機能を活用 |
| **データベース** | **SQLite3 (`sqlite3`)** | Python標準ライブラリ | 外部DBサーバー不要、ゼロ設定、WALモード対応、軽量・高速（<20msクエリ）、単一ファイル管理の容易性 |
| **ファイルシステム操作** | **`pathlib` / `shutil` / `os`** | Python標準ライブラリ | OS差異（Windowsパス区切り）を透過的に吸収し、安全なコピー・リネーム・ディレクトリ作成を提供 |
| **ハッシュ生成** | **`hashlib.sha256`** | Python標準ライブラリ | 音源ファイルの重複検知（フィンガープリント）を高速かつ高精度に実現 |
| **ごみ箱移動（削除）** | **`send2trash`** | 最新安定版 | Windowsごみ箱（Recycle Bin）へファイルを安全に移動し、誤削除時のユーザー復元を可能にする |
| **設定永続化** | **`json`** | Python標準ライブラリ | `config.json` によるシンプルで人間可読な設定管理 |

---

## 2. Technical Decisions & Architectural Rationales

### TD-101: SQLite WAL Mode over Default Rollback Journal
- **Decision**: データベース初期化時に `PRAGMA journal_mode = WAL;` を明示的に発行する。
- **Rationale**: 通常のジャーナルモードでは書き込み中に全読み取りがロックされるが、WAL（Write-Ahead Logging）モードでは読み取りと書き込みが完全並行で実行可能となり、GUIでの検索中にバックグラウンドでインポートが走ってもUIが一切フリーズしない。

### TD-102: Python `dataclasses` for Domain Entities
- **Decision**: `SampleItem`, `LibraryConfig`, `SearchFilter` を `@dataclass` で定義する。
- **Rationale**: メモリオーバーヘッドを最小限に抑え、フィールドの型明示・デフォルト値・辞書/タプル変換（`asdict`, `astuple`）を標準機能で安全に行える。

### TD-103: Batch Transaction Processing for Imports
- **Decision**: `SampleRepository.insert_samples_batch()` で `executemany()` とチャンク分割（500件単位）トランザクションを採用。
- **Rationale**: 1ファイルごとにコミットを発行する場合に比べ、I/O待機時間を約95%削減し、200+ ファイル/秒の高速インポートを達成可能。

### TD-104: Use of `send2trash` for Safe Physical Deletion
- **Decision**: 実ファイル削除時に `os.remove` で即時物理抹消せず、`send2trash` を使用してWindowsごみ箱へ送る。
- **Rationale**: ユーザーが誤って貴重な音源を削除してしまった場合でも、Windowsエクスプローラーのごみ箱から即座に復元できる安全機構（Fail-Safe）を提供する。
