# Unit 3 Functional Design: Business Logic Model (`business-logic-model.md`)

## 1. Component Architecture & Interactions

```
+-------------------------------------------------------------------------------+
| [Unit 3: Audio Engine & Waveform Visualizer]                                  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | AudioPlayerService (PyQt6 QMediaPlayer / QAudioOutput)                   |  |
|  |  - play(file_path: str, is_loop: bool = False)                          |  |
|  |  - pause() / resume() / stop()                                          |  |
|  |  - seek(position_ms: int) / seek_ratio(ratio: float)                    |  |
|  |  - set_volume(volume: float) / set_muted(muted: bool)                   |  |
|  |  - Signals: state_changed, position_changed, duration_changed, eof      |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | WaveformExtractor (Lightweight NumPy peak decimation)                    |  |
|  |  - extract_peaks(file_path: str, num_bins: int = 300) -> WaveformData   |  |
|  |  - LRU In-Memory Cache (Stores recent ~100 waveform peak arrays)        |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | WaveformWidget (PyQt6 QPainter Custom Widget)                           |  |
|  |  - render_peaks(waveform_data: WaveformData, progress_ratio: float)     |  |
|  |  - mouse_press / mouse_drag -> seek_ratio signal                        |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 2. Business Logic Specifications

### 2.1 Waveform Peak Decimation Algorithm
1. WAVファイルから先頭最大30秒または全体を 16-bit / 32-bit float で読み込む。
2. サンプル配列全体を $N$ 個（デフォルト 300個）の等分割ビン（Bin）に分割する。
3. 各ビン $i$ 内の $\min(s_i)$ および $\max(s_i)$ を抽出する。
4. 全体の最大絶対値で正規化（Normalize）し、描画時に安定した波形振幅（-1.0 〜 +1.0）を提供する。
5. 計算結果（`WaveformData`）を LRU キャッシュ（容量 100件）に保持し、リストの再選択時に 0ms で即座に描画可能とする。

### 2.2 Audio Player State Machine & Looping Policy
- **Play Transition**: `load(file_path)` ➔ `play()` ➔ `PLAYING`
- **Pause Transition**: `pause()` ➔ `PAUSED`
- **Stop Transition**: `stop()` ➔ `STOPPED` (シーク0に戻る)
- **Seek Operation**: 任意の再生位置 $P_{ms} \in [0, \text{duration}]$ へシーク。再生中であればシーク後も再生を継続、一時停止中であれば一時停止を維持。
- **End-of-Media (EOF) Trigger**:
  - `loop_playback_enabled == True` または音源種別が `Loop` の場合: `seek(0)` ➔ 即座に `play()` を再実行（シームレスループ）。
  - それ以外（`Oneshot` / `Other` かつ `loop_playback_enabled == False`）: `stop()` ➔ `STOPPED`。
