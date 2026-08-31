# Unit 1 Functional Design: Business Rules & Validation (`business-rules.md`)

## 1. Business Rules

### BR-101: Duplicate File Resolution Rule (重複ファイル解決ルール)
- **Rule**: 管理ライブラリへのインポート時、保存先ディレクトリに同一ファイル名がすでに存在する場合、既存ファイルを上書きせず、ファイル名のベース部末尾に `_1`, `_2` のような連番をインクリメント付与して保存する。
- **Example**:
  - 既存: `Library/Oneshot/kick/CDV1_Kick_17_kick_BANDLAB.wav`
  - 新規インポート: `Library/Oneshot/kick/CDV1_Kick_17_kick_BANDLAB_1.wav`
- **Validation**: 物理ファイル名とDBレコードの `file_name` および `file_path` が完全に一致すること。

### BR-102: Import Mode Flexibility Rule (コピー/移動選択ルール)
- **Rule**: インポート処理はデフォルトで「コピー方式（元ファイルを保護）」として実行される。ユーザー設定（`LibraryConfig.copy_mode == "move"`）が指定された場合のみ、元ファイルを移動（削除）する。
- **Validation**: コピー元のファイルが読み取り専用等の場合でも、エラーを出さずに安全にコピーを完了すること。

### BR-103: "Other" Fallback & Isolation Rule (「Other」隔離ルール)
- **Rule**: 
  - `sample_type` が不明な音源は、すべて `Library/Other/` ディレクトリに格納され、DB上でも `sample_type = 'Other'` として記録される。
  - `sample_type` は判明しているが `instrument` や `genre` が特定できない場合、該当するサブディレクトリの `Other/` フォルダへ格納される。
- **Validation**: 「Other」に分類された音源はファセット検索で「Other」タグを選択することで漏れなく抽出できること。

### BR-104: Database Integrity & WAL Mode Rule (DB堅牢性ルール / RESILIENCY-01)
- **Rule**: SQLite接続確立時、必ず `PRAGMA journal_mode = WAL` を適用し、同時実行時の読み取りロック競合を防止する。
- **Validation**: アプリケーション起動時に `PRAGMA integrity_check` を実行し、結果が `"ok"` でない場合は直近の有効なバックアップからの復旧を試みる。

### BR-105: Automated Snapshot Backup Rule (自動バックアップルール / RESILIENCY-12)
- **Rule**: 
  - アプリ起動時および正常終了時に、`SoundLibrary/Backups/` ディレクトリへ現在の日時を付与したスナップショット（`library_backup_YYYYMMDD_HHMMSS.db`）を自動保存する。
  - バックアップファイル数は常に最新の5世代（`max_backup_generations`）を上限とし、超過分は古い順に自動削除される。
- **Validation**: バックアップ作成処理は数ミリ秒で完了し、UIをブロックしないこと。

### BR-106: Metadata Update & Synchronization Rule (メタデータ更新同期ルール)
- **Rule**: GUI等で音源のメタデータ（タグ、BPM、Key、楽器等）が編集された場合、即座にSQLiteデータベースのレコードを更新し、`updated_at` タイムスタンプを現在日時に更新する。

### BR-107: Sound Source Deletion Rule (音源削除・登録解除ルール)
音源管理ソフトにおける削除操作は、ユーザーの意図に合わせて以下の2段階のオプションを提供します：

1. **ライブラリから登録解除（DBレコードのみ削除）**:
   - **動作**: データベース上の `samples` テーブルから該当レコードを削除する。実ファイル（`SoundLibrary/Library/...` 配下）はディスク上にそのまま残す。
   - **用途**: 「管理ソフトの一覧からは外したいが、ファイル自体は保管しておきたい」場合。
2. **実ファイルを含めて削除（ファイル削除＋DB削除）**:
   - **動作**: データベースのレコードを削除すると同時に、実ファイルをディスクから安全に削除（Windowsの場合は「ごみ箱（Recycle Bin）」へ移動）する。
   - **用途**: 「不要な音源を完全にディスク容量ごと整理・消去したい」場合。
3. **安全対策（誤操作防止）**:
   - 削除実行時は必ず確認ダイアログを表示（単一削除・複数一括削除の双方に対応）。
   - 一括削除時、対象件数（例: 「選択された 15 件の音源を削除しますか？」）を明示。
   - 再生中の音源を削除する場合は、再生を直ちに安全に停止してから削除処理を実行する。

---

## 2. Validation Logic & Constraints

| エンティティ | 検証項目 | 制約 / 期待値 | 違反時の挙動 |
|---|---|---|---|
| `SampleItem` | `file_path` | 実在するパス、非空文字列 | 例外発生、スキップ |
| `SampleItem` | `sample_type` | `"Loop"`, `"Oneshot"`, `"Other"` のいずれか | `"Other"` にフォールバック |
| `SampleItem` | `bpm` | 正の浮動小数点（10.0 〜 999.0）または `None` | `None` にフォールバック |
| `SampleItem` | `duration_sec` | 0.0 以上の数値 | 0.0 に補正 |
| `LibraryConfig` | `max_backup_generations` | 1 〜 50 の正の整数 | デフォルト値（5）に補正 |
