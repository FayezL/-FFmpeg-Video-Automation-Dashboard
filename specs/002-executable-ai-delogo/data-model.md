# Data Model: Logo Detection Entities

**Feature**: Standalone Executable & AI Logo Detection
**Date**: 2026-02-08
**Status**: Complete

## Overview

This document defines the core data entities for logo detection functionality. All entities are designed to be serializable (JSON-compatible) for storage and UI updates.

---

## Entity Definitions

### 1. DetectionResult

Represents a single detected logo region in a video frame.

**Purpose**: Store the output of logo detection algorithm for a specific region.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | `str` | Yes | Unique identifier for this detection | UUID format |
| `x` | `int` | Yes | Top-left X coordinate (pixels) | x ≥ 0 |
| `y` | `int` | Yes | Top-left Y coordinate (pixels) | y ≥ 0 |
| `width` | `int` | Yes | Region width (pixels) | width > 0 |
| `height` | `int` | Yes | Region height (pixels) | height > 0 |
| `confidence` | `float` | Yes | Detection confidence score | 0.0 ≤ confidence ≤ 1.0 |
| `frame_index` | `int` | Yes | Video frame where detected | frame_index ≥ 0 |
| `timestamp` | `float` | Yes | Video timestamp (seconds) | timestamp ≥ 0 |
| `preview_image` | `bytes` or `str` | No | Base64-encoded preview image | Optional for UI display |
| `status` | `str` | Yes | User review status | One of: "pending", "accepted", "rejected" |
| `detection_method` | `str` | Yes | Algorithm that found this region | One of: "edge", "corner", "template" |

**Relationships**:
- Belongs to one `DetectionSession`
- Can be saved to a `DetectionProfile` as a known pattern

**Validation Rules**:
- Bounding box must fit within video dimensions
- Confidence score must be between 0.0 and 1.0
- Frame index must be valid for the video
- Status must be one of the enum values

**Example (JSON)**:
```json
{
  "id": "det_7f8a9b2c",
  "x": 1635,
  "y": 240,
  "width": 176,
  "height": 147,
  "confidence": 0.87,
  "frame_index": 1200,
  "timestamp": 40.0,
  "preview_image": "data:image/png;base64,iVBORw0KG...",
  "status": "pending",
  "detection_method": "edge"
}
```

**State Transitions**:
```
pending → accepted  (user approves)
pending → rejected  (user rejects)
accepted → rejected (user changes mind)
rejected → accepted (user changes mind)
```

---

### 2. DetectionSession

Represents a complete logo detection run for a single video.

**Purpose**: Group all detection results and metadata for one video analysis.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `session_id` | `str` | Yes | Unique identifier for this session | UUID format |
| `video_path` | `str` | Yes | Path to analyzed video file | File must exist |
| `video_duration` | `float` | Yes | Total video duration (seconds) | duration > 0 |
| `video_fps` | `float` | Yes | Video frame rate | fps > 0 |
| `video_resolution` | `tuple[int, int]` | Yes | Video dimensions (width, height) | Both > 0 |
| `started_at` | `str` | Yes | Session start time (ISO 8601) | Valid datetime |
| `completed_at` | `str` | No | Session completion time | Valid datetime |
| `status` | `str` | Yes | Session status | One of: "running", "completed", "cancelled", "error" |
| `progress` | `float` | Yes | Detection progress percentage | 0.0 ≤ progress ≤ 1.0 |
| `frames_analyzed` | `int` | Yes | Number of frames processed | frames_analyzed ≥ 0 |
| `total_frames_to_analyze` | `int` | Yes | Total frames to process | Based on sampling rate |
| `results` | `List[DetectionResult]` | Yes | All detected regions | Can be empty list |
| `config` | `DetectionConfig` | Yes | Configuration used | See DetectionConfig entity |
| `error_message` | `str` | No | Error details if status="error" | Optional |

**Relationships**:
- Contains many `DetectionResult` entities
- Uses one `DetectionConfig`
- Can be saved as a `DetectionProfile` after completion

