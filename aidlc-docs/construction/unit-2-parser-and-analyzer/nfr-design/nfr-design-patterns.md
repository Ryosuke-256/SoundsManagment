# Unit 2 NFR Design: Non-Functional Design Patterns (`nfr-design-patterns.md`)

## 1. Resilience & Error Isolation Patterns (RESILIENCY-10)

### 1.1 Safe Analysis Result (Null Object) Pattern
- **Problem**: 破損WAVファイル、未対応コーデック、またはゼロバイトファイルが存在する場合、例外が未処理のまま上位に伝播するとバッチインポートやUIの解析ワーカー全体が中断してしまう。
- **Pattern**: **Safe Result / Null Object パターン** を適用。
  ```python
  def safe_analyze_audio(file_path: str) -> AudioAnalysisResult:
      try:
          return _internal_dsp_analyze(file_path)
      except Exception as e:
          # 例外をトラップし、上位を保護する安全なNull Objectを返却
          return AudioAnalysisResult(
              file_path=file_path,
              estimated_bpm=None,
              estimated_key_root=None,
              estimated_key_scale=None,
              bpm_confidence=0.0,
              key_confidence=0.0,
              suggested_filename="",
              is_loop_candidate=False,
          )
  ```
- **Benefits**: 単一ファイルの破損がシステム全体の可用性を損なわず、安全にスキップ・隔離される。

---

## 2. Performance & Concurrency Patterns

### 2.1 Worker Pool Concurrency Pattern
- **Problem**: 多数の音源ファイルを逐次DSP解析すると、100ファイルで十数秒の待機時間が発生し、UIスレッドが応答不能（フリーズ）になる。
- **Pattern**: `concurrent.futures.ThreadPoolExecutor` を用いた **Worker Pool 並行処理パターン**。
  - プログレスコールバック（`on_progress(completed, total, current_item)`）をサポートし、進捗ダイアログやプログレスバーを円滑に更新。

### 2.2 Singleton Precomputed Chromagram Matrix Pattern
- **Problem**: 12音階の周波数帯域フィルタバンク（Chromagram Filterbank）を行列計算する処理は、FFTビンごとに周波数を対数マッピングするため初期化コストが大きい。
- **Pattern**: **Singleton / Precomputation Caching パターン**。
  - アプリケーション起動時またはモジュール読み込み時に 1回だけ 12音階基底行列（`chroma_filterbank_matrix`）および 24通りのKrumhansl-Schmucklerプロファイル行列を事前計算してメモリキャッシュ。
  - 各ファイル解析時は事前計算行列との行列積（`dot product`）のみで高速にクロマグラムを算出。
