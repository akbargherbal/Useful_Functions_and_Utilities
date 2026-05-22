# Arabic Prosody Helpers — Quick Start Guide

> **`arabic_prosody_helpers.py`** · built on [pyarud](https://github.com/cnemri/pyarud) v0.1.10

---

## Installation

```bash
# Python 3.12+ is required
pip install pyarud
```

Place `arabic_prosody_helpers.py` anywhere on your `PYTHONPATH` and import from it directly.

---

## 1. Detect a meter

The fastest entry point. Pass a list of `(sadr, ajuz)` pairs — fully diacritized Arabic strings.

```python
from arabic_prosody_helpers import detect_meter

meter = detect_meter([
    ("أَخِي جَاوَزَ الظَّالِمُونَ الْمَدَى",
     "فَحَقَّ الْجِهَادُ وَحَقَّ الْفِدَا"),
])
print(meter)  # "mutakareb"
```

For a **single hemistich** (no second half), pass an empty string for `ajuz`:

```python
meter = detect_meter([("أَخِي جَاوَزَ الظَّالِمُونَ الْمَدَى", "")])
```

---

## 2. Analyse a full poem

`analyze_poem()` returns a rich [`PoemResult`](#data-model) with per-foot breakdowns, health labels, and diagnostics for every verse.

```python
from arabic_prosody_helpers import analyze_poem, summarize_issues

poem = analyze_poem([
    ("أَنَامُ مِلْءَ جُفُونِي عَنْ شَوَارِدِهَا",
     "وَيَسْهَرُ الْخَلْقُ جَرَّاهَا وَيَخْتَصِمُ"),
])

print(poem.meter)          # "baseet"
print(poem.meter_arabic)   # "البسيط"
print(poem.overall_score)  # 1.0
print(poem.is_metrically_sound)  # True

# Human-readable summary for each verse
for verse in poem.verses:
    print(summarize_issues(verse))
```

**Force a specific meter** when you already know it (skips auto-detection and is faster):

```python
poem = analyze_poem(verses, meter_name="baseet")
```

---

## 3. Analyse a single verse

`analyze_verse()` is a shortcut that returns one `VerseResult` directly.

```python
from arabic_prosody_helpers import analyze_verse

vr = analyze_verse(
    "كَمُلَ الجَمَالُ مِنَ البُحُورِ الكَامِلُ",
    "مُتَفَاعِلُنْ مُتَفَاعِلُنْ مُتَفَاعِلُ",
    meter_name="kamel",
)
print(vr.combined_score)       # 1.0
print(vr.sadr.is_sound)        # True
```

---

## 4. Inspect feet and identify zihāf

Every hemistich exposes a `.feet` list of `FootResult` objects. Each foot tells you:

- its **binary pattern** (`actual_segment` / `expected_pattern`)
- its **health**: `"perfect"`, `"valid_zihaf"`, `"broken"`, or `"severe"`
- the **zihāf name** applied: `"Salim"`, `"Khaban"`, `"Edmaar"`, `"Kaff"`, …

```python
from arabic_prosody_helpers import analyze_verse, get_zihaf_feet, get_broken_feet

vr = analyze_verse(
    "أَنَامُ مِلْءَ جُفُونِي عَنْ شَوَارِدِهَا",
    "وَيَسْهَرُ الْخَلْقُ جَرَّاهَا وَيَخْتَصِمُ",
    meter_name="baseet",
)

# All feet in the Ṣadr (first hemistich)
for foot in vr.sadr.feet:
    print(
        f"foot {foot.foot_index + 1} [{foot.position_label}]: "
        f"{foot.actual_segment:10s} | {foot.health:12s} | zihāf={foot.zihaf_name}"
    )
```

```
foot 1 [Hashw]: 110110     | valid_zihaf  | zihāf=Kaff
foot 2 [Hashw]: 1110       | valid_zihaf  | zihāf=Khaban
foot 3 [Hashw]: 1010110    | perfect      | zihāf=Salim
foot 4 [ʿArūḍ]: 1110       | valid_zihaf  | zihāf=Khaban
```

**Filter helpers:**

```python
# Feet with valid classical zihāf
modified = get_zihaf_feet(vr.sadr)

# Feet that are outright broken (don't match any allowed form)
broken = get_broken_feet(vr.ajuz)
```

---

## 5. Quick health checks

```python
from arabic_prosody_helpers import has_zihaf, is_broken

print(has_zihaf(vr))   # True  — at least one foot carries a valid zihāf
print(is_broken(vr))   # False — no broken / missing / extra-bits feet
```

---

## 6. Identify a zihāf from binary patterns

You can call the zihāf identifier directly — no `pyarud` needed.

```python
from arabic_prosody_helpers import identify_zihaf

print(identify_zihaf("1010110", "110110"))   # "Khaban"  (bit 1 dropped)
print(identify_zihaf("10110",   "1110"))     # "Khaban"
print(identify_zihaf("1101010", "111010"))   # "Qabadh" (bit 4 dropped)
print(identify_zihaf("11010",   "11010"))    # "Salim"  (unchanged)
```

---

## 7. Convert text to its binary prosodic pattern

```python
from arabic_prosody_helpers import get_binary_pattern

arudi, pattern = get_binary_pattern("مُسْتَفْعِلُنْ", saturate=False)
print(pattern)   # "1010110"

# Saturate the final vowel (default for interior lines)
_, pattern = get_binary_pattern("فِي الْبَيْتِ")
print(pattern)   # ends in "10" (Ashbaʿ extension applied)
```

---

## 8. Score interpretation

```python
from arabic_prosody_helpers import score_interpretation

print(score_interpretation(1.00))  # "Perfect — exact metrical match"
print(score_interpretation(0.93))  # "Excellent — minor variance, likely valid"
print(score_interpretation(0.72))  # "Good — one or two light zihāfāt present"
print(score_interpretation(0.55))  # "Fair — noticeable metrical irregularity"
print(score_interpretation(0.30))  # "Poor — significant metrical problems"
```

---

## 9. Look up meter metadata

```python
from arabic_prosody_helpers import get_meter_info

info = get_meter_info("taweel")
# {
#   "key":         "taweel",
#   "arabic_name": "الطويل",
#   "template":    "فَعُولُنْ مَفَاعِيلُنْ فَعُولُنْ مَفَاعِلُ",
#   "known":       True
# }
```

---

## 10. Analyse multiple poems in bulk

```python
from arabic_prosody_helpers import batch_analyze

results = batch_analyze([poem1_verses, poem2_verses, poem3_verses])

for r in results:
    print(r.meter, f"{r.overall_score:.2f}", r.is_metrically_sound)
```

---

## Data model

```
PoemResult
├── meter              str              e.g. "baseet"
├── meter_arabic       str              e.g. "البسيط"
├── overall_score      float            0.0 – 1.0
├── is_metrically_sound bool
├── candidate_meters   list[tuple]      top-N (meter, score) pairs
└── verses             list[VerseResult]
    ├── verse_index    int
    ├── combined_score float
    ├── issues         list[str]        plain-English diagnostics
    ├── sadr           HemistichResult
    │   ├── text       str
    │   ├── binary_pattern str
    │   ├── score      float
    │   ├── is_sound   bool
    │   ├── broken_foot_indices  list[int]
    │   ├── missing_foot_count   int
    │   ├── extra_bits           str | None
    │   └── feet       list[FootResult]
    │       ├── foot_index       int
    │       ├── position_label   "Hashw" | "ʿArūḍ" | "Ḍarb" | "Extra"
    │       ├── expected_pattern str    best matched form
    │       ├── actual_segment   str    observed bits
    │       ├── canonical_pattern str   pristine Salīm form
    │       ├── score            float
    │       ├── status           "ok" | "broken" | "missing" | "extra_bits"
    │       ├── zihaf_name       str | None
    │       └── health           "perfect" | "valid_zihaf" | "broken" | "severe"
    └── ajuz           HemistichResult | None   (None for single hemistich)
```

---

## Foot status reference

| `status` | `health` | Meaning |
|---|---|---|
| `ok` + Salīm pattern | `perfect` | Canonical form, no modification |
| `ok` + modified pattern | `valid_zihaf` | Classical zihāf or ʿilla applied |
| `broken` | `broken` | No allowed form matched at this position |
| `missing` | `severe` | Input exhausted before this foot was reached |
| `extra_bits` | `severe` | Leftover bits after all feet consumed |

---

## All 16 meters

| Key | Arabic | Canonical template |
|---|---|---|
| `taweel` | الطويل | فَعُولُنْ مَفَاعِيلُنْ فَعُولُنْ مَفَاعِلُ |
| `madeed` | المديد | فَاعِلَاتُنْ فَاعِلُنْ فَاعِلَاتُ |
| `baseet` | البسيط | مُسْتَفْعِلُنْ فَاعِلُنْ مُسْتَفْعِلُنْ فَعِلُ |
| `wafer` | الوافر | مُفَاعَلَتُنْ مُفَاعَلَتُنْ فَعُولُ |
| `kamel` | الكامل | مُتَفَاعِلُنْ مُتَفَاعِلُنْ مُتَفَاعِلُ |
| `hazaj` | الهزج | مَفَاعِيلُنْ مَفَاعِيلُ |
| `rajaz` | الرجز | مُسْتَفْعِلُنْ مُسْتَفْعِلُنْ مُسْتَفْعِلُ |
| `ramal` | الرمل | فَاعِلَاتُنْ فَاعِلَاتُنْ فَاعِلَاتُ |
| `saree` | السريع | مُسْتَفْعِلُنْ مُسْتَفْعِلُنْ فَاعِلُ |
| `munsareh` | المنسرح | مُسْتَفْعِلُنْ مَفْعُولَاتُ مُفْتَعِلُ |
| `khafeef` | الخفيف | فَاعِلَاتُنْ مُسْتَفْعِلُنْ فَاعِلَاتُ |
| `mudhare` | المضارع | مَفَاعِيلُ فَاعِلَاتُ |
| `muqtadheb` | المقتضب | مَفْعُولَاتُ مُفْتَعِلُ |
| `mujtath` | المجتث | مُسْتَفْعِلُنْ فَاعِلَاتُ |
| `mutakareb` | المتقارب | فَعُولُنْ فَعُولُنْ فَعُولُنْ فَعُولُ |
| `mutadarak` | المتدارك | فَعِلُنْ فَعِلُنْ فَعِلُنْ فَعِلُ |

---

## Known limitations

- **Diacritics are required.** Undiacritized text will produce unreliable patterns. There is no built-in auto-diacritization.
- **Zihāf naming is pattern-based.** The `_ZIHAF_MAP` covers all ~40 classical zihāfāt. Exotic compound modifications may fall back to a structural description such as `"Unknown (1 bit dropped)"`.
- **Ambiguous meters.** Single-verse input for structurally similar meters (e.g. Muqtaḍab vs Sarīʿ) may be misidentified unless `meter_name` is forced. Use multiple verses for reliable auto-detection.
- **Majzūʾ variants.** If a line is consistently `"missing"` its last feet, it is likely a truncated sub-meter (Majzūʾ / Mashtūr). Force the parent `meter_name` and count the missing feet.
