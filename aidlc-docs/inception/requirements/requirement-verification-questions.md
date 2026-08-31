# Requirements Clarification Questions

音源管理ソフト（Sound Sample Manager）の要件を明確化するため、以下の質問にご回答ください。
各質問の選択肢から該当するアルファベット（A, B, C...）を `[Answer]: ` の後ろに記入してください。
該当するものがない、またはカスタムな要望がある場合は、最後の「Other」を選択し、`[Answer]:` の後ろに詳細をご記入ください。

---

## Question 1: アプリケーションの形態・UIフレームワーク
音源管理ソフトのUIおよび利用形態について、どのようなものを想定されていますか？

A) デスクトップGUIアプリ（Python + PyQt6 / PySide6：高速動作、Windowsネイティブな操作感、DAWへのドラッグ＆ドロップとの親和性が高い）

B) デスクトップGUIアプリ（Web技術ベース / Electron or Tauri / Pythonバックエンド + Webフロントエンド：モダンでスタイリッシュなUIデザイン）

C) ローカルWebアプリ（ブラウザで `localhost` にアクセスして操作：ブラウザから直接DAWへのファイルドラッグはブラウザ仕様に依存）

D) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 2: DAWとの連携およびドラッグ＆ドロップ機能
DAW（Cubase, Studio One, FL Studio, Ableton Live, Logic等）と連携するにあたり、どのような操作を重視しますか？

A) 必須：アプリ内の音源リストからDAWのトラックやタイムラインへ直接ドラッグ＆ドロップして配置できること

B) 推奨：DAWへのドラッグ＆ドロップに加え、クリップボードへのファイルパスコピーやエクスプローラー/Finderで開く機能

C) 閲覧・検索のみ：ファイルの所在特定とプレビューが主目的で、DAWへの配置はエクスプローラーから手動で行う

D) Other (please describe after [Answer]: tag below)

[Answer]: A,ついでに試聴機能とかもついていると嬉しいです。ちなみに使うソフトはCakewalk,sonorです

---

## Question 3: メタデータ抽出およびタグ付けの仕組み
現在 `Loop` および `Oneshot` に含まれるファイル名（例: `03_SS_Guitar_Snob_174_4_bar_Loop_C#_guitar_174BPM_C♯minor_BANDLAB.wav`）のように、ファイル名にBPM、キー、楽器、タイプ、制作者などが含まれています。メタデータはどのように収集・管理したいですか？

A) ファイル名パターン解析（正規表現・ルールベース）＋ WAVメタデータ（RIFFタグ/ID3）を自動解析し、アプリ内で手動編集・カスタムタグ追加も可能にする

B) ファイル名パターン解析を主とし、解析できなかった項目のみ手動で補完・タグ付けする

C) 音声解析エンジン（BPM・キー自動検出ライブラリ）も組み込み、ファイル名に情報がない音源でも自動で推定・補完する

D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 4: フォルダ構成と継続的な利用・同期方式
「継続的な利用を可能にするフォルダ構成」について、どのようなライブラリ管理方式が理想的ですか？

A) **インプレース監視（監視フォルダ方式）**：任意のフォルダ（例: `BandLabSounds/Loop`, `BandLabSounds/Oneshot` や追加フォルダ）を登録し、ファイルを移動させずにデータベース（SQLite等）にインデックス化。新しいファイルが追加されたら自動/手動で再スキャン・検知する

B) **管理型ライブラリ方式**：ソフト専用の管理フォルダ（例: `Library/Type/Genre/Instrument/...`）を用意し、インポート時に自動的に整理・リネームして配置・一元管理する

C) **ハイブリッド方式**：既存のフォルダ構造をそのままスキャンして利用できるほか、必要に応じて整理済みフォルダへコピー・エクスポートする機能も備える

D) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 5: 音声プレビュー・再生機能
音源を探す際の波形表示やプレビュー再生機能について、どこまでの機能を求めますか？

A) 高機能プレビュー：リスト選択時の自動再生、波形（Waveform）表示、ループ再生（Loop音源）、シークバー、音量調整

B) 基本プレビュー：再生/停止ボタン、音量調整、シンプルな進行バー

C) 外部プレイヤー連携：OSのデフォルトプレイヤーまたはDAW側でプレビューする

D) Other (please describe after [Answer]: tag below)

[Answer]: A,自動再生(ONOFF切り替え可能)、波形、シークバー、ループ再生(ON,OFF可能）

---

## Question 6: 対応する音声フォーマット
管理対象とする音声ファイルのフォーマットについて教えてください。

A) WAV形式メイン（現在配置されている `.wav` ファイルを中心に対応）

B) 主要オーディオ形式全般（WAV, MP3, FLAC, AIFF, OGG 等に対応）

C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 7: ソート・フィルタリング・検索機能のUI
検索や絞り込み（Type, 楽器, ジャンル, BPM範囲, キー, 制作者）の操作感について、どのようなUIが使いやすいですか？

A) タグクラウド / ファセットフィルター（タイプ、楽器、ジャンルなどのボタン/チェックボックス群）＋ BPMスライダー/範囲指定 ＋ キー選択ドロップダウン ＋ フリーワード検索バー ＋ カラムクリックによるソート

B) スプレッドシート/テーブルビュー（Excelのような各列フィルタとソート）＋ 上部クイック検索バー

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 8: Security Extensions (拡張ルール: セキュリティ)
このプロジェクトにセキュリティ拡張ルールを適用しますか？

A) Yes — すべてのセキュリティルールをブロッキング制約として適用する（本番品質・安全なファイル操作や入力検証を徹底）

B) No — セキュリティルールをスキップする（個人利用・プロトタイプ向けで迅速な開発を優先）

C) Other (please describe after [Answer]: tag below)

[Answer]: B

---

## Question 9: Resiliency Baseline (拡張ルール: 耐障害性・堅牢性)
このプロジェクトにレジリエンス（耐障害性・堅牢性）のベースラインを適用しますか？

A) Yes — 障害耐性・エラーハンドリング（壊れたWAVファイルのハンドリング、DB破損防止、例外ログ出力等）の設計ベストプラクティスを適用する

B) No — レジリエンスベースラインをスキップする（プロトタイプ向け）

C) Other (please describe after [Answer]: tag below)

[Answer]: A

---

## Question 10: Property-Based Testing Extension (拡張ルール: プロパティベーステスト)
このプロジェクトにプロパティベーステスト（PBT）ルールを適用しますか？

A) Yes — すべてのPBTルールを適用する（メタデータパーサーや検索クエリロジック等の網羅的テスト）

B) Partial — ファイル名解析やシリアライズ等の純粋関数・パーサー部分のみPBTを適用する

C) No — PBTルールをスキップし、通常のユニットテストのみとする

D) Other (please describe after [Answer]: tag below)

[Answer]: B