**Validation Rules**:
- started_at must be before completed_at
- progress must match frames_analyzed / total_frames_to_analyze
- If status="completed", completed_at must be set
- If status="error", error_message must be set

**Example (JSON)**:
```json
{
  "session_id": "sess_abc123",
  "video_path": "C:/Videos/movie.mp4",
  "video_duration": 7200.0,
  "video_fps": 29.97,
  "video_resolution": [1920, 1080],
  "started_at": "2026-02-08T10:30:00Z",
  "completed_at": "2026-02-08T10:32:45Z",
  "status": "completed",
  "progress": 1.0,
  "frames_analyzed": 4000,
  "total_frames_to_analyze": 4000,
  "results": [
    { /* DetectionResult 1 */ },
    { /* DetectionResult 2 */ }
  ],
  "config": { /* DetectionConfig */ },
  "error_message": null
}
```

**State Transitions**:
```
running → completed  (normal completion)
running → cancelled  (user cancels)
running → error      (exception occurs)
```

---

### 3. DetectionConfig

Configuration settings for logo detection algorithm.

**Purpose**: Store all parameters that affect detection behavior, allowing users to save and reuse effective configurations.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `sensitivity` | `float` | Yes | Detection sensitivity threshold | 0.0 ≤ sensitivity ≤ 1.0 |
| `frame_sampling` | `int` | Yes | Analyze every Nth frame | frame_sampling ≥ 1 |
| `min_logo_width` | `int` | Yes | Minimum logo width (pixels) | min_logo_width > 0 |
| `min_logo_height` | `int` | Yes | Minimum logo height (pixels) | min_logo_height > 0 |
| `max_logo_width` | `int` | Yes | Maximum logo width (pixels) | max_logo_width > min_logo_width |
| `max_logo_height` | `int` | Yes | Maximum logo height (pixels) | max_logo_height > min_logo_height |
| `aspect_ratio_min` | `float` | Yes | Minimum width/height ratio | aspect_ratio_min > 0 |
| `aspect_ratio_max` | `float` | Yes | Maximum width/height ratio | aspect_ratio_max > aspect_ratio_min |
| `position_zones` | `List[str]` | Yes | Allowed logo positions | Valid zone names |
| `edge_threshold_low` | `int` | Yes | Canny edge detection low threshold | 0 ≤ value ≤ 255 |
| `edge_threshold_high` | `int` | Yes | Canny edge detection high threshold | low < high ≤ 255 |
| `enable_template_matching` | `bool` | Yes | Use saved logo patterns | true or false |
| `merge_overlap_threshold` | `float` | Yes | Merge regions if overlap > threshold | 0.0 ≤ value ≤ 1.0 |

**Position Zones** (enum values):
- `"top-left"` - Upper-left corner (0-20% width, 0-20% height)
- `"top-right"` - Upper-right corner (80-100% width, 0-20% height)
- `"bottom-left"` - Lower-left corner (0-20% width, 80-100% height)
- `"bottom-right"` - Lower-right corner (80-100% width, 80-100% height)
- `"top-center"` - Top center (40-60% width, 0-20% height)
- `"bottom-center"` - Bottom center (40-60% width, 80-100% height)
- `"anywhere"` - No position restriction

**Default Values**:
```json
{
  "sensitivity": 0.75,
  "frame_sampling": 30,
  "min_logo_width": 20,
  "min_logo_height": 20,
  "max_logo_width": 300,
  "max_logo_height": 150,
  "aspect_ratio_min": 0.5,
  "aspect_ratio_max": 5.0,
  "position_zones": ["top-left", "top-right", "bottom-left", "bottom-right"],
  "edge_threshold_low": 50,
  "edge_threshold_high": 150,
  "enable_template_matching": false,
  "merge_overlap_threshold": 0.5
}
```

**Validation Rules**:
- All numeric ranges must be validated
- At least one position zone must be specified
- edge_threshold_high must be greater than edge_threshold_low

---

### 4. DetectionProfile

Saved configuration and learned patterns for recurring logo detection scenarios.

