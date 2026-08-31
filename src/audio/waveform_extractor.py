"""
Waveform peak extraction engine for BandLab Sound Manager.
Provides high-speed decimation and Min/Max peak normalization for UI visualization.
"""

from dataclasses import dataclass, field
import logging
import math
import os
from typing import List, Optional
import wave

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class WaveformData:
    """Represents normalized min/max peaks for waveform visualizer rendering."""
    peaks_min: List[float] = field(default_factory=list)
    peaks_max: List[float] = field(default_factory=list)
    duration_ms: int = 0
    sample_rate: int = 44100
    channels: int = 2
    is_valid: bool = True

    @property
    def num_bins(self) -> int:
        return len(self.peaks_min)

    @classmethod
    def create_null(cls, num_bins: int = 300) -> "WaveformData":
        """Creates a safe null waveform data object for missing/corrupt audio."""
        return cls(
            peaks_min=[0.0] * num_bins,
            peaks_max=[0.0] * num_bins,
            duration_ms=0,
            sample_rate=44100,
            channels=2,
            is_valid=False,
        )


class WaveformExtractor:
    """Extracts normalized peak amplitudes from audio files into fixed-size bins."""

    def __init__(self, default_bins: int = 300):
        self.default_bins = default_bins

    def extract_peaks(self, file_path: str, num_bins: Optional[int] = None) -> WaveformData:
        """
        Extracts min/max peak amplitudes from a WAV audio file.

        Args:
            file_path: Path to the WAV audio file.
            num_bins: Number of peak points (defaults to self.default_bins).

        Returns:
            WaveformData containing normalized peak lists [-1.0, 1.0].
        """
        bins = num_bins if num_bins is not None and num_bins > 0 else self.default_bins

        if not file_path or not os.path.isfile(file_path):
            logger.warning("Audio file does not exist: %s", file_path)
            return WaveformData.create_null(bins)

        try:
            with wave.open(file_path, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()

                if n_frames == 0 or framerate == 0:
                    return WaveformData.create_null(bins)

                duration_ms = int((n_frames / framerate) * 1000)

                # Read all raw frames
                raw_data = wf.readframes(n_frames)

                # Parse sample data based on bit depth
                if sampwidth == 1:
                    dtype = np.uint8
                    data = np.frombuffer(raw_data, dtype=dtype).astype(np.float32)
                    data = (data - 128.0) / 128.0
                elif sampwidth == 2:
                    dtype = np.int16
                    data = np.frombuffer(raw_data, dtype=dtype).astype(np.float32)
                    data = data / 32768.0
                elif sampwidth == 3:
                    # 24-bit PCM
                    raw_bytes = np.frombuffer(raw_data, dtype=np.uint8)
                    n_samples = len(raw_bytes) // 3
                    if n_samples == 0:
                        return WaveformData.create_null(bins)
                    raw_bytes = raw_bytes[: n_samples * 3].reshape(-1, 3)
                    # Convert 3-byte little endian to 32-bit int
                    samples = (
                        raw_bytes[:, 0].astype(np.int32)
                        | (raw_bytes[:, 1].astype(np.int32) << 8)
                        | (raw_bytes[:, 2].astype(np.int32) << 16)
                    )
                    # Sign extend negative 24-bit numbers
                    samples[samples >= 0x800000] -= 0x1000000
                    data = samples.astype(np.float32) / 8388608.0
                elif sampwidth == 4:
                    dtype = np.int32
                    data = np.frombuffer(raw_data, dtype=dtype).astype(np.float32)
                    data = data / 2147483648.0
                else:
                    logger.warning("Unsupported sample width: %d in %s", sampwidth, file_path)
                    return WaveformData.create_null(bins)

                # If multi-channel, downmix to mono (average of channels)
                if n_channels > 1:
                    total_samples = (len(data) // n_channels) * n_channels
                    data = data[:total_samples].reshape(-1, n_channels)
                    data = np.mean(data, axis=1)

                if len(data) == 0:
                    return WaveformData.create_null(bins)

                # Split into equal bins and compute min/max per bin
                # Use array_split to handle uneven divisions
                bin_arrays = np.array_split(data, bins)

                peaks_min = []
                peaks_max = []

                for chunk in bin_arrays:
                    if len(chunk) > 0:
                        mn = float(np.min(chunk))
                        mx = float(np.max(chunk))
                    else:
                        mn = 0.0
                        mx = 0.0
                    peaks_min.append(max(-1.0, min(1.0, mn)))
                    peaks_max.append(max(-1.0, min(1.0, mx)))

                return WaveformData(
                    peaks_min=peaks_min,
                    peaks_max=peaks_max,
                    duration_ms=duration_ms,
                    sample_rate=framerate,
                    channels=n_channels,
                    is_valid=True,
                )

        except Exception as e:
            logger.error("Failed to extract waveform peaks for %s: %s", file_path, e)
            return WaveformData.create_null(bins)
