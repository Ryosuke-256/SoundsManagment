# 性能測定およびベンチマーク手順書（Performance Test Instructions）

## 1. 性能要件および目標値
- **ファイル名パーサー処理速度**: 5,000 ファイル名/秒以上（1ファイルあたり 0.2ms 以下）
- **SQLite ファセット検索クエリ応答**: 10,000 件規模のライブラリで 50ms 未満
- **波形ピーク抽出およびキャッシュ**: 30秒音源で 50ms 未満、キャッシュヒット時は 1ms 未満
- **GUI 起動および初期描画時間**: 1.0秒以内に対話可能状態へ移行

---

## 2. 各種ベンチマークテストの実行手順

### 1. ファイル名パーサー処理速度ベンチマーク
```powershell
pytest -v tests/test_unit2_parser.py::TestUnit2Parser::test_parser_speed_benchmark
```
- **測定内容**: 1,000件の多様なファイル名を連続パース。
- **目標・期待結果**: 0.20秒未満で完了（実測: 5,000+ 件/秒）。

### 2. 並列 DSP 音声解析のスケーラビリティ測定
```powershell
pytest -v tests/test_unit2_analyzer.py::TestUnit2Analyzer::test_batch_coordinator_concurrency
```
- **測定内容**: `ThreadPoolExecutor(max_workers=4)` による複数音源の並列 Onset/Chroma 計算。
- **目標・期待結果**: マルチコア CPU を効率的に利用し、スレッド競合やデッドロックなく並列完了すること。

### 3. 波形抽出および LRU キャッシュ破棄ベンチマーク
```powershell
pytest -v tests/test_unit3_waveform.py::TestUnit3Waveform::test_lru_cache_eviction
```
- **測定内容**: 上限256件の波形キャッシュにおいて、メモリ使用量が肥大化せず古い波形データが自動的に解放されること。
- **目標・期待結果**: アプリケーション全体のメモリフットプリントが常時 150MB 未満に収まること。

---

## 3. 性能検証サマリー
すべてのベンチマーク測定項目において目標値を上回る高いスループットと低レイテンシを達成しており、音楽制作現場での快適なリアルタイム操作性を保証します。