**Purpose**: Allow users to save effective detection configurations and share them across videos from the same source.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `version` | `str` | Yes | Profile format version | Semantic versioning (e.g., "1.0") |
| `profile_id` | `str` | Yes | Unique identifier | UUID format |
| `name` | `str` | Yes | User-friendly profile name | 1-100 characters |
| `description` | `str` | No | Profile description | Optional, 0-500 characters |
| `created_at` | `str` | Yes | Creation timestamp (ISO 8601) | Valid datetime |
| `modified_at` | `str` | Yes | Last modification timestamp | Valid datetime, >= created_at |
| `config` | `DetectionConfig` | Yes | Detection configuration | See DetectionConfig |
| `known_patterns` | `List[LogoPattern]` | Yes | Saved logo templates | Can be empty list |
| `statistics` | `ProfileStatistics` | Yes | Usage statistics | See ProfileStatistics |
| `tags` | `List[str]` | Yes | Search tags (e.g., "CNN", "news") | Lowercase, no spaces |

**Relationships**:
- Contains one `DetectionConfig`
- Contains many `LogoPattern` entities
- Contains one `ProfileStatistics`

**File Storage**:
- Location: `%APPDATA%/MagicTVBox/profiles/{profile_name}.json`
- Format: JSON with 2-space indentation
- Permissions: User read/write only

**Example (JSON)**:
```json
{
  "version": "1.0",
  "profile_id": "prof_xyz789",
  "name": "CNN News Watermark",
  "description": "Profile for detecting CNN watermark in recorded news broadcasts",
  "created_at": "2026-02-08T10:00:00Z",
  "modified_at": "2026-02-08T10:30:00Z",
  "config": {
    "sensitivity": 0.8,
    "frame_sampling": 30,
    "min_logo_width": 150,
    "min_logo_height": 100,
    "max_logo_width": 200,
    "max_logo_height": 150,
    "aspect_ratio_min": 1.0,
    "aspect_ratio_max": 2.0,
    "position_zones": ["bottom-right"],
    "edge_threshold_low": 60,
    "edge_threshold_high": 160,
    "enable_template_matching": true,
    "merge_overlap_threshold": 0.6
  },
  "known_patterns": [
    {
      "pattern_id": "pat_001",
      "name": "CNN Logo",
      "x": 1635,
      "y": 240,
      "width": 176,
      "height": 147,
      "reference_frame": "base64_encoded_image...",
      "confidence_threshold": 0.85
    }
  ],
  "statistics": {
    "videos_processed": 15,
    "total_detections": 15,
    "accepted_detections": 13,
    "rejected_detections": 2,
    "average_confidence": 0.87,
    "average_processing_time": 125.5
  },
  "tags": ["cnn", "news", "watermark", "bottom-right"]
}
```

**Validation Rules**:
- Profile name must be unique within user's profile directory
- modified_at must be >= created_at
- Statistics must be consistent (accepted + rejected = total_detections)

---

### 5. LogoPattern

Template for matching a specific logo using template matching.

**Purpose**: Store a known logo appearance for faster and more accurate detection in future videos.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `pattern_id` | `str` | Yes | Unique identifier | UUID format |
| `name` | `str` | Yes | Pattern name (e.g., "CNN Logo") | 1-100 characters |
| `x` | `int` | Yes | Reference X coordinate | x ≥ 0 |
| `y` | `int` | Yes | Reference Y coordinate | y ≥ 0 |
| `width` | `int` | Yes | Pattern width | width > 0 |
| `height` | `int` | Yes | Pattern height | height > 0 |
| `reference_frame` | `str` | Yes | Base64-encoded template image | Valid base64 PNG |
| `confidence_threshold` | `float` | Yes | Match threshold for this pattern | 0.0 ≤ value ≤ 1.0 |
| `match_method` | `str` | Yes | OpenCV matching method | One of: "TM_CCOEFF_NORMED", "TM_CCORR_NORMED" |
| `scale_tolerance` | `float` | Yes | Allow pattern scaling ±N% | 0.0 ≤ value ≤ 0.5 |

**Match Methods**:
- `"TM_CCOEFF_NORMED"` - Correlation coefficient (best for most logos)
- `"TM_CCORR_NORMED"` - Cross-correlation (faster, less accurate)

