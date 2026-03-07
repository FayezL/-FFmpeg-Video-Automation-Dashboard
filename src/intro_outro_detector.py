"""
Intro/Outro Detector — Perceptual hashing for repeating video segments.

Analyses the first and last ~2 minutes of a video, computes perceptual
hashes (pHash) of sampled frames, and matches them against stored
series profiles to detect intro/outro segments.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Callable, List, Optional

import cv2
import numpy as np

from src.state import (
    DetectedSegment,
    DetectionProfile,
    DetectionResult,
    SegmentPattern,
)

# How many seconds at the start/end to scan
_SCAN_WINDOW = 120  # 2 minutes
# Sample one frame per second
_SAMPLE_FPS = 1.0
# Minimum segment length we bother detecting (seconds)
_MIN_SEGMENT = 3.0
# Hash size (8x8 DCT block → 64-bit hash)
_HASH_SIZE = 8


# ======================================================================= #
#  Perceptual hashing                                                      #
# ======================================================================= #

def _phash(frame: np.ndarray) -> str:
    """Compute a 64-bit perceptual hash of a BGR frame.

    Steps: resize → grayscale → 32x32 → DCT → top-left 8x8 → median threshold.
    Returns a 16-char hex string.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if len(frame.shape) == 3 else frame
    resized = cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32)
    dct = cv2.dct(resized)
    dct_low = dct[:_HASH_SIZE, :_HASH_SIZE]
    median = float(np.median(dct_low))
    bits = (dct_low > median).flatten()
    # Pack 64 bits into an integer → hex
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return f"{h:016x}"


def _hamming(a: str, b: str) -> int:
    """Hamming distance between two hex-encoded hashes."""
    return bin(int(a, 16) ^ int(b, 16)).count("1")


# ======================================================================= #
#  Frame extraction                                                        #
# ======================================================================= #

def _extract_hashes(
    cap: cv2.VideoCapture,
    start_sec: float,
    end_sec: float,
    progress_cb: Optional[Callable[[float], None]] = None,
) -> List[str]:
    """Sample frames from [start_sec, end_sec) at 1 fps and hash each."""
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    total = end_sec - start_sec
    hashes: List[str] = []

    t = start_sec
    while t < end_sec:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = cap.read()
        if not ok:
            break
        hashes.append(_phash(frame))
        t += 1.0 / _SAMPLE_FPS

        if progress_cb and total > 0:
            progress_cb(min(1.0, (t - start_sec) / total))

    return hashes


# ======================================================================= #
#  Segment detection                                                       #
# ======================================================================= #

def _find_segment_boundary(hashes: List[str], direction: str = "forward") -> Optional[float]:
    """Detect where a repeating segment ends (intro) or begins (outro).

    Looks for a sustained jump in hash dissimilarity — the point
    where the content changes from the intro/outro to the main show.
    Returns the boundary time offset in seconds, or None.
    """
    if len(hashes) < 5:
        return None

    # Compute pairwise similarity of consecutive hashes
    diffs = []
    for i in range(1, len(hashes)):
        d = _hamming(hashes[i - 1], hashes[i])
        diffs.append(d)

    if not diffs:
        return None

    # A sharp rise in hamming distance signals a content transition.
    mean_diff = sum(diffs) / len(diffs)
    threshold = max(mean_diff * 2.5, 12)  # At least 12 bits different

    # Scan for the first window of 3+ consecutive high-diff frames
    window = 3
    for i in range(len(diffs) - window + 1):
        if all(diffs[i + j] >= threshold for j in range(window)):
            boundary = float(i) / _SAMPLE_FPS  # seconds
            if boundary >= _MIN_SEGMENT:
                return boundary

    return None


# ======================================================================= #
#  Main detector class                                                     #
# ======================================================================= #

