# Unit 2: Code Generation Plan (Metadata Parser & Audio Signal Analyzer)

## 1. Overview
Unit 2（Metadata Parser & Audio Signal Analyzer）のソースコード、ユニットテスト、プロパティテスト（PBT）、およびドキュメントを生成するための詳細実行計画書です。

### 1.1 Story Traceability (担当ユーザーストーリー)
- **Story 2.1**: ファイル名からのメタデータ抽出、BandLab命名規則の解析、および特定不能属性の「Other」フォールバック分類
- **Story 2.4 (FR-2.5)**: プロパティ不明音源の定量音声解析（NumPy/SciPyによるBPM・Key算出）および標準命名規則（`[BaseName]_[BPM]BPM_[Key].[ext]`）に沿った自動リネーム

### 1.2 Target Directory & Code Location Rules
- **Application Code**:
  - `src/parser/filename_parser.py`, `src/parser/__init__.py`
  - `src/analyzer/audio_analyzer.py`, `src/analyzer/auto_renamer.py`, `src/analyzer/batch_coordinator.py`, `src/analyzer/__init__.py`
- **Unit Tests & Property-Based Tests**:
  - `tests/test_unit2_parser.py`
  - `tests/test_unit2_analyzer.py`
  - `tests/test_unit2_pbt.py`
- **Documentation**:
  - `aidlc-docs/construction/unit-2-parser-and-analyzer/code/code-summary.md`

---

## 2. Explicit Generation Steps

- [x] **Step 1: Project Structure Setup (Parser & Analyzer Packages)**
  - `src/parser/` および `src/analyzer/` ディレクトリとそれぞれの `__init__.py` を作成。

- [x] **Step 2: Filename Parser Generation**
  - `src/parser/filename_parser.py`: `FilenameParser` クラス（正規表現パターン抽出、BandLabパック認識、Key表記統一マップ `Db`➔`C#`、個別属性フォールバック「Other」判定）を実装。

- [x] **Step 3: DSP Audio Signal Analyzer Generation**
  - `src/analyzer/audio_analyzer.py`: `AudioSignalAnalyzer` クラス（先頭15〜30秒ストリーミングロード、STFTオンセット自己相関 40〜240 BPM 探索、12音階事前計算クロマグラムフィルタバンクによるKey推定、Safe Analysis Result Null Object パターン）を実装。

- [x] **Step 4: Auto-Renamer & Batch Coordinator Generation**
  - `src/analyzer/auto_renamer.py`: `AutoRenamer` クラス（スマート置換・追記フォーマット、既存BPM/Key重複防止、プレビュー生成）を実装。
  - `src/analyzer/batch_coordinator.py`: `BatchAnalysisCoordinator` クラス（`ThreadPoolExecutor` によるマルチスレッド並行解析、進捗コールバック）を実装。

- [x] **Step 5: Unit 2 Unit Tests Generation**
  - `tests/test_unit2_parser.py`: 実ファイル名パターン（Loop, Oneshot, BandLab, 汎用音源）のメタデータパース検証。
  - `tests/test_unit2_analyzer.py`: 生成合成WAV（120BPMクリック、A440Hzトーン等）によるBPM・Key検出精度およびNull Object耐障害性テスト。

- [x] **Step 6: Unit 2 Property-Based Tests Generation (PBT-02/03)**
  - `tests/test_unit2_pbt.py`: Hypothesisを用いたパーサーの不変条件（BPM数値範囲、Key表記の標準化、TypeのLoop/Oneshot/Other収束、ランダム文字列クラッシュ耐性）のプロパティテスト。

- [x] **Step 7: Unit 2 Code Summary & Documentation Generation**
  - `aidlc-docs/construction/unit-2-parser-and-analyzer/code/code-summary.md` を作成し、Unit 2の実装成果物を要約。
