# Unit 2 NFR Requirements: Tech Stack Decisions (`tech-stack-decisions.md`)

## 1. Selected Technologies & Libraries

| 領域 | 選定技術 | バージョン | 選定理由・トレードオフ |
|---|---|---|---|
| ファイル名パーサー | Python標準 `re` モジュール | Built-in | 追加依存がなく、コンパイル済み正規表現（`re.compile`）により 1,000件 < 50ms の極めて高速な文字列マッチングを実現。 |
| DSP音声解析 (BPM & Key) | `numpy` & `scipy.signal` | `numpy>=1.24.0`, `scipy>=1.10.0` | 重量級の外部音楽情報処理ライブラリ（librosa等）に依存せず、NumPy/SciPyの高速ベクトル演算とSTFT/FFTのみで軽量・超高速にオンセット自己相関とクロマグラムを算出。 |
| 音声読み込み | Python標準 `wave` モジュール (WAV) + `scipy.io.wavfile` | Built-in / `scipy` | WAVヘッダを直接シークして先頭15秒分のサンプルのみを高速ストリーミングロード。 |
| プロパティテスト | `hypothesis` | `hypothesis>=6.80.0` | ランダムなエッジケース文字列や不正文字に対するパーサーの不変条件（PBT-02/03）を自動検証。 |

---

## 2. Technical Stack Trade-off Analysis

- **Heavy DSP Libraries (e.g. Librosa, Essentia) vs Lightweight NumPy/SciPy**:
  - *Decision*: **NumPy / SciPy** を採用。
  - *Rationale*: Librosa等は起動オーバーヘッドや大量の依存関係（numba, llvmlite, soundfile等）があり、インストーラや環境構築を複雑化させる。音楽サンプル（Loop/Oneshot）のテンポ・Key推定には、NumPy/SciPyによる直接的なSTFTオンセット自己相関とKrumhansl-Schmuckler調性プロファイル相関で十分な精度と150ms未満の高速応答が得られる。
