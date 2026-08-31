# Unit 2: Functional Design Plan (Metadata Parser & Audio Signal Analyzer)

## Purpose
Unit 2（Metadata Parser & Audio Signal Analyzer）における詳細なビジネスロジック、ファイル名解析正規表現ルール、BPM/Key正規化仕様、NumPy/SciPyを用いたDSP音声信号解析アルゴリズム、および自動リネーム規則を設計するための計画書です。

---

## Planning Questions (Unit 2 機能設計に関する確認事項)

### Question 1: ファイル名解析のパターン網羅性と「Other」タグ判定優先度
ファイル名（例: `03_SS_Guitar_Snob_174_4_bar_Loop_C#_guitar_174BPM_C♯minor_BANDLAB.wav`）からのメタデータ抽出において、属性を特定できない場合の挙動について、どのアプローチを希望されますか？

A) 厳格フォールバック方式（BPM, Key, Type, 楽器, ジャンル, 制作者の各項目を個別に正規表現で抽出し、合致しない属性のみを `"Other"` または `None` とする：各属性ごとに柔軟に特定）

B) 完全一致優先方式（既知のテンプレート命名規則に完全合致した場合のみ全属性を抽出し、それ以外は一括して `"Other"` 分類とする）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2: DSP音声解析（BPM検出）の探索テンポ範囲と倍テンポ補正
Story 2.4（FR-2.5）におけるプロパティ不明音源のテンポ（BPM）自動算出において、オンセット自己相関の探索BPM範囲について、どのアプローチを想定しますか？

A) 一般的ポピュラー音楽範囲（70 〜 190 BPM を中心に探索し、極端な倍テンポ/半テンポの誤検出を抑制する：音楽制作サンプルとして最も実用的）

B) 広帯域探索範囲（40 〜 240 BPM の全域を均等に探索する）

C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

### Question 3: 自動リネーム時の命名規則と既存名との重複防止
解析されたBPMおよびKeyをファイル名に付け足す際、元のファイル名にすでにBPM表記やKey表記が含まれていた場合の整形ルールについて、どちらを希望されますか？

A) スマート置換・追記方式（元のファイル名末尾にすでに `_120BPM` 等が存在する場合は新解析値でクリーンに置換し、存在しない場合は `[元ファイル名]_[BPM]BPM_[Key].[ext]` として末尾に追記する：二重表記を防止）

B) 単純末尾追記方式（元のファイル名に関わらず、末尾に `_[BPM]BPM_[Key].[ext]` を追記する）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Execution Checklist (実行チェックリスト)

### Part 1: Planning
- [x] Step 1: Analyze Unit 2 Context & Story Mapping (`unit-of-work.md`, `unit-of-work-story-map.md`)
- [x] Step 2: Create Unit 2 Functional Design Plan (`unit-2-parser-and-analyzer-functional-design-plan.md`)
- [x] Step 3: Embed context-appropriate questions with `[Answer]:` tags
- [x] Step 5: Collect and analyze user answers
- [x] Step 5.1: Resolve any ambiguities

### Part 2: Generation (Unit 2 機能設計成果物の作成)
- [x] Step 1: Generate `aidlc-docs/construction/unit-2-parser-and-analyzer/functional-design/domain-entities.md`
- [x] Step 2: Generate `aidlc-docs/construction/unit-2-parser-and-analyzer/functional-design/business-logic-model.md`
- [x] Step 3: Generate `aidlc-docs/construction/unit-2-parser-and-analyzer/functional-design/business-rules.md`
- [x] Step 4: Final review and presentation of Unit 2 Functional Design
