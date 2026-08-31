# Unit 1 NFR Design: Logical Components (`logical-components.md`)

## 1. Logical Component Architecture

Unit 1 の非機能要件を満たすための内部論理コンポーネント構成：

```
+-------------------------------------------------------------------------+
| [Unit 1: Data Model, Database & Library Manager]                         |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | Database & Connection Management                                  |  |
|  |  - ConnectionFactory (Thread-Local SQLite Connection, WAL Pragma)  |  |
|  |  - IntegrityChecker (PRAGMA integrity_check, Corruption Detection)|  |
|  |  - BackupManager (Online Snapshot, 5-Gen Rotation, Manual Restore)|  |
|  +-------------------------------------------------------------------+  |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | Repository & Query Execution                                      |  |
|  |  - SampleRepository (Parameterized Query Builder, Whitelist Sort) |  |
|  |  - FacetAggregator (On-demand Index Aggregation)                  |  |
|  +-------------------------------------------------------------------+  |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | Storage & File Protection                                         |  |
|  |  - PathRouter (Directory Hierarchy Resolver: Loop/Oneshot/Other)  |  |
|  |  - DuplicateResolver (Sequential Numbering `_1`, `_2`)            |  |
|  |  - BatchImportCoordinator (2-Phase File Copy & Rollback Guard)    |  |
|  |  - SafeDeleter (Windows Recycle Bin via send2trash)               |  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 2. Logical Component Specifications

### 2.1 `ConnectionFactory`
- **Responsibility**: スレッドセーフなSQLiteコネクションの生成と接続設定（WALモード、synchronous=NORMAL、busy_timeout=5000）の自動適用。
- **Scope**: `threading.local` によるスレッド単位インスタンス管理。

### 2.2 `IntegrityChecker` & `BackupManager`
- **`IntegrityChecker`**:
  - アプリケーション起動時にDBファイルのヘッダ・B-Tree構造を検査。
  - 破損検知時は直ちに `DatabaseCorruptedError` を送出。
- **`BackupManager`**:
  - `create_snapshot(db_path, backup_dir)`: `sqlite3.Connection.backup()` でスナップショット保存。
  - `cleanup_old_backups(backup_dir, max_generations=5)`: 超過ファイルを古い順に削除。
  - `get_available_backups(backup_dir) -> List[BackupInfo]`: 復元候補一覧を返却。
  - `restore_backup(backup_file, target_db_path)`: 指定されたバックアップファイルでDBを復元。

### 2.3 `BatchImportCoordinator` & `DuplicateResolver`
- **`DuplicateResolver`**:
  - 対象ディレクトリ内に同名ファイルが存在するかを判定し、存在する場合は `_1`, `_2` の連番をベースファイル名末尾に付与した一意なパスを生成。
- **`BatchImportCoordinator`**:
  - インポート対象ファイルを500件ずつのチャンクに分割。
  - 各チャンクで「物理コピー ➔ DBトランザクションINSERT」を実行し、失敗時は該当チャンクの物理コピーファイルをロールバック削除。

### 2.4 `SafeDeleter`
- **Responsibility**: 音源削除時、ファイルシステム上の実ファイルを `send2trash.send2trash(path)` でWindowsごみ箱へ安全に移動。
- **Fallback**: 万が一 `send2trash` が利用できない環境の場合は、安全に例外を通知。
