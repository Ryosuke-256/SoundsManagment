# Unit 4: Code Generation Plan (Desktop GUI & DAW Drag-and-Drop Integration)

## Purpose
Unit 4（Desktop GUI & DAW Drag-and-Drop Integration）の実装コードおよびテストコードを順次生成・検証するためのコード生成計画書です。

---

## Proposed Code Generation Steps

- [x] **Step 1: Implement `SampleTableModel` (`src/ui/sample_table_model.py`)**
  - `QAbstractTableModel` を継承し、`SampleRecord` リストをバインド。
  - 列構成: Title, Type, Instrument, Genre, BPM, Key, Creator, Duration。
  - ソート・行検索・フィルタリング対応。
  - DAW ドラッグ用 MIME データ（`text/uri-list`, `QUrl.fromLocalFile`）生成。

- [x] **Step 2: Implement `SampleTableView` (`src/ui/sample_table_view.py`)**
  - `QTableView` を継承し、行選択・ダブルクリック再生・キーボードナビゲーションをサポート。
  - 事前パス検証（`os.path.isfile`）を伴う安全な `startDrag`（Cakewalk / Sonar 等への OLE ドラッグ＆ドロップ）。
  - 右クリックコンテキストメニュー（「ライブラリから登録解除」「ごみ箱へ移動して削除 [BR-107/BR-404]」「エクスプローラーで表示」「プロパティ解析」）。

- [x] **Step 3: Implement `FacetFilterWidget` (`src/ui/facet_filter_widget.py`)**
  - 左側サイドバー。キーワード検索バー、タイプ（Loop / Oneshot / Other）、楽器、ジャンル、キー、BPM 範囲スライダー。
  - 各フィルタ選択変更時に `filter_changed` シグナルを発火。

- [x] **Step 4: Implement Background Workers (`src/ui/workers.py`)**
  - `ImportWorker(QThread)`: フォルダ一括インポート・自動分類・DB登録（キャンセル対応）。
  - `BatchAnalyzeWorker(QThread)`: プロパティ不明音源のバッチ音声解析（キャンセル対応）。
  - `RescanWorker(QThread)`: フォルダ内ファイルの再スキャン・差分同期。

- [x] **Step 5: Implement `AudioAnalyzerDialog` (`src/ui/audio_analyzer_dialog.py`)**
  - Story 2.4 / FR-2.5: プロパティ不明音源の定量解析＆命名規則自動リネーム用専用プレビューダイアログ。
  - 変更前後のファイル名 Diff プレビューテーブル、個別選択チェックボックス、アトミックコミット（リネーム＋DB同期）。

- [x] **Step 6: Implement `MainWindow` (`src/ui/main_window.py`)**
  - 3ペイン DAW フレンドリー構成（左: `FacetFilterWidget`、中央: `SampleTableView`、下部: `WaveformWidget` ＋ トランスポートプレイヤーバー）。
  - メニューバー（File, Edit, Tools, View, Help）、ツールバー（フォルダインポート、自動再生トグル、ループトグル、音量スライダー、ライブラリスキャン）。
  - ステータスバー（総音源数、選択中音源、バックグラウンド進捗バー）。

- [x] **Step 7: Implement Application Entry Point (`src/main.py`)**
  - High-DPI スケーリング有効化、DAW風ダークテーマ QSS スタイルシート適用、DB/ストレージ初期化、例外トラップ。

- [x] **Step 8: Implement Unit 4 Test Suite (`tests/test_unit4_gui.py`)**
  - `SampleTableModel` のデータ提供・ソート・MIME データ生成の単体テスト。
  - `FacetFilterWidget` のシグナル発火テスト。
  - `AudioAnalyzerDialog` および `ImportWorker` の非同期実行・キャンセルテスト。
  - `MainWindow` のレイアウトおよびコンポーネント結合テスト。

- [x] **Step 9: Run Full Test Suite (`pytest -v tests/`)**
  - 全 Unit（Unit 1, Unit 2, Unit 3, Unit 4）の統合回帰テストを実行し、100% 合格を検証。

- [x] **Step 10: Generate Unit 4 Code Summary Artifact (`aidlc-docs/construction/unit-4-gui-and-daw/code/code-summary.md`)**
  - Unit 4 の実装成果物、テスト結果、およびコードサマリーを記録。
