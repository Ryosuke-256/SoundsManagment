# Unit 1 Functional Design: Business Logic Model (`business-logic-model.md`)

## 1. Database Schema & Indexing Design

### 1.1 SQLite Table Definition: `samples`
```sql
CREATE TABLE IF NOT EXISTS samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_size INTEGER NOT NULL DEFAULT 0,
    file_hash TEXT NOT NULL DEFAULT '',
    sample_type TEXT NOT NULL DEFAULT 'Other',
    instrument TEXT NOT NULL DEFAULT 'Other',
    genre TEXT NOT NULL DEFAULT 'Other',
    bpm REAL,
    key_root TEXT,
    key_scale TEXT,
    creator TEXT NOT NULL DEFAULT 'Other',
    duration_sec REAL NOT NULL DEFAULT 0.0,
    sample_rate INTEGER NOT NULL DEFAULT 44100,
    channels INTEGER NOT NULL DEFAULT 2,
    bit_depth INTEGER NOT NULL DEFAULT 16,
    format TEXT NOT NULL DEFAULT 'WAV',
    tags TEXT NOT NULL DEFAULT '',
    is_favorite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 1.2 Performance & Faceted Search Indexes
```sql
-- 高速な絞り込みのためのインデックス定義
CREATE INDEX IF NOT EXISTS idx_samples_type ON samples(sample_type);
CREATE INDEX IF NOT EXISTS idx_samples_instrument ON samples(instrument);
CREATE INDEX IF NOT EXISTS idx_samples_genre ON samples(genre);
CREATE INDEX IF NOT EXISTS idx_samples_bpm ON samples(bpm);
CREATE INDEX IF NOT EXISTS idx_samples_key ON samples(key_root, key_scale);
CREATE INDEX IF NOT EXISTS idx_samples_creator ON samples(creator);
CREATE INDEX IF NOT EXISTS idx_samples_favorite ON samples(is_favorite);
CREATE INDEX IF NOT EXISTS idx_samples_hash ON samples(file_hash);
```

### 1.3 WAL Mode & Pragma Configuration (Resiliency)
```sql
-- 高速読み書きとクラッシュ耐性を担保するPRAGMA設定
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA foreign_keys = ON;
PRAGMA busy_timeout = 5000;
```

---

## 2. Dynamic Search Query Construction

`SampleRepository.search_samples(filter: SearchFilter)` は、`SearchFilter` オブジェクトから動的にパラメータ化SQL（Prepared Statement）を構築します：

1. **WHERE句の条件合成**:
   - `sample_types`: `sample_type IN (?, ?...)`
   - `instruments`: `instrument IN (?, ?...)`
   - `genres`: `genre IN (?, ?...)`
   - `key_roots`: `key_root IN (?, ?...)`
   - `key_scales`: `key_scale IN (?, ?...)`
   - `bpm_min` / `bpm_max`: `bpm >= ? AND bpm <= ?`
   - `creators`: `creator IN (?, ?...)`
   - `is_favorite_only`: `is_favorite = 1`
   - `query_text`: `(file_name LIKE ? OR tags LIKE ? OR genre LIKE ? OR instrument LIKE ? OR creator LIKE ?)`
2. **ORDER BY句の安全性**:
   - カラム名はホワイトリスト（`id`, `file_name`, `sample_type`, `instrument`, `genre`, `bpm`, `key_root`, `duration_sec`, `created_at`）のみ許可し、SQLインジェクションを完全に防止。
   - `ASC` / `DESC` 指定によるソート。

---

## 3. Managed Library Directory Hierarchy Logic

`LibraryFileManager` は、メタデータ属性に基づいて物理ファイルを以下の構造化パスへルーティングします：

```
SoundLibrary/
├── Library/
│   ├── Loop/
│   │   ├── [Genre]/
│   │   │   └── [Instrument]/
│   │   │       └── [FileName].wav
│   │   └── Other/
│   │       └── [FileName].wav
│   ├── Oneshot/
│   │   ├── [Instrument]/
│   │   │   └── [FileName].wav
│   │   └── Other/
│   │       └── [FileName].wav
│   └── Other/
│       └── [FileName].wav
├── Database/
│   └── library.db
├── Backups/
│   └── library_backup_YYYYMMDD_HHMMSS.db
└── Imports/
```

### 物理パス決定アルゴリズム (`determine_target_path`)
1. **Loopの場合**:
   - ジャンル特定可能（`genre != "Other"`）かつ楽器特定可能（`instrument != "Other"`）:
     ➔ `Library/Loop/[Genre]/[Instrument]/[FileName]`
   - ジャンル特定可能で楽器不明:
     ➔ `Library/Loop/[Genre]/Other/[FileName]`
   - ジャンル不明の場合:
     ➔ `Library/Loop/Other/[FileName]`
2. **Oneshotの場合**:
   - 楽器特定可能（`instrument != "Other"`）:
     ➔ `Library/Oneshot/[Instrument]/[FileName]`
   - 楽器不明の場合:
     ➔ `Library/Oneshot/Other/[FileName]`
3. **Type不明（Other）の場合**:
   ➔ `Library/Other/[FileName]`

---

## 4. Duplicate Resolution & Import Flow

ユーザー回答（Q1: C 連番リネーム追加、Q2: C コピー方式デフォルト）に基づく処理フロー：

```
[インポート対象ファイル]
        │
        ▼
