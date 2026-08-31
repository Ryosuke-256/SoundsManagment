# 単体テスト実行手順書（Unit Test Execution Instructions）

## 1. 概要
本単体テストスイートは、ドメインデータモデル、SQLite データベース操作、ファイル名メタデータパース、音声信号処理（Onset/BPM & Chroma/Key）、波形ピーク抽出・キャッシュ、およびデスクトップ GUI コンポーネントを網羅的に検証します。

---

## 2. 単体テストの実行手順

### 1. ユニット別単体テストの実行
各機能モジュールごとに個別にテストを実行できます。

```powershell
# Unit 1: データベース・ストレージ管理テスト（9テスト）
pytest -v tests/test_unit1_database.py tests/test_unit1_storage.py

# Unit 2: メタデータパーサー・DSP音声解析テスト（10テスト）
pytest -v tests/test_unit2_parser.py tests/test_unit2_analyzer.py

# Unit 3: オーディオ再生・波形描画エンジンテスト（13テスト）
pytest -v tests/test_unit3_audio.py tests/test_unit3_waveform.py

# Unit 4: デスクトップGUI・テーブルモデルテスト（7テスト）
pytest -v tests/test_unit4_gui.py
```

### 2. プロパティベーステスト（Hypothesis）の実行
境界値や異常値に対する不変性を検証するプロパティベーステストを実行します。

```powershell
# Unit 2 & Unit 3 のプロパティベーステスト（5テスト）
pytest -v tests/test_unit2_pbt.py tests/test_unit3_pbt.py
```

### 3. テスト期待結果
- **Unit 1**: 9 テスト成功（CRUD、WAL モード、ファセット検索、バックアップ、フォルダルーティング、安全削除）。
- **Unit 2**: 13 テスト成功（BandLab 命名規則パース、異体字・Unicode 記号正規化、Onset BPM 解析、クロマ調性解析、並列実行性、PBT 不変性）。
- **Unit 3**: 15 テスト成功（再生ライフサイクル、シーク、音量、モノラル/ステレオ波形ピーク抽出、LRU キャッシュ破棄、シーク不変性）。
- **Unit 4**: 7 テスト成功（仮想テーブル行バインド、MIME text/uri-list 生成、ファセットフィルタシグナル、一括インポート、Story 2.4 自動リネームダイアログ、メインウィンドウ結合）。
- **全体合計**: **44 / 44 テスト成功（合格率 100%）**。

---

## 3. テスト失敗時のトラブルシューティング
1. **DB ロックエラーが発生した場合**: 一時的な SQLite `.db-wal` ファイルの排他ロックを解除するため、実行中のバックグラウンドプロセスがないか確認してください。
2. **音声/波形テストで失敗した場合**: テスト用 16-bit PCM WAV ファイルの生成処理でクリッピングが発生していないか確認してください。
3. **GUI テストでタイムアウトが発生した場合**: `QApplication` インスタンスが正しく初期化され、テスト環境下でモーダルダイアログがブロックしていないか確認してください。
