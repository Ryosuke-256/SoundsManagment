# Unit 3: Code Generation Plan (Audio Engine & Waveform Visualizer)

## 1. Overview
Unit 3（Audio Engine & Waveform Visualizer）のソースコード、ウィジェット、ユニットテスト、プロパティテスト（PBT）、およびドキュメントを生成するための詳細実行計画書です。

### 1.1 Story Traceability (担当ユーザーストーリー)
- **Story 1.2**: 音源リスト選択時の波形表示、自動再生（Auto-Play ON/OFF）、ループ試聴（Loop Playback ON/OFF）、シークバー操作、音量・ミュート調整

### 1.2 Target Directory & Code Location Rules
- **Application Code**:
  - `src/audio/waveform_extractor.py` (`WaveformData`, `WaveformExtractor`)
  - `src/audio/waveform_cache.py` (`WaveformCache`)
  - `src/audio/player_service.py` (`AudioPlayerService`, `PlaybackState`, `PlaybackMode`)
  - `src/audio/__init__.py`
  - `src/ui/waveform_widget.py` (`WaveformWidget`)
  - `src/ui/__init__.py`
- **Unit Tests & Property-Based Tests**:
  - `tests/test_unit3_audio.py`
  - `tests/test_unit3_waveform.py`
  - `tests/test_unit3_pbt.py`
- **Documentation**:
  - `aidlc-docs/construction/unit-3-audio-engine/code/code-summary.md`

---

## 2. Explicit Generation Steps

- [x] **Step 1: Project Structure Setup (Audio & UI Packages)**
  - `src/audio/` および `src/ui/` ディレクトリとそれぞれの `__init__.py` を作成。

- [x] **Step 2: Waveform Extractor & LRU Cache Generation**
  - `src/audio/waveform_extractor.py`: `WaveformExtractor` クラス（NumPy高速Min/Max間引き、正規化、破損ファイルSafe Null Waveformフォールバック）を実装。
  - `src/audio/waveform_cache.py`: `WaveformCache` クラス（`OrderedDict` による容量100件のLRUキャッシュ）を実装。

- [x] **Step 3: Audio Player Service Generation**
  - `src/audio/player_service.py`: `AudioPlayerService` クラス（`QMediaPlayer` / `QAudioOutput` ラッパー、Auto-Play / Loopインテリジェント制御、音量・ミュート・シーク制御、Qtカスタムシグナル、ヘッドレス・テストモード対応）を実装。

- [x] **Step 4: Waveform Interactive Visualizer Widget Generation**
  - `src/ui/waveform_widget.py`: `WaveformWidget` クラス（PyQt6 `QPainter` によるアンチエイリアス波形バー描画、再生ヘッドと進行グラデーションオーバーレイ、クリック・ドラッグによる即時シーク、状態連動描画タイマー）を実装。

- [x] **Step 5: Unit 3 Unit Tests Generation**
  - `tests/test_unit3_audio.py`: `AudioPlayerService` の状態遷移（STOPPED/PLAYING/PAUSED）、音量/ミュート制御、ループ再生ロジック、シーク位置クランプ検証。
  - `tests/test_unit3_waveform.py`: `WaveformExtractor` のピーク抽出、正規化精度、キャッシュヒット、破損ファイル耐障害性テスト。

- [x] **Step 6: Unit 3 Property-Based Tests Generation (PBT-04)**
  - `tests/test_unit3_pbt.py`: Hypothesisを用いた波形ピーク正規化範囲（$[-1.0, 1.0]$）、指定ビン数 $N$ 一致不変条件、シーク境界クランプのプロパティテスト。

- [x] **Step 7: Unit 3 Code Summary & Documentation Generation**
  - `aidlc-docs/construction/unit-3-audio-engine/code/code-summary.md` を作成し、Unit 3の実装成果物を要約。