1. メタデータ解析 (FilenameParser)
        │
        ▼
2. ターゲットパス算出 (determine_target_path)
        │
        ▼
3. ターゲットパスに同名ファイルが既に存在するか判定
   ├─► 存在しない場合: そのまま配置
   └─► 存在する場合:
         ファイル名末尾に `_1`, `_2` 等のインクリメント連番を付与
         例: `Kick_01.wav` ➔ `Kick_01_1.wav`
        │
        ▼
4. ファイルの物理配置 (copy_mode に応じて copy2 または move)
        │
        ▼
5. SHA-256ハッシュおよびファイル情報（サイズ、時間等）を取得
        │
        ▼
6. SQLiteデータベース（samples）へINSERT
```

---

## 5. Sound Source Deletion Flow (削除処理ロジック)

音源削除要求に対する実行フロー（単一・複数一括対応）：

```
[音源テーブルで右クリック / Deleteキー押下]
        │
        ▼
1. 削除オプション選択ダイアログ表示
   ├─► Option A: 「ライブラリから登録解除（DBのみ削除、ファイルは保持）」
   └─► Option B: 「実ファイルを完全に削除（ごみ箱へ移動＋DB削除）」
        │
        ▼
2. ユーザー確認（対象件数を明示）
   ├─► キャンセル ➔ 処理中止
   └─► 承認
        │
        ▼
3. 対象音源が現在再生中の場合 ➔ AudioPlayer.stop() を呼び出して再生停止
        │
        ▼
4. Option B（ファイル削除）の場合:
   - `send2trash` または `os.remove` で実ファイルを安全に削除/ごみ箱移動
        │
        ▼
5. `SampleRepository.delete_sample()` または `delete_samples_batch()` で
   SQLiteから対象レコードをDELETE
        │
        ▼
6. UIテーブルビューおよびファセット集計件数を即座にリフレッシュ
```

---

## 6. Automated DB Backup & Integrity Check Logic

ユーザー回答（Q3: A 起動時および終了時）に基づくバックアップライフサイクル：

1. **起動時 (`on_startup`)**:
   - `PRAGMA integrity_check` を実行。整合性OKなら `Backups/library_backup_YYYYMMDD_HHMMSS.db` として複製スナップショットを作成。
   - バックアップフォルダ内のファイル数が `max_backup_generations`（5）を超過している場合、最も古いバックアップファイルを自動削除。
2. **終了時 (`on_shutdown`)**:
   - 未コミットトランザクションを安全にフラッシュ（WALチェックポイント実行: `PRAGMA wal_checkpoint(TRUNCATE)`）。
   - 正常終了時のスナップショットをバックアップフォルダへ保存。
