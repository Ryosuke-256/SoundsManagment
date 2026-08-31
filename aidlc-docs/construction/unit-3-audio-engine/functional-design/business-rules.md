# Unit 3 Functional Design: Business Rules (`business-rules.md`)

## 1. Business Rules for Audio Engine & Waveform Visualizer

### BR-301: Audio Playback & Volume Control
- 音量は 0.0（無音）〜 1.0（最大）の範囲でリニアに制御可能。
- ミュート切替時は現在の音量値を保持したまま音量を0にし、ミュート解除時に元の音量値に復帰する。
- 再生中（`PLAYING`）に新しい音源が選択された場合、直前の音源再生は直ちに停止（`stop()`）され、新音源に切り替わる。

### BR-302: Auto-Play Triggering Policy
- `auto_play_enabled == True` の場合、ユーザーがリストで音源を選択した瞬間（選択変更イベント）に直ちに再生を開始する。
- `auto_play_enabled == False` の場合、音源選択時は波形およびメタデータのロードのみを行い、再生はユーザーが再生ボタンをクリックするまで待機（`STOPPED`）する。

### BR-303: Loop Playback Policy
- 音源の末尾（End-of-Media）到達時：
  - `loop_playback_enabled == True` または音源メタデータの `sample_type == 'Loop'` の場合：
    - 自動で再生位置を先頭（0ms）に巻き戻し、継続再生する（シームレスループ）。
  - `loop_playback_enabled == False` かつ `sample_type != 'Loop'` の場合：
    - 再生を停止し、再生位置を0msにリセットして `STOPPED` 状態へ遷移する。

### BR-304: Interactive Waveform Seek & Click-to-Play
- ユーザーが波形ウィジェット上の任意の位置をクリックまたはドラッグした場合、その水平座標の比率 $R \in [0.0, 1.0]$ に応じたミリ秒位置 $P = R \times \text{duration\_ms}$ へ即座にシークする。
- 停止中（`STOPPED`）に波形をクリックした場合、その位置から自動的に再生を開始する。

---

## 2. Invariant Specifications for Testing (PBT-04)
- **Invariant 1 (Volume Bound)**: $0.0 \le \text{volume} \le 1.0$ は常に保たれる。
- **Invariant 2 (Seek Position Range)**: 任意のシーク要求 $P$ に対し、実際の再生位置は $0 \le P \le \text{duration\_ms}$ にクランプされる。
- **Invariant 3 (Waveform Normalization Bound)**: 抽出された波形ピーク配列の各値は $-1.0 \le \text{peak\_min}_i \le 0.0$ および $0.0 \le \text{peak\_max}_i \le 1.0$ に厳密に収まる。
