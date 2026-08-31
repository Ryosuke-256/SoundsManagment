# Unit 4 NFR Requirements: Desktop GUI & DAW Integration

## 1. Performance & UI Responsiveness Requirements

### 1.1 Table Virtualization & Scrolling Performance
- **Requirement**: ライブラリ内に 1,000 件〜10,000 件の音源が登録されている場合でも、テーブルの初回描画時間は **100ms 未満**、スクロール時の描画は **60 FPS**（16.6ms/フレーム）を維持する。
- **Verification**: `QAbstractTableModel` のデータフェッチ速度とスクロール時のCPU負荷測定。

### 1.2 Non-Blocking Background Execution
- **Requirement**: フォルダの一括インポート、ライブラリスキャン、およびプロパティ不明音源のバッチ音声解析実行中、UIメインスレッドのフレームドロップをゼロに抑え、プログレスバーによる進捗率（`X / Total`）およびキャンセル操作を提供する。
- **Verification**: `QThread` ワーカー実行中のUIインタラクション応答性検証。

---

## 2. Display & DAW Integration Requirements

### 2.1 DAW-Style Dark Palette & High-DPI Scaling
- **Requirement**:
  - Cakewalk by BandLab / Sonar 等のプロオーディオDAWと親和性の高いダークテーマパレット（背景 `#1e1e24`, `#2d3748`, アクセント `#00d2ff`）を適用。
  - Windows 11 の High-DPI ディスプレイ（125%, 150%, 200% スケーリング環境）で文字やアイコンのぼやけ・UI崩れが生じないこと。

### 2.2 Drag-and-Drop Reliability (RESILIENCY-10)
- **Requirement**:
  - ドラッグ開始時にファイルの実存在を確認し、存在しない場合はドラッグを安全にキャンセルして警告を表示。
  - Cakewalk / Sonar がファイルを掴むまでの間にアプリケーションがクラッシュしないこと。
