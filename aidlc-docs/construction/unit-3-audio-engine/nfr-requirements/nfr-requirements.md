# Unit 3 NFR Requirements: Audio Engine & Waveform Visualizer

## 1. Performance Requirements

### 1.1 Playback Startup Latency
- **Requirement**: 音源リストでの行選択（Auto-Play ON時）または再生ボタンクリックから、オーディオバッファが再生開始されるまでのレイテンシは **50ms 未満** を維持する。
- **Verification**: `QMediaPlayer.setSource()` から `QMediaPlayer.playbackStateChanged(PlayingState)` までの応答時間測定。

### 1.2 Waveform Peak Extraction Speed
- **Requirement**: 1ファイルあたりの波形ピーク（200〜400点）抽出処理時間は **20ms 未満**、キャッシュヒット時は **0ms**。
- **Verification**: ベンチマークテストによる時間測定。

### 1.3 GUI Rendering & CPU Footprint
- **Requirement**:
  - 再生中：30〜60 FPS で再生ヘッドおよびシーク位置を滑らかに更新。
  - 非再生中（停止／一時停止）：描画更新タイマーを完全停止し、波形ウィジェットのCPU使用率を **0.0%** に抑制。

---

## 2. Resiliency & Fault Tolerance (RESILIENCY-10)

### 2.1 Audio Device Error Handling
- **Requirement**:
  - オーディオ出力デバイスが未検出、または再生中にヘッドフォン／インターフェースが抜線された場合でも、アプリケーションがクラッシュ（Abnormal Termination）しない。
  - `QMediaPlayer.errorOccurred` シグナルを捕捉し、安全に内部状態を `STOPPED` にリセットし、UIの再生ボタンを安全状態に戻す。

### 2.2 Corrupted Audio File Guard
- **Requirement**:
  - 0バイトファイルや破損WAVファイルが再生要求された場合、例外をトラップして空の `WaveformData`（中央線のみ）を描画し、再生エラー通知シグナルを発行して停止状態を維持する。

---

## 3. Property-Based Testing Specifications (PBT-04)
- **Hypothesis Invariant**:
  - 任意の時間 $T \ge 0$、任意サンプルレート、任意チャンネル数の合成音声データに対して、生成されるピーク配列の長さが常に指定ビン数 $N$（例: 300）と一致し、値が $[-1.0, 1.0]$ の範囲内に収まること。
