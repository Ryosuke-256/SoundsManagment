# Unit 3 Functional Design: Domain Entities (`domain-entities.md`)

## 1. Domain Entities & State Types

### 1.1 `PlaybackState` (Enum)
Represents the current audio playback state of the engine.
- `STOPPED`: 再生停止中。再生位置は0または初期状態。
- `PLAYING`: 音声再生中。
- `PAUSED`: 一時停止中。現在の再生位置を保持。

### 1.2 `PlaybackMode` (Data Model)
Configuration for automatic and looped playback.
- `auto_play_enabled: bool` (Auto-Play ON/OFF: デフォルトON)
- `loop_playback_enabled: bool` (Loop Playback ON/OFF: デフォルトOFF、ただしType='Loop'時はインテリジェントに自動適用可能)
- `volume: float` (0.0 〜 1.0, デフォルト0.8)
- `muted: bool` (ミュートON/OFF: デフォルトFalse)

### 1.3 `WaveformData` (Data Model)
Lightweight waveform representation optimized for rendering performance (< 400 float points).
- `file_path: str`
- `peaks_min: List[float]` (負方向ピーク配列 [-1.0, 0.0], 長さ200〜400)
- `peaks_max: List[float]` (正方向ピーク配列 [0.0, 1.0], 長さ200〜400)
- `duration_ms: int` (ミリ秒単位の総再生時間)
- `sample_rate: int`
- `channels: int`

### 1.4 `PlaybackProgress` (Data Model)
Real-time progress notification event.
- `current_position_ms: int` (現在の再生位置: ミリ秒)
- `duration_ms: int` (総再生時間: ミリ秒)
- `progress_ratio: float` (0.0 〜 1.0)
