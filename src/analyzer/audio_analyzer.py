"""Audio signal processing engine for BPM and Key detection using NumPy and SciPy."""
import os
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple

import numpy as np


@dataclass
class AudioAnalysisResult:
    """Quantitative audio signal analysis result."""
    file_path: str
    estimated_bpm: Optional[float] = None
    estimated_key_root: Optional[str] = None
    estimated_key_scale: Optional[str] = None
    bpm_confidence: float = 0.0
    key_confidence: float = 0.0
    suggested_filename: str = ""
    is_loop_candidate: bool = False


class AudioSignalAnalyzer:
    """Lightweight and robust audio DSP analyzer for tempo (BPM) and tonal key detection."""

    # Note names for 12 chroma pitch classes
    PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

    # Krumhansl-Schmuckler Key Profiles for Major and Minor scales
    MAJOR_PROFILE = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    MINOR_PROFILE = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

    def __init__(self, target_sample_rate: int = 22050):
        self.target_sample_rate = target_sample_rate
        # Precompute normalized key profile matrices for fast correlation
        self._major_profiles = self._build_rotated_profiles(self.MAJOR_PROFILE)
        self._minor_profiles = self._build_rotated_profiles(self.MINOR_PROFILE)

    @classmethod
    def _build_rotated_profiles(cls, base_profile: np.ndarray) -> np.ndarray:
        """Builds 12 circular rotations of the tonal profile vector."""
        profiles = np.zeros((12, 12))
        norm_base = base_profile - np.mean(base_profile)
        norm_base = norm_base / (np.linalg.norm(norm_base) + 1e-9)
        for i in range(12):
            profiles[i] = np.roll(norm_base, i)
        return profiles

    def load_audio_head(self, file_path: str, max_duration_sec: float = 20.0) -> Tuple[np.ndarray, int]:
        """Loads and converts the head portion of an audio file to mono float32 array.
        
        Args:
            file_path: Path to audio file.
            max_duration_sec: Maximum duration in seconds to load (default 20s).
            
        Returns:
            Tuple[np.ndarray, int]: (Mono audio samples [-1.0, 1.0], sample_rate)
        """
        p = Path(file_path).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Audio file does not exist: {file_path}")

        # Try standard wave module first for fast header parsing and seeking
        try:
            with wave.open(str(p), "rb") as wf:
                sr = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                max_frames = int(sr * max_duration_sec)
                raw_bytes = wf.readframes(max_frames)

                if sampwidth == 2:
                    audio_data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
                elif sampwidth == 1:
                    audio_data = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
                elif sampwidth == 3:
                    # 24-bit PCM
                    raw_array = np.frombuffer(raw_bytes, dtype=np.uint8)
                    n_samples = len(raw_array) // 3
                    samples = np.zeros(n_samples, dtype=np.int32)
                    for i in range(3):
                        samples |= raw_array[i::3].astype(np.int32) << (i * 8 + 8)
                    audio_data = samples.astype(np.float32) / 2147483648.0
                elif sampwidth == 4:
                    audio_data = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
                else:
                    audio_data = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0

                if n_channels > 1:
                    audio_data = audio_data.reshape(-1, n_channels).mean(axis=1)

                return audio_data, sr
        except Exception:
            # Fallback to scipy.io.wavfile
            from scipy.io import wavfile
            sr, data = wavfile.read(str(p))
            max_samples = int(sr * max_duration_sec)
            data = data[:max_samples]

            if data.dtype == np.int16:
                audio_data = data.astype(np.float32) / 32768.0
            elif data.dtype == np.int32:
                audio_data = data.astype(np.float32) / 2147483648.0
            elif data.dtype == np.uint8:
                audio_data = (data.astype(np.float32) - 128.0) / 128.0
            else:
                audio_data = data.astype(np.float32)

            if audio_data.ndim > 1:
                audio_data = audio_data.mean(axis=1)

            return audio_data, sr

    def estimate_bpm(self, audio: np.ndarray, sample_rate: int) -> Tuple[Optional[float], float]:
        """Estimates tempo (BPM) using spectral flux onset envelope autocorrelation across 40-240 BPM.
        
        Returns:
            Tuple[Optional[float], float]: (Estimated BPM, Confidence score 0.0〜1.0)
        """
        if len(audio) < sample_rate * 0.5:
            return None, 0.0

        from scipy import signal

        # Resample if needed
        if sample_rate != self.target_sample_rate:
            num_target_samples = int(len(audio) * self.target_sample_rate / sample_rate)
            audio = signal.resample(audio, num_target_samples)
            sr = self.target_sample_rate
        else:
            sr = sample_rate

        # Compute STFT for onset envelope
        n_fft = 1024
        hop_length = 256
        f, t, zxx = signal.stft(audio, fs=sr, nperseg=n_fft, noverlap=n_fft - hop_length)
        magnitude = np.abs(zxx)

        # Spectral flux: positive first-difference across time frames
        diff = np.diff(magnitude, axis=1)
        onset_env = np.sum(np.maximum(0, diff), axis=0)

        # Normalize onset envelope
        onset_env = onset_env - np.mean(onset_env)
        norm = np.linalg.norm(onset_env)
        if norm < 1e-6:
            return None, 0.0
        onset_env = onset_env / norm

        # Autocorrelation of onset envelope
        autocorr = np.correlate(onset_env, onset_env, mode="full")
        autocorr = autocorr[len(autocorr) // 2:]

        # Map lag range for 40 BPM to 240 BPM
        # BPM = 60 * sr / (hop_length * lag) -> lag = 60 * sr / (hop_length * BPM)
        min_bpm, max_bpm = 40.0, 240.0
        min_lag = int(60.0 * sr / (hop_length * max_bpm))
        max_lag = int(60.0 * sr / (hop_length * min_bpm))

        if max_lag >= len(autocorr):
            max_lag = len(autocorr) - 1
        if min_lag >= max_lag:
            return None, 0.0

        search_slice = autocorr[min_lag:max_lag + 1]
        best_lag_offset = np.argmax(search_slice)
        best_lag = min_lag + best_lag_offset
        peak_val = search_slice[best_lag_offset]

        estimated_bpm = (60.0 * sr) / (hop_length * best_lag)

        # Calculate confidence from peak-to-mean ratio
        mean_val = np.mean(search_slice) + 1e-9
        confidence = float(np.clip((peak_val - mean_val) / (peak_val + 1e-9), 0.0, 1.0))

        return round(float(estimated_bpm), 1), confidence

    def estimate_key(self, audio: np.ndarray, sample_rate: int) -> Tuple[Optional[str], Optional[str], float]:
        """Estimates musical key root and scale (Major/Minor) using Chromagram template matching.
        
        Returns:
            Tuple[Optional[str], Optional[str], float]: (Key Root e.g. "C#", Scale "minor"/"major", Confidence)
        """
        if len(audio) < sample_rate * 0.5:
            return None, None, 0.0

        from scipy import signal

        # Resample if needed
        if sample_rate != self.target_sample_rate:
            num_target_samples = int(len(audio) * self.target_sample_rate / sample_rate)
            audio = signal.resample(audio, num_target_samples)
            sr = self.target_sample_rate
        else:
            sr = sample_rate

        # Compute STFT
        n_fft = 2048
        hop_length = 512
        f, t, zxx = signal.stft(audio, fs=sr, nperseg=n_fft, noverlap=n_fft - hop_length)
        magnitude = np.abs(zxx)

        # Map frequencies to 12 pitch classes (A4 = 440 Hz)
        # Note number MIDI = 69 + 12 * log2(f / 440)
        # Chroma class = MIDI % 12 (0=C, 1=C#, 2=D, ... 9=A)
        chroma = np.zeros(12)
        valid_freq_mask = (f > 65.0) & (f < 2000.0)  # Filter relevant musical harmonic range (C2 to B6)

        freqs = f[valid_freq_mask]
        mags = magnitude[valid_freq_mask, :].mean(axis=1)

        for freq, mag in zip(freqs, mags):
            midi_note = 69.0 + 12.0 * np.log2(freq / 440.0)
            pitch_idx = int(np.round(midi_note)) % 12
            # 0 in MIDI % 12 is C (60 % 12 == 0)
            chroma[pitch_idx] += mag

        norm_chroma = chroma - np.mean(chroma)
        c_norm = np.linalg.norm(norm_chroma)
        if c_norm < 1e-6:
            return None, None, 0.0
        norm_chroma = norm_chroma / c_norm

        # Correlate with 12 Major and 12 Minor profiles
        major_corr = np.dot(self._major_profiles, norm_chroma)
        minor_corr = np.dot(self._minor_profiles, norm_chroma)

        best_maj_idx = int(np.argmax(major_corr))
        best_min_idx = int(np.argmax(minor_corr))

        max_maj_val = major_corr[best_maj_idx]
        max_min_val = minor_corr[best_min_idx]

        if max_maj_val >= max_min_val:
            key_root = self.PITCH_CLASSES[best_maj_idx]
            key_scale = "major"
            confidence = float(np.clip(max_maj_val, 0.0, 1.0))
        else:
            key_root = self.PITCH_CLASSES[best_min_idx]
            key_scale = "minor"
            confidence = float(np.clip(max_min_val, 0.0, 1.0))

        return key_root, key_scale, confidence

    def analyze_file(self, file_path: str, max_duration_sec: float = 20.0) -> AudioAnalysisResult:
        """Analyzes an audio file and returns quantitative BPM and Key detection results.
        
        Implements Safe Analysis Result (Null Object) pattern (RESILIENCY-10) on decode errors.
        """
        try:
            audio, sr = self.load_audio_head(file_path, max_duration_sec=max_duration_sec)
            bpm, bpm_conf = self.estimate_bpm(audio, sr)
            key_root, key_scale, key_conf = self.estimate_key(audio, sr)

            return AudioAnalysisResult(
                file_path=str(Path(file_path).resolve()),
                estimated_bpm=bpm,
                estimated_key_root=key_root,
                estimated_key_scale=key_scale,
                bpm_confidence=bpm_conf,
                key_confidence=key_conf,
                is_loop_candidate=bool(bpm is not None and bpm_conf > 0.4),
            )
        except Exception:
            # Error isolation guard: return safe Null Object result
            return AudioAnalysisResult(
                file_path=str(Path(file_path).resolve()) if file_path else "",
                estimated_bpm=None,
                estimated_key_root=None,
                estimated_key_scale=None,
                bpm_confidence=0.0,
                key_confidence=0.0,
                suggested_filename="",
                is_loop_candidate=False,
            )
