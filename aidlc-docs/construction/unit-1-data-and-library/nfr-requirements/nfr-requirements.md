# Unit 1 NFR Requirements: Data Model, Database & Library Manager (`nfr-requirements.md`)

## 1. Executive Summary
本ドキュメントは、**Unit 1: Data Model, Database & Library Manager** における性能（Performance）、スケーラビリティ（Scalability）、可用性・耐障害性（Reliability & Fault Tolerance）、およびデータ保全性（Data Integrity）に関する非機能要件を定義します。

---

## 2. Performance Requirements (性能要件)

| 項目 | 指標 / 目標値 | 達成手段・設計指針 |
|---|---|---|
| **ファセット検索応答時間** | **< 20 ms**（10,000音源規模） | 主要属性（Type, Instrument, Genre, BPM, Key, Creator, Favorite）へのB-Treeインデックス適用 |
| **フリーワード部分一致検索** | **< 50 ms**（10,000音源規模） | 最適化されたSQLプリペアドステートメントによるパラメータ化クエリ実行 |
| **バッチインポート処理速度** | **> 200 ファイル/秒** | 100〜500件単位のバッチトランザクションコミット（Q2: A） |
| **起動時DB接続 & 整合性検証** | **< 100 ms** | `PRAGMA integrity_check` + WALモードによる高速起動 |
| **バックアップスナップショット作成** | **< 50 ms** | SQLiteのオンラインバックアップAPIまたはファイルコピーによる高速世代保存 |

---

## 3. Scalability & Capacity Requirements (スケーラビリティ・容量要件)

- **ライブラリ想定規模**: 最大10,000音源ファイル（Q1: A 高速応答優先）。
- **データベースサイズ**: 10,000レコード時で約 10MB 〜 20MB（SQLiteインデックス含む）。
- **メモリフットプリント**: DBマネージャーおよびリポジトリ層で 50MB 未満を維持。
- **ディスクI/O効率**: 一括インポート時のディスク書き込み頻度をバッチコミットで最小化。

---

## 4. Reliability & Fault Tolerance Requirements (耐障害性要件 / RESILIENCY-01, 12)

### 4.1 SQLite WAL (Write-Ahead Logging)
- **クラッシュ耐性**: システムの予期せぬ電源断やOSクラッシュが発生した場合でも、WALログによりDBファイルの破損を防止。
- **同時実行性**: 読み取りクエリ（UI検索）が書き込みトランザクション（インポート・更新）をブロックしない設計（`PRAGMA synchronous = NORMAL`）。

### 4.2 Automated Backup & Disaster Recovery (Q3: B)
- **世代バックアップ**: アプリ起動時および正常終了時に `SoundLibrary/Backups/library_backup_YYYYMMDD_HHMMSS.db` を保存（直近5世代保持、自動ローテーション）。
- **破損検知と手動選択復旧**:
  - 起動時チェックで破損が検知された場合、システムを即時停止させず、バックアップ履歴一覧ダイアログを表示。
  - ユーザーが選択した正常な世代バックアップファイルを `SoundLibrary/Database/library.db` に復元して自動再起動。

### 4.3 Safe File Operations (RESILIENCY-10)
- **重複リネーム追加**: 同名ファイルが存在する場合は上書きせず連番（`_1`, `_2`）を自動付与して双方を保全。
- **ごみ箱移動削除**: 音源ファイル削除時は直接物理抹消せず、Windowsごみ箱（Recycle Bin）へ移動して誤削除復元を可能にする。

---

## 5. Security & Isolation Requirements (セキュリティ・分離要件)

- **SQLインジェクション対策**: すべての動的クエリでパラメータバインディング（`?` プレースホルダー）を強制。
- **ソートカラム検証**: ソート対象カラム名をホワイトリスト配列で厳格検証。
- **パストラバーサル防止**: ファイルパス解決時に `os.path.abspath` および `pathlib.Path.resolve()` を用い、管理ライブラリ外への不正アクセスを防止。
