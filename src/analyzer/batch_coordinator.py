"""Batch analysis coordinator for parallel audio DSP processing."""
import concurrent.futures
from pathlib import Path
from typing import List, Callable, Optional

from src.analyzer.audio_analyzer import AudioSignalAnalyzer, AudioAnalysisResult


class BatchAnalysisCoordinator:
    """Coordinates multi-threaded batch DSP analysis for multiple sound sample files."""

    def __init__(self, analyzer: Optional[AudioSignalAnalyzer] = None, max_workers: int = 4):
        self.analyzer = analyzer or AudioSignalAnalyzer()
        self.max_workers = max_workers

    def analyze_batch(
        self,
        file_paths: List[str],
        on_progress: Optional[Callable[[int, int, str], None]] = None,
        max_duration_sec: float = 20.0,
    ) -> List[AudioAnalysisResult]:
        """Analyzes a list of audio files in parallel using ThreadPoolExecutor.
        
        Args:
            file_paths: List of absolute file paths to analyze.
            on_progress: Optional callback function signature (completed_count, total_count, current_filename).
            max_duration_sec: Maximum audio duration to load for each file.
            
        Returns:
            List[AudioAnalysisResult]: List of analysis results in same order.
        """
        total = len(file_paths)
        if total == 0:
            return []

        results: List[Optional[AudioAnalysisResult]] = [None] * total
        completed_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Map future to index
            future_to_index = {
                executor.submit(self.analyzer.analyze_file, fp, max_duration_sec): idx
                for idx, fp in enumerate(file_paths)
            }

            for future in concurrent.futures.as_completed(future_to_index):
                idx = future_to_index[future]
                fp = file_paths[idx]
                try:
                    res = future.result()
                except Exception:
                    # Safe fallback
                    res = AudioAnalysisResult(
                        file_path=str(Path(fp).resolve()),
                        estimated_bpm=None,
                        estimated_key_root=None,
                        estimated_key_scale=None,
                        bpm_confidence=0.0,
                        key_confidence=0.0,
                        suggested_filename="",
                        is_loop_candidate=False,
                    )

                results[idx] = res
                completed_count += 1

                if on_progress:
                    on_progress(completed_count, total, Path(fp).name)

        return [r for r in results if r is not None]
