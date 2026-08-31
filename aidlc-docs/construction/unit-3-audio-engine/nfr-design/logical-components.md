# Unit 3 NFR Design: Logical Components (`logical-components.md`)

## 1. Logical Component Architecture

Unit 3 におけるオーディオ再生エンジンおよび波形描画の論理コンポーネント構成：

```
+-------------------------------------------------------------------------------+
| [Unit 3: Audio Engine & Waveform Visualizer]                                  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | AudioPlayerService (PyQt6 QObject / QMediaPlayer / QAudioOutput)        |  |
|  |  - State management (STOPPED, PLAYING, PAUSED)                          |  |
|  |  - Auto-Play & Intelligent Loop playback logic                          |  |
|  |  - Volume / Mute clamping & persistence                                 |  |
|  |  - Qt Custom Signals (state_changed, progress_changed, etc.)            |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | WaveformExtractor & WaveformCache                                       |  |
|  |  - Fast NumPy decimation (min/max peak normalization)                   |  |
|  |  - LRU In-Memory Cache (Capacity: 100 items)                            |  |
|  |  - Safe Null Waveform fallback on corrupted audio                       |  |
|  +-------------------------------------------------------------------------+  |
|                                                                               |
|  +-------------------------------------------------------------------------+  |
|  | WaveformWidget (Custom PyQt6 QWidget)                                   |  |
|  |  - QPainter antialiased rounded bar waveform rendering                 |  |
|  |  - Interactive mouse click & drag seek handler                          |  |
|  |  - Progress overlay gradient & playhead indicator                       |  |
|  +-------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------+
```

---

## 2. Component Detailed Specifications

### 2.1 `AudioPlayerService`
- **Responsibility**: 音声再生、シーク、ループ制御、音量管理、およびQtシグナル発行を担当。
- **Methods**:
  - `play_sample(file_path: str, is_loop: bool = False)`
  - `pause()`, `resume()`, `stop()`
  - `seek_ms(position_ms: int)`, `seek_ratio(ratio: float)`
  - `set_volume(volume: float)`, `set_muted(muted: bool)`
  - `set_auto_play(enabled: bool)`, `set_loop_playback(enabled: bool)`

### 2.2 `WaveformExtractor`
- **Responsibility**: WAVファイルから描画用ピーク配列（200〜400点）を高速生成。
- **Methods**:
  - `extract_peaks(file_path: str, num_bins: int = 300) -> WaveformData`

### 2.3 `WaveformCache`
- **Responsibility**: 直近100件の `WaveformData` をLRU順に保持。
- **Methods**:
  - `get(file_path: str) -> Optional[WaveformData]`
  - `put(file_path: str, data: WaveformData) -> None`
  - `clear() -> None`

### 2.4 `WaveformWidget`
- **Responsibility**: 波形データおよび再生進行状況の描画、マウスインタラクションによるシーク通知。
