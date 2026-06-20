"""
Traffic Sentinel — Video Processor Service
Service-layer wrapper around the core VideoProcessor module.
Adds progress callbacks, error handling, and result persistence.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from backend.app.core.logger import get_logger
from backend.app.config import settings
from backend.app.utils.video_utils import is_valid_video, get_video_meta, list_videos

logger = get_logger("traffic_sentinel.services.video_processor")


class VideoProcessorService:
    """
    Thin service wrapper that delegates to the core VideoProcessor while
    adding progress reporting and result caching.
    """

    def __init__(self) -> None:
        self._core: Optional[Any] = None  # lazy-loaded VideoProcessor
        logger.info("VideoProcessorService initialised")

    def _get_core(self):
        if self._core is None:
            try:
                from backend.app.video_processor import VideoProcessor
                self._core = VideoProcessor()
            except Exception as exc:
                logger.error("Failed to initialise VideoProcessor: %s", exc)
                raise
        return self._core

    # ── Public API ───────────────────────────────────────────────────────────

    def process(
        self,
        video_path: Path,
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> Dict:
        """
        Process *video_path* and return the result dict.
        *on_progress(pct, message)* is called periodically if provided.
        """
        if not is_valid_video(video_path):
            raise ValueError(f"Unsupported or missing video file: {video_path}")

        meta = get_video_meta(video_path)
        logger.info("Processing video: %s (%.1f MB)",
                    video_path.name,
                    meta["size_bytes"] / 1_048_576)

        if on_progress:
            on_progress(5, f"Loaded {video_path.name}")

        core = self._get_core()
        result: Dict = core.process_video(str(video_path))

        if on_progress:
            on_progress(90, "Saving results …")

        self._persist(result, video_path.stem)

        if on_progress:
            on_progress(100, "Done")

        return result

    def process_batch(
        self,
        video_paths: List[Path],
        on_progress: Optional[Callable[[int, str], None]] = None,
    ) -> List[Dict]:
        results = []
        n = len(video_paths)
        for i, p in enumerate(video_paths, 1):
            if on_progress:
                on_progress(int((i - 1) / n * 90), f"Processing {p.name} ({i}/{n})")
            try:
                results.append(self.process(p))
            except Exception as exc:
                logger.error("Failed to process %s: %s", p.name, exc)
                results.append({"video_name": p.name, "error": str(exc)})

        if on_progress:
            on_progress(100, f"Batch complete — {len(results)} videos processed")
        return results

    def list_available(self) -> List[Path]:
        return list_videos(settings.input_video_dir)

    def load_results(self) -> List[Dict]:
        """Return all persisted result JSON files from the output directory."""
        out_dir = settings.output_results_dir
        results = []
        for f in sorted(out_dir.glob("*.json")):
            try:
                with open(f) as fh:
                    results.append(json.load(fh))
            except Exception as exc:
                logger.warning("Could not read result file %s: %s", f, exc)
        return results

    # ── Internal ─────────────────────────────────────────────────────────────

    def _persist(self, result: Dict, stem: str) -> None:
        out_dir = settings.output_results_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{stem}_result.json"
        with open(out_file, "w") as fh:
            json.dump(result, fh, indent=2, default=str)
        logger.debug("Result saved: %s", out_file)