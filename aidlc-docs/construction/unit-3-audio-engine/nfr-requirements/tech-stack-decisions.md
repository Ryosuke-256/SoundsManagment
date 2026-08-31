# Unit 3 NFR Requirements: Tech Stack Decisions (`tech-stack-decisions.md`)

## 1. Technology Selections for Unit 3

### 1.1 Audio Playback Engine: `PyQt6.QtMultimedia`
- **Component**: `QMediaPlayer`, `QAudioOutput`, `QUrl`
- **Rationale**:
  - Windows 11 の WASAPI / DirectSound ハードウェアオーディオパイプラインを自動活用し、超低レイテンシで安定した再生を実現。
  - Qt標準シグナル・スロットモデル（`positionChanged`, `durationChanged`, `playbackStateChanged`, `errorOccurred`）によるUI完全同期。
  - 外部Cライブラリや重厚なオーディオフレームワークの追加インストールが不要。

### 1.2 Waveform Peak Extractor: `wave` + `numpy`
- **Component**: Python組み込み `wave`, `numpy` (ベクトル化Min/Maxリダクション)
- **Rationale**:
  - 先頭15〜30秒のPCMサンプルを高速バイナリリードし、NumPyの等分割スライス（`np.array_split` / `reshape`）と `np.min()` / `np.max()` により数ミリ秒で200〜400点のピーク配列を生成。
  - メモリ消費量を数十KB未満に抑制。

### 1.3 Custom Waveform Widget: `PyQt6.QtWidgets.QWidget` + `QPainter`
- **Component**: `QWidget`, `QPainter`, `QPainterPath`, `QColor`, `QPen`, `QBrush`, `QMouseEvent`
- **Rationale**:
  - カスタムペイントによるDAW品質（Cakewalk / Ableton風）のダークテーマ波形描画。
  - クリック・ドラッグによる即時シーク、および再生進行状況のグラデーションオーバーレイ表示。

### 1.4 Test Framework: `pytest`, `unittest`, `hypothesis`
- **Rationale**:
  - 再生状態マシン、シーク位置クランプ、波形正規化不変条件を網羅的に自動検証。
