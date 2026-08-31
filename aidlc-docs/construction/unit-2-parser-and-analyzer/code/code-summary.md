# Unit 2: Code Summary (Metadata Parser & Audio Signal Analyzer)

## 1. Overview
Unit 2（Metadata Parser & Audio Signal Analyzer）のコード実装およびテスト検証が完了しました。

### 1.1 Implemented Modules & Responsibilities
- **`src/parser/filename_parser.py` (`FilenameParser`, `ParsedMetadata`)**:
  - 高速正規表現・トークン分解によるメタデータ（Type, BPM, Key, Instrument, Genre, Creator）抽出（1,000ファイル < 50ms）。
  - フラット記号（`Db`➔`C#`、`D♭`➔`C#`）の標準化マッピング。
  - 未分類・未特定の個別属性に対する安全な「Other」フォールバック分類。
- **`src/analyzer/audio_analyzer.py` (`AudioSignalAnalyzer`, `AudioAnalysisResult`)**:
  - 先頭15〜30秒のストリーミングWAV読み込み（メモリ消費 < 10MB/ファイル）。
  - STFTオンセットスペクトルフラックスと自己相関による 40〜240 BPM テンポ検出。
  - 12音階事前計算クロマグラム基底行列とKrumhansl-Schmuckler調性プロファイル相関によるKey推定。
  - 破損WAVやデコード失敗時のSafe Analysis Result（Null Object）パターン（RESILIENCY-10）による耐障害性保護。
- **`src/analyzer/auto_renamer.py` (`AutoRenamer`, `RenamePreviewItem`)**:
  - `[BaseName]_[BPM]BPM_[Key].[ext]` 形式の標準命名規則フォーマッター。
  - 既存の末尾BPM/Keyタグを置換し、二重追記を防止するスマートクリーン処理。
  - UI確認・承認用プレビューリスト生成。
- **`src/analyzer/batch_coordinator.py` (`BatchAnalysisCoordinator`)**:
  - `concurrent.futures.ThreadPoolExecutor` によるマルチスレッド並行解析。
  - UIへの進捗コールバック通知（`completed_count`, `total_count`, `current_filename`）。

---

## 2. Test Verification Summary
全22件のテスト（Unit 1: 9件、Unit 2: 13件）が正常にパスしました。

### 2.1 Automated Test Execution Results
- `tests/test_unit2_parser.py`: 5 tests PASSED (BandLab loop, oneshot, flat normalization, fallback to Other, <50ms benchmark)
- `tests/test_unit2_analyzer.py`: 5 tests PASSED (Synthetic 120BPM click, A440Hz tone, corrupted file resilience, auto renamer, thread pool batch)
- `tests/test_unit2_pbt.py`: 3 property tests PASSED (Hypothesis PBT-02/03 crash resilience, key normalization invariant, round-trip structured preservation)
- `tests/test_unit1_database.py`: 4 tests PASSED
- `tests/test_unit1_storage.py`: 5 tests PASSED
- **Total**: 22 passed in 1.90s (PyTest) / 0.624s (UnitTest).
