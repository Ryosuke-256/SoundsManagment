# Unit 1: Code Generation Plan (Data Model, Database & Library Manager)

## 1. Overview
Unit 1（Data Model, Database & Library Manager）のソースコード、ユニットテスト、およびドキュメントを生成するための詳細実行計画書です。

### 1.1 Story Traceability (担当ユーザーストーリー)
- **Story 2.1**: 音源インポート・自動フォルダ整理 & 「Other」フォールバック（フォルダ階層、ファイルルーティング、連番重複解決）
- **Story 2.2**: 「Other」音源の確認と手動メタデータ編集・タグ付け（`update_sample` API）
- **Story 2.3**: データベース永続化・高速検索同期・自動バックアップ（SQLite WAL、Integrity Check、5世代スナップショット）
- **Story 1.1**: 多角的なファセット絞り込みとソートによる音源検索（パラメータ化クエリビルダー、B-Treeインデックス）

### 1.2 Target Directory & Code Location Rules
- **Application Code**:
  - `src/core/models.py`, `src/core/config.py`
  - `src/database/db_manager.py`, `src/database/repository.py`
  - `src/storage/file_manager.py`
- **Unit Tests**:
  - `tests/test_unit1_database.py`
  - `tests/test_unit1_storage.py`
- **Documentation**:
  - `aidlc-docs/construction/unit-1-data-and-library/code/code-summary.md`

---

## 2. Explicit Generation Steps

- [x] **Step 1: Project Structure Setup (Greenfield)**
  - `src/core/`, `src/database/`, `src/storage/`, `tests/` ディレクトリおよび各 `__init__.py` を作成。

- [x] **Step 2: Core Domain Models & Config Generation**
  - `src/core/models.py`: `SampleItem`, `SearchFilter`, `ImportSummary`, `BackupInfo` を `@dataclass` で定義。
  - `src/core/config.py`: `LibraryConfig` クラス（JSON設定ロード/保存、デフォルトパス解決）を実装。

- [x] **Step 3: Database Manager Generation (SQLite WAL & Backup)**
  - `src/database/db_manager.py`: `DatabaseManager` クラス（Thread-Local Connection、WALモード設定、スキーマ作成、`PRAGMA integrity_check`、5世代スナップショット自動バックアップ・手動復元機能）を実装。

- [x] **Step 4: Sample Repository Layer Generation**
  - `src/database/repository.py`: `SampleRepository` クラス（CRUD操作、バッチINSERT、パラメータ化ファセット検索クエリビルダー、ソートカラム検証、オンデマンドインデックス集計）を実装。

- [x] **Step 5: Library File Manager & Safe Storage Generation**
  - `src/storage/file_manager.py`: `LibraryFileManager` クラス（管理フォルダ階層作成、ファイルルーティング `Loop/`, `Oneshot/`, `Other/`、重複時連番付与、2段階コミット風ロールバック保護、Windowsごみ箱移動 `send2trash` 統合）を実装。

- [x] **Step 6: Unit 1 Unit Tests Generation**
  - `tests/test_unit1_database.py`: DB初期化、WAL設定、CRUD、検索フィルタリング、バックアップ/整合性チェックのテスト。
  - `tests/test_unit1_storage.py`: フォルダ作成、ルーティング、重複連番解決、ごみ箱移動削除、ロールバック保護のテスト。

- [x] **Step 7: Unit 1 Code Summary & Documentation Generation**
  - `aidlc-docs/construction/unit-1-data-and-library/code/code-summary.md` を作成し、Unit 1の実装成果物を要約。