class IntroOutroDetector:
    """Detects intro/outro segments using perceptual hashing."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        if profiles_dir is None:
            import sys
            if sys.platform == "win32":
                base = Path.home() / "AppData" / "Local" / "MagicTVBox"
            else:
                base = Path.home() / ".config" / "magictvbox"
            profiles_dir = base / "detection_profiles"
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    #  Analyse a video                                                     #
    # ------------------------------------------------------------------ #

    def analyze_video(
        self,
        video_path: str,
        series_name: Optional[str] = None,
        progress_callback: Optional[Callable[[float], None]] = None,
    ) -> DetectionResult:
        """Scan a video and return detected intro/outro segments."""
        t0 = time.time()

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return DetectionResult(file_path=video_path,
                                  error="Could not open video file")

        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = total_frames / fps if fps > 0 else 0

        if duration < 30:
            cap.release()
            return DetectionResult(file_path=video_path,
                                  error="Video too short for detection")

        intro_end_sec = min(_SCAN_WINDOW, duration * 0.25)
        outro_start_sec = max(duration - _SCAN_WINDOW, duration * 0.75)

        def _intro_progress(p):
            if progress_callback:
                progress_callback(p * 0.5)  # first half

        def _outro_progress(p):
            if progress_callback:
                progress_callback(0.5 + p * 0.5)  # second half

        # Intro scan
        intro_hashes = _extract_hashes(cap, 0, intro_end_sec, _intro_progress)
        intro_boundary = _find_segment_boundary(intro_hashes, "forward")

        # Outro scan
        outro_hashes = _extract_hashes(cap, outro_start_sec, duration, _outro_progress)
        # For outro we look for where the main content transitions INTO the outro
        outro_boundary = _find_segment_boundary(outro_hashes, "forward")

        cap.release()
        elapsed = time.time() - t0

        # Check against existing profile for confidence boost
        series_id = self._series_id(series_name) if series_name else None
        profile = self.load_profile(series_id) if series_id else None

        intro_seg = None
        if intro_boundary is not None:
            confidence = 0.65  # Base confidence from hash analysis
            if profile and profile.intro_pattern:
                sim = profile.intro_pattern.similarity_score(
                    intro_hashes[: int(intro_boundary * _SAMPLE_FPS)]
                )
                confidence = min(0.95, 0.5 + sim * 0.5)
            intro_seg = DetectedSegment(
                segment_type="intro",
                start_time=0.0,
                end_time=intro_boundary,
                confidence=round(confidence, 2),
                method="hash_match" if profile else "hash_analysis",
            )

        outro_seg = None
        if outro_boundary is not None:
            confidence = 0.60
            if profile and profile.outro_pattern:
                sim = profile.outro_pattern.similarity_score(
                    outro_hashes[int(outro_boundary * _SAMPLE_FPS):]
                )
                confidence = min(0.95, 0.5 + sim * 0.5)
            outro_seg = DetectedSegment(
                segment_type="outro",
                start_time=outro_start_sec + outro_boundary,
                end_time=duration,
                confidence=round(confidence, 2),
                method="hash_match" if profile else "hash_analysis",
            )

        return DetectionResult(
            file_path=video_path,
            series_id=series_id,
            intro=intro_seg,
            outro=outro_seg,
            analysis_duration=round(elapsed, 2),
        )

    # ------------------------------------------------------------------ #
    #  Profile management                                                  #
    # ------------------------------------------------------------------ #

    def load_profile(self, series_id: str) -> Optional[DetectionProfile]:
        """Load a detection profile from disk."""
        path = self.profiles_dir / f"{series_id}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return self._profile_from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def save_profile(self, profile: DetectionProfile) -> None:
        """Persist a detection profile to disk."""
        path = self.profiles_dir / f"{profile.series_id}.json"
        path.write_text(
            json.dumps(self._profile_to_dict(profile), indent=2),
            encoding="utf-8",
        )

    def learn_from_correction(
        self,
        series_name: str,
        segment_type: str,
        hashes: List[str],
        duration: float,
    ) -> None:
        """Update a profile when the user corrects a detection."""
        sid = self._series_id(series_name)
        profile = self.load_profile(sid) or DetectionProfile(
            series_id=sid, series_name=series_name
        )

        pattern = SegmentPattern(
            perceptual_hashes=hashes,
            duration_seconds=duration,
            sample_count=1,
        )

        if segment_type == "intro":
            if profile.intro_pattern:
                profile.intro_pattern.sample_count += 1
            profile.intro_pattern = pattern
        else:
            if profile.outro_pattern:
                profile.outro_pattern.sample_count += 1
            profile.outro_pattern = pattern

        profile.user_corrections += 1
        profile.episodes_analyzed += 1
        profile.last_updated = time.time()
        self.save_profile(profile)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _series_id(name: str) -> str:
        return hashlib.md5(name.lower().strip().encode()).hexdigest()[:16]

    @staticmethod
    def _profile_to_dict(p: DetectionProfile) -> dict:
        def _pat(sp: Optional[SegmentPattern]) -> Optional[dict]:
            if sp is None:
                return None
            return {
                "hashes": sp.perceptual_hashes,
                "duration": sp.duration_seconds,
                "offset": sp.start_offset,
                "samples": sp.sample_count,
            }
        return {
            "series_id": p.series_id,
            "series_name": p.series_name,
            "intro": _pat(p.intro_pattern),
            "outro": _pat(p.outro_pattern),
            "threshold": p.confidence_threshold,
            "corrections": p.user_corrections,
            "episodes": p.episodes_analyzed,
            "updated": p.last_updated,
        }

    @staticmethod
    def _profile_from_dict(d: dict) -> DetectionProfile:
        def _pat(raw: Optional[dict]) -> Optional[SegmentPattern]:
            if raw is None:
                return None
            return SegmentPattern(
                perceptual_hashes=raw["hashes"],
                duration_seconds=raw["duration"],
                start_offset=raw.get("offset", 0.0),
                sample_count=raw.get("samples", 1),
            )
        return DetectionProfile(
            series_id=d["series_id"],
            series_name=d["series_name"],
            intro_pattern=_pat(d.get("intro")),
            outro_pattern=_pat(d.get("outro")),
            confidence_threshold=d.get("threshold", 0.75),
            user_corrections=d.get("corrections", 0),
            episodes_analyzed=d.get("episodes", 0),
            last_updated=d.get("updated", 0.0),
        )
