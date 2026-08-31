# Unit 3: Functional Design Plan (Audio Engine & Waveform Visualizer)

## Purpose
Unit 3（Audio Engine & Waveform Visualizer）におけるドメインエンティティ、再生制御ロジック、波形ピークデータ生成、およびビジネスルールの機能設計を行うための計画書です。

---

## Planning Questions (Unit 3 機能設計に関する確認事項)

### Question 1: 音声再生バックエンド（Audio Playback Engine）の設計
音源の試聴・シーク・音量制御を行うオーディオエンジンの実装方式について、どちらを希望されますか？

A) `PyQt6.QtMultimedia.QMediaPlayer` + `QAudioOutput` 方式（PyQt6標準のハードウェアアクセラレーションを活用し、再生位置通知・音量制御・状態管理をQtシグナルでUIとシームレスに同期：推奨）

B) 純粋NumPy / sounddevice 方式（低レベルオーディオストリームによるカスタムバッファ再生）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2: 波形データ（Waveform Peaks）の抽出解像度とキャッシュ方式
音源リスト選択時に波形を描画するためのピークデータ抽出方式について、どちらを希望されますか？

A) 固定200〜400ポイントのMin/Maxピーク配列抽出方式（先頭15〜30秒または全体から200〜400サンプルの正規化ピーク配列を高速生成し、メモリ上に保持：推奨）

B) フルサンプル生データ保持方式（全音声サンプルをそのままメモリに展開）

C) Other (please describe after [Answer]: tag below)

[Answer]: A,できるだけ軽量に

---

### Question 3: ループ再生（Loop Playback）と自動再生（Auto-Play）の振る舞い
音源選択時の再生挙動（Auto-Play / Loop）に関する制御ポリシーについて、どちらを希望されますか？

A) グローバルトグル連携 ＋ サンプル種別インテリジェント適用（Auto-Play ON時は選択と同時に即座にプレビュー開始。Loop ON時、または音源Typeが「Loop」の場合は末尾到達時に自動でシーク0に戻りシームレスにリピート再生：推奨）

B) 完全マニュアル再生（音源種別に関わらず再生ボタンクリック時のみ再生し、末尾到達時は常に停止）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Execution Checklist (実行チェックリスト)

### Part 1: Planning
- [x] Step 1: Analyze Unit 3 Scope & Requirements (Story 1.2: Waveform & Audio Preview)
- [x] Step 2: Create Unit 3 Functional Design Plan (`unit-3-audio-engine-functional-design-plan.md`)
- [x] Step 3: Embed context-appropriate questions with `[Answer]:` tags
- [x] Step 5: Collect and analyze user answers
- [x] Step 5.1: Resolve any ambiguities

### Part 2: Generation (Unit 3 機能設計成果物の作成)
- [x] Step 1: Generate `aidlc-docs/construction/unit-3-audio-engine/functional-design/domain-entities.md`
- [x] Step 2: Generate `aidlc-docs/construction/unit-3-audio-engine/functional-design/business-logic-model.md`
- [x] Step 3: Generate `aidlc-docs/construction/unit-3-audio-engine/functional-design/business-rules.md`
- [x] Step 4: Final review and presentation of Unit 3 Functional Design
