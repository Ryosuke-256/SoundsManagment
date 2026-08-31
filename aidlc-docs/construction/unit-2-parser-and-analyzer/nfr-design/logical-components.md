# Unit 2 NFR Design: Logical Components (`logical-components.md`)

## 1. Logical Component Architecture

Unit 2 におけるメタデータ解析およびDSP音声信号処理の論理コンポーネント構成：

```
+-------------------------------------------------------------------------+
| [Unit 2: Metadata Parser & Audio Signal Analyzer]                       |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | Filename Parsing & Normalization                                  |  |
|  |  - Tokenizer & RegexMatcher (Compiled regex, BandLab / General)  |  |
|  |  - KeyNormalizer (Flat-to-Sharp, Scale standardizer)              |  |
|  |  - FallbackResolver (Granular 'Other' / None assignment)          |  |
|  +-------------------------------------------------------------------+  |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | DSP Audio Signal Processing Engine                                |  |
|  |  - StreamingAudioLoader (Head 15-30s WAV stream, <10MB RAM)       |  |
|  |  - OnsetTempoDetector (STFT Flux, Autocorrelation 40-240 BPM)     |  |
|  |  - ChromagramKeyDetector (Precomputed Filterbank, Harmonic Corr)  |  |
|  |  - SafeAnalysisWrapper (Null Object / Error Isolation Guard)      |  |
|  +-------------------------------------------------------------------+  |
|                                                                         |
|  +-------------------------------------------------------------------+  |
|  | Renaming & Batch Coordination                                     |  |
|  |  - NameSynthesizer (Smart Replace / Anti-Duplication Format)      |  |
|  |  - BatchAnalysisCoordinator (ThreadPoolExecutor & Progress Signal)|  |
|  +-------------------------------------------------------------------+  |
+-------------------------------------------------------------------------+
```

---

## 2. Component Detailed Specifications

### 2.1 `FilenameParser`
- **Responsibility**: ファイル名文字列から高速かつ堅牢にメタデータを抽出し、各属性を正規化。
- **Methods**:
  - `parse_filename(file_path_or_name: str) -> ParsedMetadata`
  - `normalize_key(raw_key_string: str) -> Tuple[Optional[str], Optional[str]]`

### 2.2 `AudioSignalAnalyzer`
- **Responsibility**: NumPy / SciPy を用いて音声ファイルから定量的なテンポ（BPM）および調性（Key）を算出。
- **Methods**:
  - `analyze_file(file_path: str, max_duration_sec: float = 20.0) -> AudioAnalysisResult`
  - `estimate_bpm(signal: np.ndarray, sample_rate: int) -> Tuple[Optional[float], float]`
  - `estimate_key(signal: np.ndarray, sample_rate: int) -> Tuple[Optional[str], Optional[str], float]`

### 2.3 `AutoRenamer`
- **Responsibility**: 解析結果をもとに命名規則に沿った新ファイル名候補の生成および重複防止。
- **Methods**:
  - `generate_suggested_name(original_filename: str, bpm: Optional[float], key_root: Optional[str], key_scale: Optional[str]) -> str`
  - `create_rename_preview(samples: List[SampleItem], analysis_results: List[AudioAnalysisResult]) -> List[RenamePreviewItem]`

### 2.4 `BatchAnalysisCoordinator`
- **Responsibility**: `ThreadPoolExecutor` を用いて複数音源の並行解析を実行し、UIへ進捗（completed, total, current_item）を通知。
