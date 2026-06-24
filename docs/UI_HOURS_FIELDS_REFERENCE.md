# UI Hours Fields - Visual Reference

This document shows exactly what you should see in the application UI for hours support.

---

## Mode: CUT_LAST or CUT_FIRST

**When Selected**: You'll see ONE row of time fields.

```
┌─────────────────────────────────────────────────────┐
│ Cut Mode: [CUT_LAST ▼]                              │
│                                                      │
│   Hours: [  0  ]  Minutes: [  5  ]  Seconds: [  0  ]│
│   ─────  ──────   ────────  ──────   ────────  ───  │
│   Label  Entry    Label     Entry    Label     Entry│
└─────────────────────────────────────────────────────┘
```

**What It Means**:
- This will remove 0 hours, 5 minutes, 0 seconds from the **end** (CUT_LAST) or **beginning** (CUT_FIRST) of the video.

**Example Usage**:
- To remove last 2 hours: Set Hours=2, Minutes=0, Seconds=0
- To remove first 1 hour 30 min: Set Hours=1, Minutes=30, Seconds=0

---

## Mode: CUT_RANGE

**When Selected**: You'll see TWO rows of time fields (Start and End).

```
┌────────────────────────────────────────────────────────────────┐
│ Cut Mode: [CUT_RANGE ▼]                                        │
│                                                                 │
│   Start: [ 0 ] h  [ 0 ] m  [ 0 ] s                            │
│   ─────  ─────────────────────────                            │
│   Label  Entry Entry Entry with labels                         │
│                                                                 │
│   End:   [   ] h  [   ] m  [   ] s                            │
│   ─────  ─────────────────────────                            │
│   Label  Entry Entry Entry (empty = to end of video)           │
└────────────────────────────────────────────────────────────────┘
```

**What It Means**:
- **Start**: The ABSOLUTE position in the video where output begins
- **End**: The ABSOLUTE position in the video where output ends (empty = to end)
- Output duration = End time - Start time

**Example Usage**:

### Extract the second hour of a 3-hour movie
```
Start: [ 1 ] h  [ 0 ] m  [ 0 ] s
End:   [ 2 ] h  [ 0 ] m  [ 0 ] s
Result: 1 hour of video (from 1:00:00 to 2:00:00)
```

### Extract from 30 minutes to 1.5 hours
```
Start: [ 0 ] h  [ 30 ] m  [ 0 ] s
End:   [ 1 ] h  [ 30 ] m  [ 0 ] s
Result: 1 hour of video (from 0:30:00 to 1:30:00)
```

### Extract from 10 seconds to the end
```
Start: [ 0 ] h  [ 0 ] m  [ 10 ] s
End:   [   ] h  [   ] m  [   ] s  (leave empty)
Result: Entire video minus first 10 seconds
```

### Your Original Test (2-hour movie)
```
Start: [ 0 ] h  [ 0 ] m  [ 10 ] s
End:   [ 0 ] h  [ 4 ] m  [ 10 ] s
Result: 4 minutes (from 0:00:10 to 0:04:10)
```

**Why Only 4 Minutes?**
Because End=4m10s means "stop at the 4 minute 10 second mark of the video", not "keep 4 minutes from the end". To extract the last 4 minutes of a 2-hour movie:
```
Start: [ 1 ] h  [ 56 ] m  [ 0 ] s
End:   [ 2 ] h  [ 0  ] m  [ 0 ] s  (or leave empty)
Result: Last 4 minutes (from 1:56:00 to 2:00:00)
```

---

## Field Details

### Hours Entry Fields
- **Width**: 60px (CUT_LAST/CUT_FIRST) or 45px (CUT_RANGE)
- **Default Value**: "0" for required fields, "" (empty) for optional End time
- **Validation**: Must be non-negative number
- **Format**: Decimal allowed (e.g., 1.5 for 1 hour 30 minutes)

### Visual Consistency
All time entry fields have:
- Same height (28px)
- Consistent spacing
- Clear labels
- Proper alignment

---

## Mode Comparison

| Mode | Purpose | Time Fields | Interpretation |
|------|---------|-------------|----------------|
| **NONE** | No trimming | None | Process entire video |
| **CUT_LAST** | Remove from end | Hours, Minutes, Seconds | Duration to remove from END |
| **CUT_FIRST** | Remove from start | Hours, Minutes, Seconds | Duration to remove from START |
| **CUT_RANGE** | Extract segment | Start (h/m/s), End (h/m/s) | ABSOLUTE timestamps in video |

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Confusing Duration vs Position in CUT_RANGE
```
WRONG: "I want the last 30 minutes"
       Start: [ 0 ] h  [ 0  ] m  [ 0 ] s
       End:   [ 0 ] h  [ 30 ] m  [ 0 ] s
Result: First 30 minutes ❌

CORRECT: "I want the last 30 minutes" (of a 2-hour movie)
         Start: [ 1 ] h  [ 30 ] m  [ 0 ] s
         End:   [ 2 ] h  [ 0  ] m  [ 0 ] s (or empty)
Result: Last 30 minutes ✅
```

### ❌ Mistake 2: End Time Before Start Time
```
WRONG: Start: [ 2 ] h  [ 0 ] m  [ 0 ] s
       End:   [ 1 ] h  [ 0 ] m  [ 0 ] s
Error: "End time must be after start time" ❌
```

### ❌ Mistake 3: Negative Values
```
WRONG: Hours: [ -1 ]
Error: "Time values cannot be negative" ❌
```

---

## Testing Checklist

When you open the app, verify:

- [ ] Hours field appears in CUT_LAST mode
- [ ] Hours field appears in CUT_FIRST mode
- [ ] Start hours field appears in CUT_RANGE mode
- [ ] End hours field appears in CUT_RANGE mode
- [ ] All fields accept numeric input
- [ ] Validation shows errors for negative values
- [ ] Validation catches end time before start time
- [ ] Processing uses hours correctly (test with a known video)

---

## Quick Reference: Common Operations

### Remove Opening Credits (2 minutes)
```
Mode: CUT_FIRST
Hours: [ 0 ]  Minutes: [ 2 ]  Seconds: [ 0 ]
```

### Remove Ending Credits (5 minutes)
```
Mode: CUT_LAST
Hours: [ 0 ]  Minutes: [ 5 ]  Seconds: [ 0 ]
```

### Extract Middle 30 Minutes (from 15min to 45min)
```
Mode: CUT_RANGE
Start: [ 0 ] h  [ 15 ] m  [ 0 ] s
End:   [ 0 ] h  [ 45 ] m  [ 0 ] s
```

### Keep Only First Hour
```
Mode: CUT_RANGE
Start: [ 0 ] h  [ 0 ] m  [ 0 ] s
End:   [ 1 ] h  [ 0 ] m  [ 0 ] s
```

### Remove First 2 Hours, Keep Rest
```
Mode: CUT_FIRST
Hours: [ 2 ]  Minutes: [ 0 ]  Seconds: [ 0 ]
```

---

**Ready to Test!** 🎉

Open your application and you should now see all the hours fields as described above.
