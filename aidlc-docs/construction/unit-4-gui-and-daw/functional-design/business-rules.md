# Unit 4 Functional Design: Business Rules (`business-rules.md`)

## 1. GUI & Interaction Business Rules

### BR-401: Non-Blocking UI Responsiveness
- 音源のインポート、一括解析、波形抽出、およびデータベース検索はすべて非同期スレッド（`QThread` / `ThreadPoolExecutor`）または高応答キャッシュで実行し、UI メインスレッドを 16ms 以上ブロックしない。

### BR-402: Faceted Filter Synchronization
- 左側サイドバーでタグやチェックボックス（Type, Instrument, Genre, Key, BPM）を変更した際、即座に検索クエリを発行し、中央テーブルの表示を 20ms 未満で更新する。

### BR-403: DAW Drag & Drop MIME Compliance
- ドラッグ操作時の MIME データには必ず有効な絶対パスのローカルファイル URL（`file:///...`）を設定し、Cakewalk by BandLab / Sonar が直接ファイルアクセスできるようにする。
- 存在しないファイルや移動済みファイルのドラッグは開始しない。

### BR-404: 2-Step Safe Deletion Confirmation (BR-107)
- テーブル上の音源を右クリックまたは Delete キーで削除する際：
  1. 「Remove from Library」（ライブラリから登録解除のみ・ファイル保持）
  2. 「Move to Recycle Bin」（DB削除＋Windowsごみ箱移動）
  の 2 択を確認ダイアログで明示し、誤操作によるデータ消失を防止する。

### BR-405: Safe Analyzer Rename Atomic Commit (Story 2.4 / FR-2.5)
- リネーム実行時、同名ファイルが既に存在する場合は `_1`, `_2` の連番自動付与（Unit 1 ルール）を適用し、上書き破壊を防ぐ。
- ファイルリネーム成功後にのみ DB レコード（`file_path`, `title`, `bpm`, `key`）をコミットする。リネームに失敗した場合は DB を更新せず、エラー行をハイライト表示する。
