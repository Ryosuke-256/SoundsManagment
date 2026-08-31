# 結合テスト手順書（Integration Test Instructions）

## 1. 目的
疎結合に設計されたモジュール間のデータ連携およびイベント処理が正しく連動して動作することを検証します：
- フォルダ一括インポート連携（`ImportWorker` ＋ `FilenameParser` ＋ `LibraryFileManager` ＋ `SampleRepository`）
- 定量音声解析＆自動リネーム連携（`BatchAnalysisCoordinator` ＋ `AutoRenamer` ＋ `LibraryFileManager` ＋ `SampleRepository`）
- UI イベント統括連携（`FacetFilterWidget` → `MainWindow` → `SampleTableModel` → `WaveformWidget` → `AudioPlayerService`）

---

## 2. 主要な結合テストシナリオ

### シナリオ 1: 音源フォルダの一括インポートと管理フォルダ・DB登録
1. ユーザーが未整理の音源フォルダを選択してインポートを開始。
2. `ImportWorker` がファイルを探索し、`FilenameParser.parse_filename` でメタデータを抽出。
3. `LibraryFileManager.import_single_file` が管理フォルダ（`Library/Loop/<Genre>/<Inst>` 等）へファイルを安全コピー。
4. `SampleRepository.insert_samples_batch` が単一トランザクションでデータベースへメタデータを高速一括登録。
5. `MainWindow` のファセットカウンタおよびテーブルビューが自動更新。

### シナリオ 2: 定量音声解析および命名規則自動リネーム（Story 2.4 / FR-2.5）
1. ユーザーがテーブル上の音源を選択し、「音声解析＆自動リネーム」ダイアログを開く。
2. `BatchAnalyzeWorker` がマルチスレッドで Onset BPM 解析およびクロマ調性解析を実行。
3. `AutoRenamer` が解析結果に基づき新ファイル名（`[BaseName]_[BPM]BPM_[Key].[ext]`）のプレビューを生成。
4. ユーザーが差分を確認して「リネーム適用」を実行。
5. `LibraryFileManager.rename_library_file` が実ファイルをアトミックにリネームし、`SampleRepository.update_sample` がDBレコードを同期更新。

### シナリオ 3: DAW へのドラッグ＆ドロップ連携（Cakewalk / Sonar / Studio One）
1. ユーザーが音源テーブルから行を選択して DAW トラックへドラッグを開始。
2. `SampleTableView.startDrag` がドラッグ開始前に実ファイル存在確認（`os.path.isfile` [BR-403]）を実行。
3. `SampleTableModel.mimeData` が `QUrl.fromLocalFile` を含む Windows OLE `text/uri-list` 形式データを生成。
4. DAW がドロップイベントを受け取り、再生ヘッド位置にオーディオクリップを配置。

---

## 3. 結合テストの自動実行コマンド
```powershell
# 結合テストスイートの実行
pytest -v tests/test_unit4_gui.py::TestMainWindowIntegration
pytest -v tests/test_unit4_gui.py::TestAudioAnalyzerDialog
pytest -v tests/test_unit4_gui.py::TestAsyncWorkers
```
- **期待結果**: すべての結合シナリオがタイムアウトや例外なく **合格（PASS）** すること。
