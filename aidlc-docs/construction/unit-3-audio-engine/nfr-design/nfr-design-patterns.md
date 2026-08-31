# Unit 3 NFR Design: Non-Functional Design Patterns (`nfr-design-patterns.md`)

## 1. Resilience & Decoupling Patterns (RESILIENCY-10)

### 1.1 Audio Player Service Wrapper Pattern
- **Problem**: UIウィジェットから `QMediaPlayer` / `QAudioOutput` のAPIを直接呼び出すと、状態管理（STOPPED/PLAYING/PAUSED）やエラー処理がUI各所に散らばり、結合度が高くなる。
- **Pattern**: `QObject` を継承した **`AudioPlayerService` ラッパーパターン** を適用。
  - Qtシグナル（`state_changed`, `position_changed`, `duration_changed`, `error_occurred`）を発行し、UIはシグナル購読のみで描画更新を行う。
  - ヘッドレス環境やテスト環境では、内部でモック／Nullオーディオバックエンドに切り替え可能な設計とする。

---

## 2. Performance & Memory Patterns

### 2.1 Waveform LRU In-Memory Cache Pattern
- **Problem**: 音源リストを矢印キーで連続移動した際、同一音源の波形ピークデータを何度も再計算するとディスクI/OとCPUが無駄に消費される。
- **Pattern**: `collections.OrderedDict` を用いた **LRU In-Memory Cache パターン**（容量100件）。
  ```python
  class WaveformCache:
      def __init__(self, max_size: int = 100):
          self._cache = OrderedDict()
          self._max_size = max_size

      def get(self, file_path: str) -> Optional[WaveformData]:
          if file_path in self._cache:
              self._cache.move_to_end(file_path)
              return self._cache[file_path]
          return None

      def put(self, file_path: str, data: WaveformData) -> None:
          self._cache[file_path] = data
          if len(self._cache) > self._max_size:
              self._cache.popitem(last=False)
  ```
- **Benefits**: メモリ消費は100件で約数十KBと極小でありながら、再選択時の波形描画レイテンシを0msに短縮。

### 2.2 Dynamic Animation Timer Activation Pattern
- **Problem**: 波形シークバーの再生ヘッドを常時描画更新タイマーで回すと、無駄なCPU使用率が発生する。
- **Pattern**: **状態連動タイマーパターン**。
  - `PLAYING` 状態に遷移した時のみ `QTimer.start(33)`（約30 FPS）を起動。
  - `STOPPED` または `PAUSED` 状態では `QTimer.stop()` を実行し、CPU使用率を完全な 0.0% に抑制。