**Example**:
```json
{
  "pattern_id": "pat_001",
  "name": "CNN Logo",
  "x": 1635,
  "y": 240,
  "width": 176,
  "height": 147,
  "reference_frame": "iVBORw0KGgoAAAANSUhEUg...",
  "confidence_threshold": 0.85,
  "match_method": "TM_CCOEFF_NORMED",
  "scale_tolerance": 0.1
}
```

---

### 6. ProfileStatistics

Usage statistics for a detection profile.

**Purpose**: Track profile effectiveness and help users choose the best profile.

**Attributes**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `videos_processed` | `int` | Yes | Number of videos analyzed | videos_processed ≥ 0 |
| `total_detections` | `int` | Yes | Total regions detected | total_detections ≥ 0 |
| `accepted_detections` | `int` | Yes | User-accepted regions | accepted_detections ≥ 0 |
| `rejected_detections` | `int` | Yes | User-rejected regions | rejected_detections ≥ 0 |
| `average_confidence` | `float` | Yes | Mean confidence score | 0.0 ≤ value ≤ 1.0 |
| `average_processing_time` | `float` | Yes | Mean detection time (seconds) | time ≥ 0 |
| `last_used` | `str` | No | Last use timestamp (ISO 8601) | Valid datetime |

**Derived Metrics**:
- **Accuracy Rate**: `accepted_detections / total_detections`
- **False Positive Rate**: `rejected_detections / total_detections`

**Validation Rules**:
- `accepted_detections + rejected_detections ≤ total_detections`
- If `videos_processed == 0`, all other stats should be 0

---

## Entity Relationships

```
DetectionProfile (1) ──contains──> (1) DetectionConfig
DetectionProfile (1) ──contains──> (*) LogoPattern
DetectionProfile (1) ──contains──> (1) ProfileStatistics

DetectionSession (1) ──uses──> (1) DetectionConfig
DetectionSession (1) ──produces──> (*) DetectionResult

DetectionResult (*) ──can become──> (1) LogoPattern
```

## Storage Strategy

### In-Memory (During Detection)

- `DetectionSession` - Active session state
- `DetectionResult[]` - Live results being processed
- `DetectionConfig` - Current configuration

### Persisted (After Detection)

- `DetectionProfile` - Saved to `profiles/*.json`
- `LogoPattern` - Embedded in profiles
- `ProfileStatistics` - Updated on each use

### Temporary (UI State)

- `preview_image` in `DetectionResult` - Cached for UI display, not saved
- `progress` in `DetectionSession` - Updated every 100ms, not persisted

## Migration Strategy

### Version 1.0 (Initial)

All entities as defined above.

### Future Versions

When schema changes:
1. Increment `version` field in profiles
2. Implement migration function in `detection_profiles.py`:
   ```python
   def migrate_profile(old_profile: dict) -> DetectionProfile:
       version = old_profile.get("version", "1.0")
       if version == "1.0":
           return DetectionProfile(**old_profile)
       # Future migrations here
   ```

## Validation Implementation

All entities should implement:
```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class DetectionResult:
    id: str
    x: int
    y: int
    width: int
    height: int
    confidence: float
    frame_index: int
    timestamp: float
    status: str
    detection_method: str
    preview_image: Optional[str] = None

    def validate(self) -> bool:
        """Validate all constraints"""
        assert self.x >= 0, "x must be >= 0"
        assert self.y >= 0, "y must be >= 0"
        assert self.width > 0, "width must be > 0"
        assert self.height > 0, "height must be > 0"
        assert 0.0 <= self.confidence <= 1.0, "confidence must be 0-1"
        assert self.status in ["pending", "accepted", "rejected"], "invalid status"
        return True

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict"""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "frame_index": self.frame_index,
            "timestamp": self.timestamp,
            "status": self.status,
            "detection_method": self.detection_method,
            "preview_image": self.preview_image
        }

    @classmethod
    def from_dict(cls, data: dict):
        """Deserialize from JSON dict"""
        result = cls(**data)
        result.validate()
        return result
```

---

**Data model complete. All entities defined with validation rules and relationships.**
