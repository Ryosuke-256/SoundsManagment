# Unit 4 Functional Design: Business Logic Model (`business-logic-model.md`)

## 1. Application Layout & Window Architecture

```
+-----------------------------------------------------------------------------------------------+
| [MainWindow] BandLab Sound Manager                                                            |
|  [Menu Bar: File | Edit | Tools (Audio Analyzer & Auto-Rename) | View | Help]                 |
|  [Toolbar: Import Folder | Auto-Play Toggle | Loop Toggle | Volume Slider | Rescan Library]   |
+-----------------------------------+-----------------------------------------------------------+
| [Left Sidebar: Facet Search Tree] | [Center: Sample Table View (Sortable)]                   |
| - Search: [____________]          |  Title | Type | Inst | Genre | BPM | Key | Creator | Dur   |
| - Type (Loop, Oneshot, Other)     |  -------------------------------------------------------  |
| - Instrument (Guitar, Bass, ...)  |  > Lead_120BPM_C.wav | Loop | Synth | Trap | 120 | C | ...    |
| - Genre (Trap, Lofi, EDM, ...)    |  > Kick_Punch.wav    | Oneshot | Drum | Pop | - | - | ...     |
| - Key (C, D, E, F, G, A, B, ...)  |  > Atmospheric_01    | Loop | Other | Lofi | 90 | Am | ...    |
| - BPM Range Slider [40 --- 240]   |                                                           |
|                                   |  (Direct Drag-and-Drop to Cakewalk/Sonar Audio Tracks)    |
+-----------------------------------+-----------------------------------------------------------+
| [Bottom: Audio Preview & Waveform Player Panel]                                               |
|  [Play/Pause] [Stop] [00:12 / 00:30]  [====== Waveform Visualizer (Click/Drag Seek) ======]  |
|  [Auto-Play: ON] [Loop: ON] [Vol: 80%] [Delete / Remove Action]                               |
+-----------------------------------------------------------------------------------------------+
```

---

## 2. Component Logic & Interaction Flow

### 2.1 Sample Selection & Auto-Play Flow
1. ユーザーが中央の `SampleTableView` で音源行をクリックまたは矢印キーで選択。
2. `SampleTableView` の `selectionChanged` シグナルが発火し、選択行の `file_path` および `sample_type` を取得。
3. `WaveformExtractor`（または `WaveformCache`）から波形ピークを取得し、下部の `WaveformWidget` にセット。
4. `AudioPlayerService.play_sample(file_path, is_loop=(sample_type == 'Loop'))` を呼び出し。
5. Auto-Play が ON の場合は即座に再生開始。OFF の場合は停止状態で待機。

### 2.2 Direct DAW Drag-and-Drop Flow
1. ユーザーがテーブル行でマウス左ボタンを押下したままドラッグ開始。
2. `SampleTableView` の `mouseMoveEvent` が移動閾値（`QApplication.startDragDistance()`）を検知。
3. `QDrag` オブジェクトを生成し、`QMimeData.setUrls([QUrl.fromLocalFile(file_path)])` を設定。
4. `drag.exec(Qt.DropAction.CopyAction)` を呼び出し、Windows OLE ドラッグセッションを開始。
5. Cakewalk by BandLab / Sonar のオーディオトラックにドロップされると、DAW 側がファイルパスを直接認識してクリップを配置。

### 2.3 Audio Analysis & Auto-Rename Dialog Flow (Story 2.4 / FR-2.5)
1. ツールバーまたはメニューの「Audio Analyzer & Auto-Rename」をクリック。
2. 未分類音源または選択中音源をリストアップした `AudioAnalyzerDialog` が起動。
3. 「Start Analysis」を押下すると、Unit 2 の `BatchAnalysisCoordinator` がバックグラウンドスレッドで各音源の BPM・キーを解析。
4. 解析結果に基づき、新ファイル名候補（`[BaseName]_[BPM]BPM_[Key].[ext]`）を Diff プレビュー表示。
5. ユーザーが対象を選択し「Apply Rename & Update DB」を押下。
6. `AutoRenamer` が物理ファイルをリネームし、`SampleRepository` が DB レコードを更新。テーブルおよび波形が自動リフレッシュ。
