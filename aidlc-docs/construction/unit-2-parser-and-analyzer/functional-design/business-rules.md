# Unit 2 Functional Design: Business Rules & PBT Specification (`business-rules.md`)

## 1. Business Rules

### BR-201: Granular Attribute Fallback Rule (属性個別フォールバックルール)
- **Rule**: ファイル名解析（`FilenameParser`）は、BPM, Key, Type, Instrument, Genre, Creator の各属性を独立して評価する。
- **Validation**:
  - 特定できなかった属性のみに `"Other"` または `None` を設定し、一部が不明であっても特定できた他の属性（例: TypeとBPMは判明したが楽器が不明）は正確に保持する。

### BR-202: Key Representation Standardization Rule (Key表記統一ルール)
- **Rule**: すべてのKey主音はシャープ記号（`#`）を標準とし、フラット表記（`Db`, `Eb`, `Gb`, `Ab`, `Bb`）やUnicode記号（`♯`, `♭`）は標準表記（`C#`, `D#`, `F#`, `G#`, `A#`）に自動正規化される。
- **Validation**: 検索およびリネーム時にKeyの表記揺れによる検索漏れやファイル名不整合が発生しないこと。

### BR-203: Wide-Range DSP BPM Estimation Rule (広帯域BPM検出ルール)
- **Rule**: 不明音源のDSP音声解析は 40 〜 240 BPM の広帯域テンポを均等に探索し、オンセット自己相関ピークから最も支配的なテンポを算出する。
- **Validation**: アンビエント（40〜60 BPM）からドラムンベース・ハードコア（170〜220 BPM）まで幅広いジャンルの音源をカバーできること。

### BR-204: Smart Auto-Rename & Anti-Duplication Rule (スマートリネーム重複防止ルール)
- **Rule**: 自動リネーム時は、既存のファイル名にすでに含まれるBPM・Key表記（例: `_174BPM`, `_C#minor`）を自動検知して除去・更新し、`Sample_174BPM_174BPM.wav` のような二重表記を防止する。
- **Validation**: 生成されたファイル名が標準規則 `[BaseName]_[BPM]BPM_[Key].[ext]` に正確に合致すること。

---

## 2. Property-Based Testing (PBT) Specification (PBT-02, PBT-03, PBT-07)

Hypothesisフレームワークを用いたパーサーおよび正規化関数の不変条件プロパティテスト仕様：

### PBT-02: Round-Trip & Preservation Property
- **Property**: 任意の生成された標準音源ファイル名 `[Genre]_[BPM]BPM_[Key]_[Instrument]_[Type]_[Creator].wav` をパーサーに入力した際、抽出される各属性値が入力と完全に一致すること。

### PBT-03: Invariant Normalization Properties
- **Invariant 1 (BPM Bounds)**: 抽出されたBPMは `None` であるか、または `10.0 <= bpm <= 999.0` の正の数値であること。
- **Invariant 2 (Key Formats)**: 抽出されたKey主音は `None` または `{"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"}` のいずれかであること。
- **Invariant 3 (Type Convergence)**: 抽出された `sample_type` は必ず `"Loop"`, `"Oneshot"`, `"Other"` の3つのいずれかに厳格に収束すること。
- **Invariant 4 (Non-Crashing Robustness)**: ランダムなASCII/Unicode文字列、空文字列、記号のみのファイル名を与えても、パーサーが例外でクラッシュせず、安全にフォールバック値を返すこと。
