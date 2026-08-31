# Unit 2 Functional Design: Business Logic Model (`business-logic-model.md`)

## 1. Filename Parsing & Normalization Logic

### 1.1 BandLab Sounds & General Sound Pack Parsing Logic
`FilenameParser` は、以下のアルゴリズムでファイル名文字列から各属性を段階的に抽出します：

1. **トークン分割**:
   - アンダースコア（`_`）やハイフン（`-`）、空白でトークンを分解。
2. **Type（音源タイプ）判定**:
   - 正規表現 `(?i)\b(loop|loops)\b` ➔ `"Loop"`
   - 正規表現 `(?i)\b(oneshot|one-shot|shot|shots|hit|hits)\b` ➔ `"Oneshot"`
   - 特定できない場合は親ディレクトリ名（`Loop/` or `Oneshot/`）を補助参照、それ以外は `"Other"`。
3. **BPM（テンポ）抽出**:
   - 明示的表記: `(\d{2,3}(?:\.\d+)?)\s*(?:bpm|BPM)`
   - 独立数値トークン: `(?:^|_|-)(\d{2,3})(?:_|-|$)`（50 〜 250 の範囲）
4. **Key（調性・主音・スケール）抽出 & 正規化**:
   - パターン: `([A-Ga-g][#b♯♭]?)\s*(minor|major|min|maj|m)?\b`
   - 異名同音（フラット ➔ シャープ）変換マップ:
     `Db` ➔ `C#`, `Eb` ➔ `D#`, `Gb` ➔ `F#`, `Ab` ➔ `G#`, `Bb` ➔ `A#`
   - Unicode記号正規化: `♯` ➔ `#`, `♭` ➔ `b`
   - スケール正規化: `m`, `min`, `minor` ➔ `"minor"`, `maj`, `major` ➔ `"major"`
5. **Instrument（楽器）抽出**:
   - 辞書マッチング: `guitar`, `bass`, `808`, `808s`, `synth`, `pad`, `lead`, `pluck`, `keys`, `piano`, `rhodes`, `kick`, `snare`, `clap`, `hihat`, `hat`, `cymbal`, `drums`, `percussion`, `perc`, `vocal`, `vox`, `fx`, `sfx`, `flute`, `brass`, `strings` 等。
6. **Creator & Genre / Pack名抽出**:
   - 末尾の既知ベンダータグ（`BANDLAB`, `HEAVEE`, `SOUNDS` 等）を Creator として抽出。
   - 先頭・中間のパック識別文字列（例: `SS_Guitar_Snob`, `DW_DistArp`）を Genre / Pack として抽出。

---

## 2. DSP Audio Signal Analysis Algorithm (BPM & Key Detection)

プロパティ不明音源（「Other」分類等）に対し、軽量な NumPy / SciPy 音声信号処理で BPM と Key を定量算出します（Q2: B 広帯域 40〜240 BPM 探索）。

```
[音声ファイル読み込み (WAV/MP3/etc.)]
               │
               ▼
[モノラル変換 & 22050Hz リサンプリング]
               │
       ┌───────┴──────────────────┐
       ▼                          ▼
[BPM算出 (Onset Autocorrelation)] [Key推定 (STFT Chromagram)]
 1. 短時間フーリエ変換 (STFT)      1. STFTスペクトログラム計算
 2. スペクトルフラックス (Onset)    2. 12半音ピッチクラスへ射影
 3. 自己相関関数 (Autocorrelation) 3. 平均クロマベクトル集計
 4. 40〜240 BPM範囲の最大ピーク   4. Krumhansl-Schmuckler
    ➔ 検出BPM & 信頼度スコア         調性プロファイル相関
                                     ➔ 検出Key & スケール
       └───────┬──────────────────┘
               │
               ▼
[AudioAnalysisResult 生成 & 新ファイル名候補フォーマット]
```

### 2.1 BPM Detection Algorithm (Onset Envelope Autocorrelation)
1. 音声信号からフレーム長 1024、ホップ長 512 でスペクトログラムを計算。
2. フレーム間のエネルギー正の変化（Spectral Flux）を抽出し、オンセット強度エンベロープ（Onset Envelope）を生成。
3. オンセットエンベロープの自己相関（Autocorrelation）を計算。
4. 40 BPM（lag = `sr * 60 / (hop * 40)`）〜 240 BPM（lag = `sr * 60 / (hop * 240)`）の探索ラグ範囲で最大ピークを特定。
5. ピークの鋭さ（Peak-to-Average Ratio）から `bpm_confidence`（0.0〜1.0）を算出。

### 2.2 Key Detection Algorithm (Chromagram & Harmonic Profiles)
1. FFTの各周波数ビンを 12音階（A, A#, B, C, C#, D, D#, E, F, F#, G, G#）のピッチクラスに射影し、時間平均クロマベクトル（12次元）を算出。
2. Krumhansl-Schmucklerの調性テンプレート（12個のMajorプロファイルおよび12個のMinorプロファイル、計24プロファイル）とのピアソン相関係数を計算。
3. 最も相関係数が高い調性（例: `C# minor`）を検出Keyとし、最大相関係数を `key_confidence` として記録。

---

## 3. Smart Auto-Renaming Logic

ユーザー回答（Q3: A スマート置換・追記方式）に基づくファイル名整形アルゴリズム：

1. **既存BPM・Key表記の検出・除去**:
   - ベースファイル名から既存の `_\d{2,3}BPM` や `_[A-G][#b]?(?:minor|major)?` を正規表現で安全にストリップ。
2. **標準フォーマット合成**:
   - BPMとKeyの両方が検出された場合:
     ➔ `f"{clean_basename}_{int(round(bpm))}BPM_{key_root}{key_scale}.{ext}"`
     例: `Kick_Sample.wav` (BPM=120, Key=C) ➔ `Kick_Sample_120BPM_Cmajor.wav`
   - BPMのみ検出された場合:
     ➔ `f"{clean_basename}_{int(round(bpm))}BPM.{ext}"`
   - Keyのみ検出された場合:
     ➔ `f"{clean_basename}_{key_root}{key_scale}.{ext}"`
3. **二重表記の完全防止**:
   - すでに同じBPMやKeyが付与されているファイル名に対して同一の文字列を重複して追加しない。
