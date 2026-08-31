# Application Design Plan

## Purpose
音源管理ソフト（Sound Sample Manager）のハイレベルなコンポーネント構成、サービス層の責務、インターフェース、依存関係、およびデータフローを設計するための計画書です。

---

## Planning Questions (設計方針に関する確認事項)

### Question 1: アーキテクチャパターンとUI・ロジックの分離方式
PyQt6デスクトップアプリケーション全体の設計パターンについて、どのアプローチを希望されますか？

A) レイヤード・アーキテクチャ（UI層 / サービス層 / リポジトリ層 / コアユーティリティ層を疎結合に分離し、Qtシグナル・スロットまたはイベントバスで非同期連携する構成：保守性とテスト容易性が高い）

B) MVC / MVPパターン（Model: DB/ファイル, View: PyQtウィジェット, Controller/Presenter: イベント処理を直結する構成：シンプルで小規模〜中規模向け）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

### Question 2: 音声解析（BPM・Key算出）エンジンの実装方針 (DSP Engine Strategy)
Story 2.4で追加された「プロパティ不明音源の定量音声解析（BPM/Key検出）」の内部処理方式について、どのアプローチを想定しますか？

A) 軽量・純Python/NumPy/SciPyベースの自己完結型アルゴリズム（外部ヘビーライブラリに過度に依存せず、FFT/クロマ特徴量計算によるピッチ・調性推定およびオンセット自己相関によるBPM検出を実装：ポータブルで起動・依存関係がシンプル）

B) 音声処理特化ライブラリの活用（`librosa` または `aubio` を依存関係に組み込み、高度なテンポトラッキングと調性解析を行う：高精度だがパッケージサイズ・依存関係が増加）

C) ハイブリッド型（基本は軽量NumPy/SciPyアルゴリズムで高速に処理し、将来的に外部DSPライブラリもプラグイン可能にする構造）

D) Other (please describe after [Answer]: tag below)

[Answer]: C, 一旦は軽量型で実装してください

---

### Question 3: オーディオ再生と波形抽出の非同期スレッド設計
音源のプレビュー再生、波形ピークデータ生成、および大量音源のインポート/スキャン時のスレッド処理について、どの方式を希望されますか？

A) Qtスレッドプール / QThreadワーカー方式（UIスレッドを完全にブロックせず、波形生成・DBスキャン・音声解析をバックグラウンドワーカーで実行し、QtシグナルでUIへ通知する高レスポンス設計）

B) シンプルシングルスレッド＋タイマー/プログレスダイアログ方式（実装を極力シンプルにし、重い処理時のみプログレスバーで待機）

C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Execution Checklist (実行チェックリスト)

### Part 1: Planning
- [x] Step 1: Analyze context (`requirements.md`, `stories.md`)
- [x] Step 2: Create application design plan (`application-design-plan.md`)
- [x] Step 3: Embed context-appropriate questions with `[Answer]:` tags
- [x] Step 7: Collect and analyze user answers
- [x] Step 10: Obtain user approval for Application Design Plan

### Part 2: Generation (設計成果物の作成)
- [x] Step 1: Generate `aidlc-docs/inception/application-design/components.md` (コンポーネント定義書)
- [x] Step 2: Generate `aidlc-docs/inception/application-design/component-methods.md` (コンポーネントメソッド・インターフェース仕様書)
- [x] Step 3: Generate `aidlc-docs/inception/application-design/services.md` (サービス層オーケストレーション定義書)
- [x] Step 4: Generate `aidlc-docs/inception/application-design/component-dependency.md` (依存関係・通信パターン・データフロー図)
- [x] Step 5: Generate `aidlc-docs/inception/application-design/application-design.md` (統合設計書)
- [x] Step 6: Final review and user approval of Application Design
