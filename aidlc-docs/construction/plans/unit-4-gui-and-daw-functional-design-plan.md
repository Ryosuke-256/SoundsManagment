# Unit 4: Functional Design Plan (Desktop GUI & DAW Drag-and-Drop Integration)

## Purpose
Unit 4（Desktop GUI & DAW Drag-and-Drop Integration）における機能設計（メインウィンドウ画面構成、DAWドラッグ＆ドロップ仕様、ファセット検索UI、音声解析＆リネームダイアログ、ビジネスルール）を策定するための計画書です。

---

## Planning Questions (Unit 4 機能設計に関する確認事項)

### Question 1: メイン画面レイアウト構成（GUI Main Window Layout）
音源の検索・プレビュー・DAW配置を快適に行うための画面レイアウトについて、どちらを希望されますか？

A) 3ペイン DAWフレンドリー・ダークテーマ構成（左側: タイプ/楽器/ジャンル/キー/BPMのファセット検索サイドバー、中央: 音源リスト一覧テーブル、下部: 波形表示・再生コントロールバー：推奨）

B) 2ペイン構成（上部: 検索バー＋音源リスト、下部: 波形プレイヤー）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2: DAW（Cakewalk by BandLab / Sonar 等）へのドラッグ＆ドロップ方式
音源リスト行からDAWオーディオトラックへのドラッグ＆ドロップ連携方式について、どちらを希望されますか？

A) 標準 Windows ファイルURI (`text/uri-list` / `QUrl.fromLocalFile`) ドラッグ連携（リスト行をクリック＆ドラッグして直接 Cakewalk / Sonar / Studio One 等のトラックにドロップすると、即座にオーディオクリップとしてインポートされる方式：推奨）

B) 独自クリップボードコピー方式

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 3: プロパティ不明音源の音声解析＆一括リネームUI (Story 2.4 / FR-2.5)
プロパティ不明音源のBPM/キー自動解析およびリネームを実行するUI操作画面について、どちらを希望されますか？

A) 解析＆リネーム専用プレビューダイアログ方式（ツールバー/メニューから起動。解析対象ファイル一覧、算出されたBPM・キー、変更前後のファイル名Diffをテーブル表示し、確認後にワンクリックで一括リネーム＆DB同期を実行：推奨）

B) リスト一覧上でのインライン直接実行方式

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Execution Checklist (実行チェックリスト)

### Part 1: Planning
- [x] Step 1: Review Unit 4 Requirements & Application Design
- [x] Step 2: Create Unit 4 Functional Design Plan (`unit-4-gui-and-daw-functional-design-plan.md`)
- [x] Step 3: Embed context-appropriate questions with `[Answer]:` tags
- [x] Step 5: Collect and analyze user answers
- [x] Step 5.1: Resolve any ambiguities

### Part 2: Generation (Unit 4 機能設計成果物の作成)
- [x] Step 1: Generate `aidlc-docs/construction/unit-4-gui-and-daw/functional-design/domain-entities.md`
- [x] Step 2: Generate `aidlc-docs/construction/unit-4-gui-and-daw/functional-design/business-logic-model.md`
- [x] Step 3: Generate `aidlc-docs/construction/unit-4-gui-and-daw/functional-design/business-rules.md`
- [x] Step 4: Final review and presentation of Unit 4 Functional Design
