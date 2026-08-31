# Unit 3: NFR Design Plan (Audio Engine & Waveform Visualizer)

## Purpose
Unit 3（Audio Engine & Waveform Visualizer）における非機能設計パターン（オーディオプレイヤーサービスラッパー、波形LRUメモリキャッシュ、ヘッドレス・テストモード分離、論理コンポーネント構成）を設計するための計画書です。

---

## Planning Questions (Unit 3 非機能設計に関する確認事項)

### Question 1: プレイヤードメインイベント通知とシグナル統合パターン
UIウィジェットや他のサービスからオーディオエンジンを制御・購読する設計パターンについて、どちらを希望されますか？

A) `AudioPlayerService` ラッパー ＋ Qtカスタムシグナルパターン（`QMediaPlayer` の低レベル詳細を隠蔽し、再生進捗 `position_changed(ms)`、再生状態 `state_changed(PlaybackState)`、エラー `error_occurred(str)` を発行：推奨）

B) `QMediaPlayer` 直接参照方式（UIからQt低レベルオブジェクトを直接操作）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2: 波形ピークデータのメモリ管理・キャッシュパターン
頻繁にリストを選択して波形を描画する際のメモリ消費とキャッシュ管理パターンについて、どちらを希望されますか？

A) `WaveformCache` LRUインメモリキャッシュパターン（直近100ファイルのピークデータをメモリ保持し、容量超過時は最古のデータを自動破棄してメモリリークを防止：推奨）

B) キャッシュなし（選択ごとに毎回ファイルを直接読み込んでピーク計算）

C) Other (please describe after [Answer]: tag below)

[Answer]: A,できるだけ軽量に

---

### Question 3: CI/テスト環境におけるヘッドレス（無音響デバイス）動作パターン
CIサーバーやヘッドレス環境（音声デバイスが存在しない環境）での単体テスト実行方針について、どちらを希望されますか？

A) ヘッドレス耐障害性 Null Audio モード（音声デバイスが利用不可能な環境でもテストがクラッシュせず、波形生成・状態遷移・シーク計算のテストが100%成功する設計：推奨）

B) 実デバイス依存方式（音声デバイスがない環境ではテストをスキップ）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Execution Checklist (実行チェックリスト)

### Part 1: Planning
- [x] Step 1: Review Unit 3 NFR Requirements
- [x] Step 2: Create Unit 3 NFR Design Plan (`unit-3-audio-engine-nfr-design-plan.md`)
- [x] Step 3: Embed context-appropriate questions with `[Answer]:` tags
- [x] Step 5: Collect and analyze user answers
- [x] Step 5.1: Resolve any ambiguities

### Part 2: Generation (Unit 3 NFR設計成果物の作成)
- [x] Step 1: Generate `aidlc-docs/construction/unit-3-audio-engine/nfr-design/nfr-design-patterns.md`
- [x] Step 2: Generate `aidlc-docs/construction/unit-3-audio-engine/nfr-design/logical-components.md`
- [x] Step 3: Final review and presentation of Unit 3 NFR Design
