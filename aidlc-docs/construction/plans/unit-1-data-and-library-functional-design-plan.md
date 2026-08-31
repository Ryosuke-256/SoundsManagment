# Unit 1: Functional Design Plan (Data Model, Database & Library Manager)

## Purpose
Unit 1（Data Model, Database & Library Manager）の詳細なビジネスロジック、データモデル、バリデーションルール、および整合性・バックアップ仕様を設計するための計画書です。

---

## Planning Questions (Unit 1 機能設計に関する確認事項)

### Question 1: インポート時の重複ファイル（同名ファイル）の処理方針
ライブラリ管理フォルダへのインポート時、すでに同名または同一内容のファイルが存在する場合の挙動について、どのアプローチを希望されますか？

A) スキップ（すでにライブラリ内に存在する場合はインポートをスキップし、既存のメタデータを保持する：最も安全で重複を防止）

B) 上書き更新（既存ファイルを新ファイルで上書きし、DBのメタデータも最新情報に更新する）

C) 連番リネーム追加（例: `Kick_01_1.wav` のように連番を付与して別ファイルとして両方保持する）

D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Question 2: インポート時の元ファイル操作（コピー vs 移動）
外部フォルダ（例: ダウンロードフォルダや現在の `Loop/`, `Oneshot/` フォルダ）から管理ライブラリ（`SoundLibrary/Library/`）へ音源を取り込む際のファイル操作について、どちらをデフォルトとしますか？

A) コピー方式（元ファイルを残したまま、管理ライブラリフォルダへ複製配置する：元データが保護され安全）

B) 移動方式（元ファイルを管理ライブラリフォルダへ移動する：ディスク容量を節約）

C) 選択可能方式（基本はコピーをデフォルトとし、設定で移動を選択可能にする）

D) Other (please describe after [Answer]: tag below)

[Answer]: C

---

### Question 3: データベースバックアップの実行タイミング
SQLiteデータベース（`SoundLibrary/Database/library.db`）の自動バックアップ世代管理（直近5世代保持）について、どのタイミングでの実行を希望されますか？

A) アプリ起動時および正常終了時に自動スナップショット作成（安定した状態のDBを自動保存）

B) インポートやバッチ処理などの大きな変更完了時に自動スナップショット作成

C) 起動時・終了時・大量インポート完了時の両方で自動スナップショット作成

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Execution Checklist (実行チェックリスト)

### Part 1: Planning
- [x] Step 1: Analyze Unit 1 Context (`unit-of-work.md`, `unit-of-work-story-map.md`)
- [x] Step 2: Create Unit 1 Functional Design Plan (`unit-1-data-and-library-functional-design-plan.md`)
- [x] Step 3: Embed context-appropriate questions with `[Answer]:` tags
- [x] Step 5: Collect and analyze user answers
- [x] Step 5.1: Resolve any ambiguities

### Part 2: Generation (Unit 1 機能設計成果物の作成)
- [x] Step 1: Generate `aidlc-docs/construction/unit-1-data-and-library/functional-design/domain-entities.md`
- [x] Step 2: Generate `aidlc-docs/construction/unit-1-data-and-library/functional-design/business-logic-model.md`
- [x] Step 3: Generate `aidlc-docs/construction/unit-1-data-and-library/functional-design/business-rules.md`
- [x] Step 4: Final review and presentation of Unit 1 Functional Design
