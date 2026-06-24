# Video Trim Modes Guide

This guide explains all video trimming modes with clear examples.

## Overview

The app supports 4 trim modes:
1. **NONE** - No trimming (keep entire video)
2. **CUT_LAST** - Remove time from the END
3. **CUT_FIRST** - Remove time from the START
4. **CUT_RANGE** - Extract a specific time range

---

## Mode Details

### Mode 1: NONE
**Keep the entire video without any trimming.**

**Example:**
- Input: 2-hour movie (0:00:00 to 2:00:00)
- Output: Full 2-hour movie (0:00:00 to 2:00:00)

---

### Mode 2: CUT_LAST
**Remove time from the END, keep the BEGINNING.**

**Fields:**
- `cut_hours`: Hours to remove from end
- `cut_minutes`: Minutes to remove from end
- `cut_seconds`: Seconds to remove from end

**Example 1 - Remove last 5 minutes:**
- Input: 2-hour movie (7200 seconds)
- Settings: hours=0, minutes=5, seconds=0
- Output: 0:00:00 to 1:55:00 (7200 - 300 = 6900 seconds)

**Example 2 - Remove last 10 seconds:**
- Input: 2-hour movie (7200 seconds)
- Settings: hours=0, minutes=0, seconds=10
- Output: 0:00:00 to 1:59:50 (7200 - 10 = 7190 seconds)

---

### Mode 3: CUT_FIRST
**Remove time from the START, keep the END.**

**Fields:**
- `cut_hours`: Hours to remove from start
- `cut_minutes`: Minutes to remove from start
- `cut_seconds`: Seconds to remove from start

**Example 1 - Remove first 10 seconds:**
- Input: 2-hour movie (7200 seconds)
- Settings: hours=0, minutes=0, seconds=10
- Output: 0:00:10 to 2:00:00 (starts at 10s, duration 7190 seconds)

**Example 2 - Remove first 5 minutes:**
- Input: 2-hour movie (7200 seconds)
- Settings: hours=0, minutes=5, seconds=0
- Output: 0:05:00 to 2:00:00 (starts at 300s, duration 6900 seconds)

---

### Mode 4: CUT_RANGE
**Extract a specific time range (ABSOLUTE timestamps).**

**Start Fields (where to BEGIN the output):**
- `cut_start_hours`: Start hour (absolute)
- `cut_start_minutes`: Start minute (absolute)
- `cut_start_seconds`: Start second (absolute)

**End Fields (where to END the output, or None for "to end"):**
- `cut_end_hours`: End hour (absolute, None = to end)
- `cut_end_minutes`: End minute (absolute, None = to end)
- `cut_end_seconds`: End second (absolute, None = to end)

**Example 1 - Extract from 0:10 to 4:10:**
- Input: 2-hour movie
- Start: hours=0, minutes=0, seconds=10
- End: hours=0, minutes=4, seconds=10
- Output: 0:00:10 to 0:04:10 (4 minutes total)
- **This is what you tested!** ✓

**Example 2 - Extract from 10 seconds to end:**
- Input: 2-hour movie
- Start: hours=0, minutes=0, seconds=10
- End: hours=None, minutes=None, seconds=None
- Output: 0:00:10 to 2:00:00 (1:59:50 duration)

**Example 3 - Extract from 5 minutes to 1 hour 30 minutes:**
- Input: 2-hour movie
- Start: hours=0, minutes=5, seconds=0
- End: hours=1, minutes=30, seconds=0
- Output: 0:05:00 to 1:30:00 (1 hour 25 minutes total)

**Example 4 - Extract the middle hour:**
- Input: 2-hour movie
- Start: hours=0, minutes=30, seconds=0
- End: hours=1, minutes=30, seconds=0
- Output: 0:30:00 to 1:30:00 (1 hour total)

---

## Your Test Case Explained

**Your Settings:**
- Mode: CUT_RANGE
- Start: hours=0, minutes=0, seconds=10
- End: hours=0, minutes=4, seconds=10

**What Happened:**
- Input: 2-hour movie (0:00:00 to 2:00:00)
- Start at: 10 seconds (0:00:10)
- End at: 250 seconds (0:04:10)
- Output: 0:00:10 to 0:04:10 = **4 minutes**

✅ **This is correct!** The end time is an ABSOLUTE timestamp, not a duration.

---

## What You Might Have Wanted

If you wanted to **remove the first 10 seconds AND the last 4 minutes 10 seconds**, you would need to:

### Option A: Use CUT_RANGE with calculated end time
- Input: 2-hour movie = 7200 seconds
- Remove last: 4m10s = 250 seconds
- End time: 7200 - 250 = 6950 seconds = 1:55:50
- Settings:
  - Start: hours=0, minutes=0, seconds=10
  - End: hours=1, minutes=55, seconds=50
- Output: 0:00:10 to 1:55:50

### Option B: Use CUT_FIRST then process again with CUT_LAST
1. First pass: CUT_FIRST mode, remove 10 seconds
2. Second pass: CUT_LAST mode, remove 4m10s

---

## Field Reference

### For CUT_LAST and CUT_FIRST modes:
```
cut_hours:   How many HOURS to remove
cut_minutes: How many MINUTES to remove
cut_seconds: How many SECONDS to remove
Total = (hours × 3600) + (minutes × 60) + seconds
```

### For CUT_RANGE mode:
```
START (where to begin):
  cut_start_hours:   Hour number (0, 1, 2...)
  cut_start_minutes: Minute number (0-59)
  cut_start_seconds: Second number (0-59)
  Start = (hours × 3600) + (minutes × 60) + seconds

END (where to stop):
  cut_end_hours:   Hour number or None (for "to end")
  cut_end_minutes: Minute number or None
  cut_end_seconds: Second number or None
  End = (hours × 3600) + (minutes × 60) + seconds
       OR None (if all fields are None) = to end of video
```

---

## Pro Tips

1. **For simple trimming**, use CUT_LAST or CUT_FIRST
2. **For extracting a clip**, use CUT_RANGE with both start and end
3. **To remove from start and keep to end**, use CUT_FIRST
4. **To remove from end and keep from start**, use CUT_LAST
5. **Set end fields to None** in CUT_RANGE to mean "to the end of video"

---

## Common Use Cases

| Goal | Mode | Settings |
|------|------|----------|
| Remove opening credits (1m30s) | CUT_FIRST | hours=0, min=1, sec=30 |
| Remove ending credits (2m) | CUT_LAST | hours=0, min=2, sec=0 |
| Extract clip from 5:00 to 10:00 | CUT_RANGE | start: 0h 5m 0s, end: 0h 10m 0s |
| Remove first 10s, keep rest | CUT_FIRST | hours=0, min=0, sec=10 |
| Keep from 1:30 to end | CUT_RANGE | start: 0h 1m 30s, end: None |
| Extract last hour of 2h movie | CUT_RANGE | start: 1h 0m 0s, end: None |
