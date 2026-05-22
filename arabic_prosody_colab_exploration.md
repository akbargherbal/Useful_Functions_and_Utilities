# Arabic Prosody Verification — Google Colab Exploration
## خطوة بخطوة: اختبار مكتبات التحقق العروضي

> **How to use this file:**  
> Each `### Cell N` heading is one Colab cell. Copy the code block beneath it into a new cell.  
> Run cells top to bottom — later cells depend on earlier ones.  
> Observations/questions to answer are marked **🔍 Observe**.

---

## PART 0 — Environment Setup

---

### Cell 0-A — Install all three libraries

```python
# Run this first. Restart runtime after if Colab prompts you.
!pip install pyarabic aruudy pyarud --quiet
```

> **Note on versions:** PyArud officially targets Python 3.12+.  
> Colab currently ships Python 3.10/3.11. If the install fails or you get import errors,  
> jump to **Cell 0-B** for the workaround.

---

### Cell 0-B — (Fallback) Check Python version and handle PyArud unavailability

```python
import sys
print("Python version:", sys.version)

# Attempt imports and record what's available
PYARABIC_OK = False
ARUUDY_OK   = False
PYARUD_OK   = False

try:
    import pyarabic.araby as araby
    PYARABIC_OK = True
    print("✅ pyarabic — imported successfully")
except ImportError as e:
    print(f"❌ pyarabic — {e}")

try:
    import aruudy.poetry.arm as arm
    ARUUDY_OK = True
    print("✅ aruudy — imported successfully")
except ImportError as e:
    print(f"❌ aruudy — {e}")

try:
    import pyarud
    PYARUD_OK = True
    print("✅ pyarud — imported successfully")
except ImportError as e:
    print(f"❌ pyarud — {e}")
    print("   → PyArud may need Python 3.12. See Cell 0-C.")
```

> **🔍 Observe:** Which of the three imports succeed in Colab's current runtime?  
> Record this — it determines which sections below are live vs read-only.

---

### Cell 0-C — (If PyArud fails) Run it via a Python 3.12 subprocess

```python
# If pyarud failed above, this cell installs Python 3.12 in the Colab environment
# and wraps pyarud calls through it. Skip if pyarud imported fine.

if not PYARUD_OK:
    print("Attempting Python 3.12 installation for pyarud...")
    !sudo apt-get install -y python3.12 python3.12-venv --quiet
    !python3.12 -m ensurepip --quiet
    !python3.12 -m pip install pyarud --quiet
    
    # Verify
    result = !python3.12 -c "import pyarud; print('pyarud version:', pyarud.__version__)"
    print(result)
    
    if "pyarud version" in str(result):
        PYARUD_OK = True
        PYARUD_VIA_SUBPROCESS = True
        print("✅ pyarud available via python3.12 subprocess")
    else:
        PYARUD_VIA_SUBPROCESS = False
        print("❌ pyarud unavailable — Cells 4-x will be read-only reference")
else:
    PYARUD_VIA_SUBPROCESS = False
```

---

### Cell 0-D — Test verses to use throughout

```python
# These are the reference verses we'll scan in every cell.
# All are fully diacritized (شكل كامل).
# Format: (text, meter_name, expected_result)

TEST_VERSES = [
    # ✅ Correct: البسيط — مستفعلن فاعلن مستفعلن فاعلن
    (
        "إِنَّ الصَّوْتَ بِغَيْرِ قَاعِدَةٍ خَاوِي",
        "البسيط",
        "should_pass"
    ),
    # ✅ Correct: الطويل — فعولن مفاعيلن فعولن مفاعيلن
    (
        "أَلَا لَيْتَ شِعْرِي هَلْ أَبِيتَنَّ لَيْلَةً",
        "الطويل",
        "should_pass"
    ),
    # ❌ Broken: deliberate extra syllable
    (
        "إِنَّ الصَّوْتَ الجَمِيلَ بِغَيْرِ قَاعِدَةٍ خَاوِي",
        "البسيط",
        "should_fail"
    ),
    # ✅ Correct: الكامل (classic example)
    (
        "كَرَمَ الزَّمَانُ عَلَى الكِرَامِ فَأَكْرَمَا",
        "الكامل",
        "should_pass"
    ),
    # ✅ Correct with زحاف (القبض) on الطويل
    (
        "أَلَا لَيْتَ شِعْرِي هَلْ أَبِيتَنَّ لَيْلَةً",
        "الطويل",
        "should_pass"
    ),
]

print(f"Loaded {len(TEST_VERSES)} test verses.")
for i, (text, meter, expected) in enumerate(TEST_VERSES):
    icon = "✅" if expected == "should_pass" else "❌"
    print(f"  [{i}] {icon} {meter}: {text[:40]}...")
```

> **Why these verses?**  
> We need at least one that should pass, one that should fail, and one that uses  
> a permitted زحاف — so we can see how each library handles each case.  
> Add your own verses from the LLM output here as you go.

---

---

## PART 1 — PyArabic: Normalization Layer

> **Purpose:** Clean the LLM's text before any prosodic scanning.  
> The LLM occasionally emits tatweel (ـ) as a typographic spacer, inconsistent  
> hamza forms, or trailing whitespace. These cause false failures downstream.

---

### Cell 1-A — Explore available functions

```python
import pyarabic.araby as araby
import inspect

# Print all public functions in pyarabic.araby
funcs = [name for name, obj in inspect.getmembers(araby) if callable(obj) and not name.startswith("_")]
print("Functions in pyarabic.araby:\n")
for f in funcs:
    print(f"  {f}")
```

> **🔍 Observe:** Scan the list for anything prosody-related beyond what the feasibility  
> study mentioned. Functions like `vocalisation_to_pattern` or `tokenize` could be useful.

---

### Cell 1-B — Core normalization: what each function does to our text

```python
import pyarabic.araby as araby

# Inject a "dirty" version of one of our test verses to see what gets cleaned
dirty_verse = "إِنَّ الصَّـوْتَ بِغَيْرِ قَاعِدَةٍ خَاوِي"
#                        ↑ tatweel injected here

print("Original (dirty):", dirty_verse)
print()

# 1. Strip tatweel (ـ) — the elongation character used as filler
no_tatweel = araby.strip_tatweel(dirty_verse)
print("strip_tatweel():  ", no_tatweel)

# 2. Strip all tashkeel (diacritics) — useful to see the bare consonantal skeleton
no_diacritics = araby.strip_tashkeel(dirty_verse)
print("strip_tashkeel(): ", no_diacritics)

# 3. Strip only shadda — keep vowels but remove shadda marks
no_shadda = araby.strip_shadda(dirty_verse)
print("strip_shadda():   ", no_shadda)

# 4. Normalize hamza — unify أ / إ / آ / ا forms
normalized_hamza = araby.normalize_hamza(dirty_verse)
print("normalize_hamza():", normalized_hamza)

# 5. Normalize alef with madda (آ → ا + maddah handling)
normalized_alef = araby.normalize_spellingstandard(dirty_verse)
print("normalize_std():  ", normalized_alef)
```

> **🔍 Observe:**  
> - Does `strip_tatweel` correctly remove the ـ without touching the surrounding letters?  
> - Does `normalize_hamza` change anything in your actual LLM output verses?  
>   Paste a real LLM-generated hemistich here to find out.

---

### Cell 1-C — Build and test the normalization pipeline function

```python
import pyarabic.araby as araby
import unicodedata

def normalize_for_scanning(text: str) -> str:
    """
    Normalize a fully-diacritized Arabic hemistich before prosodic scanning.
    
    Steps (in order — sequence matters):
      1. Unicode NFC normalization (resolve composed vs decomposed forms)
      2. Strip tatweel (typographic spacer that inflates syllable counts)
      3. Normalize hamza variants (أ إ آ → canonical forms)
      4. Strip zero-width characters that LLMs occasionally emit
      5. Collapse multiple spaces → single space, strip edges
    
    Does NOT strip tashkeel — we need it for scansion.
    """
    # Step 1: Unicode NFC
    text = unicodedata.normalize("NFC", text)
    
    # Step 2: Remove tatweel
    text = araby.strip_tatweel(text)
    
    # Step 3: Normalize hamza
    text = araby.normalize_hamza(text)
    
    # Step 4: Remove zero-width characters (ZWJ, ZWNJ, etc.)
    ZERO_WIDTH = ["\u200c", "\u200d", "\u200e", "\u200f", "\ufeff"]
    for char in ZERO_WIDTH:
        text = text.replace(char, "")
    
    # Step 5: Normalize whitespace
    text = " ".join(text.split())
    
    return text


# Run on all test verses and check for changes
print("Normalization results:\n")
for i, (text, meter, expected) in enumerate(TEST_VERSES):
    cleaned = normalize_for_scanning(text)
    changed = "⚠️ CHANGED" if cleaned != text else "— unchanged"
    print(f"[{i}] {changed}")
    if cleaned != text:
        print(f"     Before: {text}")
        print(f"     After:  {cleaned}")
```

> **🔍 Observe:**  
> - Do any of your test verses change after normalization?  
> - If not, paste a verse that has a tatweel in it and confirm it gets stripped.  
> - Any unexpected changes? That's a bug to fix before moving to scansion.

---

### Cell 1-D — Inspect syllabic structure using PyArabic

```python
import pyarabic.araby as araby

# PyArabic can separate a text into its vocalisation (tashkeel) and base letters.
# This is not scansion, but it lets us SEE the phonological structure.

verse = normalize_for_scanning(TEST_VERSES[0][0])
print("Verse:", verse)
print()

# Separate the vocalisation (returns tuple: letters, vocalisation)
try:
    letters, vocalisation = araby.separate_tashkeel(verse)
    print("Consonants only: ", letters)
    print("Vocalisation:    ", vocalisation)
    print("Length (consonants):", len([c for c in letters if araby.is_arabicrange(c)]))
except Exception as e:
    print(f"separate_tashkeel not available or error: {e}")
    # Some versions expose this differently:
    letters = araby.strip_tashkeel(verse)
    print("Consonants only (fallback):", letters)

# Count harakat (short vowels) — proxy for syllable count
harakat = [c for c in verse if c in araby.HARAKAT]
print(f"\nḤarakat count: {len(harakat)}")
print("Harakat characters:", harakat)
```

> **🔍 Observe:**  
> - Is the harakat count per hemistich consistent across verses of the same meter?  
>   For البسيط a full hemistich has ~8 syllable positions.  
> - This is the raw material a custom syllable counter would work from.

---

---

## PART 2 — Aruudy: Fast Gate (Meter Detection)

> **Purpose:** Quick pass/fail — does this hemistich match *any* known meter?  
> If not, skip PyArud entirely. Also provides الكتابة العروضية  
> (prosodic transcription), which is useful for debugging and logging.

---

### Cell 2-A — Explore the Aruudy API from source

```python
import aruudy
import aruudy.poetry.arm as arm
import inspect

# Top-level package
print("=== aruudy package members ===")
print(dir(aruudy))
print()

# arm module (Arabic meter recognition)
print("=== aruudy.poetry.arm members ===")
members = [m for m in dir(arm) if not m.startswith("_")]
for m in members:
    obj = getattr(arm, m)
    if callable(obj):
        try:
            sig = str(inspect.signature(obj))
        except (ValueError, TypeError):
            sig = "(...)"
        print(f"  {m}{sig}")
    else:
        print(f"  {m}  [attr: {type(obj).__name__}]")
```

> **🔍 Observe:**  
> - What is the main function name for meter detection? Likely `get_ameter`, `analyze`, or similar.  
> - Note the exact parameter names — the next cell uses them.  
>   **Fill in Cell 2-B based on what you find here.**

---

### Cell 2-B — Basic meter detection on test verses

```python
import aruudy.poetry.arm as arm

# ─────────────────────────────────────────────────────────────────────────────
# IMPORTANT: The exact function name depends on what Cell 2-A showed.
# Common patterns in Aruudy versions:
#   arm.get_ameter(text)
#   arm.process(text)
#   arm.analyze_verse(text)
# Replace DETECT_FUNC below with what Cell 2-A revealed.
# ─────────────────────────────────────────────────────────────────────────────

def detect_meter_aruudy(hemistich: str):
    """
    Attempt meter detection via Aruudy.
    Returns the raw result object — we'll inspect its structure next.
    """
    # Try the most common API patterns in order:
    for func_name in ["get_ameter", "process", "analyze_verse", "analyze"]:
        func = getattr(arm, func_name, None)
        if func:
            try:
                return func_name, func(hemistich)
            except Exception as e:
                print(f"  {func_name}() raised: {e}")
    return None, None


print("Testing Aruudy meter detection:\n")
for text, meter, expected in TEST_VERSES[:3]:
    cleaned = normalize_for_scanning(text)
    func_name, result = detect_meter_aruudy(cleaned)
    print(f"Verse:     {cleaned[:50]}...")
    print(f"Expected:  {meter} ({expected})")
    print(f"Function:  {func_name}()")
    print(f"Raw result type: {type(result)}")
    print(f"Raw result:      {result}")
    print("-" * 60)
```

> **🔍 Observe:**  
> - What does the raw result object look like? Is it a dict, a named object, a string?  
> - Does it return the meter name in Arabic? Does it match our declared meter names?  
>   (e.g. does it say "البسيط" exactly, or "baseet", or something else?)

---

### Cell 2-C — Inspect the result object structure

```python
# After Cell 2-B reveals the result type, dig into it here.

sample_text = normalize_for_scanning(TEST_VERSES[0][0])  # البسيط example
func_name, result = detect_meter_aruudy(sample_text)

if result is not None:
    print("Result type:", type(result))
    print()
    
    # If it's an object, show all its attributes
    attrs = [a for a in dir(result) if not a.startswith("_")]
    print("Attributes / methods:")
    for attr in attrs:
        val = getattr(result, attr, "N/A")
        if not callable(val):
            print(f"  .{attr} = {val!r}")
    
    # If it's a dict
    if isinstance(result, dict):
        print("Dict keys and values:")
        for k, v in result.items():
            print(f"  [{k!r}] = {v!r}")
    
    # If it's a string
    if isinstance(result, str):
        print("String result:", result)
else:
    print("No result — check Cell 2-A for correct function name.")
```

> **🔍 Observe:**  
> - Which attribute holds the meter name?  
> - Which attribute (if any) holds الكتابة العروضية (prosodic transcription)?  
> - Is there a confidence score, or is detection binary?

---

### Cell 2-D — Extract prosodic transcription (الكتابة العروضية)

```python
# الكتابة العروضية is the phonological rewrite of the text used in classical scansion.
# E.g.: "الصَّوْت" → "اصْصَوْت" (ال الشمسية assimilated)
#        "هَذَا" → "هَاذَا" (alef elision handled)

# Fill in PROSODIC_ATTR with the attribute name found in Cell 2-C
PROSODIC_ATTR = "prosody"       # ← change this to actual attribute name
METER_ATTR    = "meter"         # ← change this to actual attribute name

print("Prosodic transcriptions:\n")
for text, declared_meter, expected in TEST_VERSES:
    cleaned = normalize_for_scanning(text)
    _, result = detect_meter_aruudy(cleaned)
    
    if result is None:
        print(f"  SKIP (no result): {text[:40]}...")
        continue
    
    # Extract meter and prosodic writing (adjust attribute names as needed)
    detected_meter = getattr(result, METER_ATTR, None) \
                  or (result.get(METER_ATTR) if isinstance(result, dict) else "?")
    prosodic_text  = getattr(result, PROSODIC_ATTR, None) \
                  or (result.get(PROSODIC_ATTR) if isinstance(result, dict) else "?")
    
    match = "✅" if str(detected_meter) == declared_meter else "❌"
    icon  = "✅" if expected == "should_pass" else "❌"
    
    print(f"Original:    {text}")
    print(f"Prosodic:    {prosodic_text}")
    print(f"Detected:    {detected_meter}  {match} (expected: {declared_meter})")
    print(f"Verdict:     {icon} ({expected})")
    print("-" * 60)
```

> **🔍 Observe:**  
> - For the deliberately broken verse (`TEST_VERSES[2]`), does Aruudy return `None` / no meter, or does it return a wrong meter?  
>   Either behaviour is acceptable for a fast gate — as long as it does NOT return البسيط for the broken verse.  
> - Does the prosodic transcription look correct? Spot-check the assimilation rules.

---

### Cell 2-E — Build the Aruudy fast-gate function

```python
# ─────────────────────────────────────────────────────────────────────────────
# Fill in these two constants based on your Cell 2-C findings:
METER_ATTR    = "meter"      # attribute/key that holds the meter name
PROSODIC_ATTR = "prosody"    # attribute/key that holds الكتابة العروضية
# ─────────────────────────────────────────────────────────────────────────────

def fast_gate_aruudy(hemistich: str, declared_meter: str) -> dict:
    """
    Stage 1 verification: does this hemistich match any known meter?
    
    Returns a dict:
      pass         (bool)   — True if a meter was detected
      meter_match  (bool)   — True if detected meter == declared meter
      detected     (str)    — meter name Aruudy found (or None)
      prosodic     (str)    — الكتابة العروضية (or None)
      raw          (object) — raw Aruudy result for debugging
    """
    cleaned = normalize_for_scanning(hemistich)
    _, result = detect_meter_aruudy(cleaned)
    
    if result is None:
        return {
            "pass": False,
            "meter_match": False,
            "detected": None,
            "prosodic": None,
            "raw": None,
            "reason": "no_meter_detected",
        }
    
    detected = getattr(result, METER_ATTR, None) \
             or (result.get(METER_ATTR) if isinstance(result, dict) else None)
    prosodic = getattr(result, PROSODIC_ATTR, None) \
             or (result.get(PROSODIC_ATTR) if isinstance(result, dict) else None)
    
    # Normalize meter name comparison (strip whitespace, normalize Arabic)
    def norm(s):
        return s.strip() if s else ""
    
    meter_match = norm(str(detected)) == norm(declared_meter)
    
    return {
        "pass": detected is not None,
        "meter_match": meter_match,
        "detected": detected,
        "prosodic": prosodic,
        "raw": result,
        "reason": "ok" if meter_match else ("wrong_meter" if detected else "no_meter"),
    }


# Test
print("Fast gate results:\n")
for text, meter, expected in TEST_VERSES:
    result = fast_gate_aruudy(text, meter)
    icon = "✅" if result["pass"] and result["meter_match"] else "❌"
    print(f"{icon} [{expected}]")
    print(f"   Verse:    {text[:50]}...")
    print(f"   Pass:     {result['pass']}  |  Meter match: {result['meter_match']}")
    print(f"   Detected: {result['detected']}  (declared: {meter})")
    print(f"   Reason:   {result['reason']}")
    print()
```

> **🔍 Observe:**  
> - Does the deliberately broken verse correctly get `pass=False` or `meter_match=False`?  
> - Does the زحاف verse (permitted deviation) still pass? It should.  
> - Are meter names returned in Arabic exactly matching our declared names?  
>   If not, you'll need a translation dict (`{"baseet": "البسيط", ...}`).

---

---

## PART 3 — PyArud: Deep Scan (Foot-by-Foot)

> **Purpose:** Confirm meter, identify the specific foot that fails,  
> and cross-check the zihāf against the closed allowlist from the system prompt.  
> This is the engine that generates structured violation reports.

---

### Cell 3-A — Explore the PyArud API

```python
# Only run this if PYARUD_OK is True.
# If PyArud runs via subprocess (PYARUD_VIA_SUBPROCESS), skip to Cell 3-F.

if PYARUD_OK and not PYARUD_VIA_SUBPROCESS:
    import pyarud
    import inspect
    
    print("pyarud version:", getattr(pyarud, "__version__", "unknown"))
    print()
    print("Top-level members:")
    for name in dir(pyarud):
        if not name.startswith("_"):
            obj = getattr(pyarud, name)
            kind = "fn" if callable(obj) else "mod" if hasattr(obj, "__module__") else "attr"
            print(f"  [{kind}] {name}")
else:
    print("PyArud not available in this runtime — read Cell 3-F for subprocess approach.")
```

---

### Cell 3-B — Basic PyArud analysis on a single verse

```python
if PYARUD_OK and not PYARUD_VIA_SUBPROCESS:
    import pyarud
    
    # ─────────────────────────────────────────────────────────────────────────
    # The exact API must be confirmed from Cell 3-A.
    # Common patterns based on the library's source:
    #   pyarud.analyze(text)
    #   pyarud.scan(text)
    #   pyarud.check_bayt(hemistich1, hemistich2)
    # We try hemistich-level analysis first since that matches our pipeline unit.
    # ─────────────────────────────────────────────────────────────────────────
    
    sample = normalize_for_scanning(TEST_VERSES[0][0])
    print("Input hemistich:", sample)
    print()
    
    # Try candidate function names
    for func_name in ["analyze", "scan", "check", "check_hemistich", "analyze_hemistich"]:
        func = getattr(pyarud, func_name, None)
        if func:
            print(f"Trying pyarud.{func_name}()...")
            try:
                result = func(sample)
                print(f"  Result type: {type(result)}")
                print(f"  Result:      {result}")
                break
            except Exception as e:
                print(f"  Error: {e}")
else:
    print("Skipped — PyArud not available.")
```

> **🔍 Observe:**  
> - Which function name works?  
> - What does the result look like? Does it have a `.feet` or `.tafaeel` list?  
> - What are the status codes it returns? Are they strings (`"ok"`, `"broken"`) or numbers?

---

### Cell 3-C — Inspect a foot object

```python
if PYARUD_OK and not PYARUD_VIA_SUBPROCESS:
    # After Cell 3-B reveals the working function, inspect one result fully.
    
    SCAN_FUNC = "analyze"   # ← fill in from Cell 3-B
    
    sample = normalize_for_scanning(TEST_VERSES[0][0])
    func   = getattr(pyarud, SCAN_FUNC)
    result = func(sample)
    
    print("Full result object:")
    print(repr(result))
    print()
    
    # If there's a feet/tafaeel list:
    feet_attr = None
    for candidate in ["feet", "tafaeel", "tafeel", "parts", "units"]:
        if hasattr(result, candidate):
            feet_attr = candidate
            break
    
    if feet_attr:
        feet = getattr(result, feet_attr)
        print(f"Feet list ({feet_attr}), length: {len(feet)}")
        for i, foot in enumerate(feet):
            print(f"\n  Foot {i+1}:")
            for attr in dir(foot):
                if not attr.startswith("_"):
                    val = getattr(foot, attr, "N/A")
                    if not callable(val):
                        print(f"    .{attr} = {val!r}")
    else:
        print("No feet attribute found — result may be a flat structure.")
        print("Attributes:", [a for a in dir(result) if not a.startswith("_")])
else:
    print("Skipped.")
```

> **🔍 Observe:**  
> - What attributes does a foot object have?  
>   We need: sequence number, name (اسم التفعيلة), status (ok/broken/...), zihāf name.  
> - Are zihāf names in Arabic or Latin transliteration?  
>   This affects how we write the allowlist in Cell 3-E.

---

### Cell 3-D — Run on the broken verse: confirm it detects the failure

```python
if PYARUD_OK and not PYARUD_VIA_SUBPROCESS:
    SCAN_FUNC  = "analyze"   # ← from Cell 3-B
    FEET_ATTR  = "feet"      # ← from Cell 3-C
    STATUS_ATTR = "status"   # ← from Cell 3-C
    ZIHAF_ATTR  = "zihaf"    # ← from Cell 3-C
    NAME_ATTR   = "name"     # ← foot name attribute from Cell 3-C
    
    print("Scanning all test verses:\n")
    func = getattr(pyarud, SCAN_FUNC)
    
    for text, meter, expected in TEST_VERSES:
        cleaned = normalize_for_scanning(text)
        try:
            result = func(cleaned)
            feet   = getattr(result, FEET_ATTR, [])
            
            broken_feet = [
                f for f in feet
                if getattr(f, STATUS_ATTR, "ok") != "ok"
            ]
            
            verdict = "✅ PASS" if not broken_feet else "❌ FAIL"
            print(f"{verdict}  (expected: {expected})")
            print(f"  Verse:  {text[:50]}...")
            print(f"  Meter:  {meter}")
            
            if broken_feet:
                for foot in broken_feet:
                    status = getattr(foot, STATUS_ATTR, "?")
                    name   = getattr(foot, NAME_ATTR, "?")
                    zihaf  = getattr(foot, ZIHAF_ATTR, None)
                    print(f"  → Foot '{name}': status={status}, zihaf={zihaf}")
            print()
        
        except Exception as e:
            print(f"ERROR on verse: {e}")
            print()
else:
    print("Skipped.")
```

> **🔍 Observe:**  
> - Does the broken verse correctly fail?  
> - Does PyArud give a specific foot number/name for the failure? This is what makes it  
>   valuable — the violation report can tell the LLM exactly which foot to fix.  
> - Does the زحاف verse pass? If PyArud marks it as `ok` with a zihāf note, what is the zihāf name?

---

### Cell 3-E — Build the zihāf allowlist and the deep-scan function

```python
# ─────────────────────────────────────────────────────────────────────────────
# These allowlists are transcribed DIRECTLY from the system prompt's tables.
# The keys must match whatever meter names PyArud/Aruudy return.
# The values must match whatever zihāf names PyArud returns.
# Adjust the string values after running Cell 3-C.
# ─────────────────────────────────────────────────────────────────────────────

PERMITTED_ZIHAFAT = {
    "الطويل":    {"القبض"},
    "البسيط":    {"الخبن", "الطي"},
    "الكامل":    {"الإضمار", "الوقص"},
    "الرجز":     {"الخبن"},
    "المتقارب":  {"القبض"},
    "الوافر":    {"العقل"},
    "الخفيف":    {"الخبن", "الكف"},
    "السريع":    {"الطي", "الخبن"},
}


def deep_scan_pyarud(hemistich: str, declared_meter: str) -> dict:
    """
    Stage 2 verification: foot-by-foot prosodic analysis.
    
    Checks:
      (a) Is the hemistich metrically parseable?
      (b) Does the detected meter match the declared meter?
      (c) Are all zihāfāt within the closed allowlist for this meter?
    
    Returns a dict with:
      pass        (bool)
      violations  (list of dicts: foot_seq, foot_name, status, zihaf, reason)
      detected_meter (str)
      meter_match    (bool)
    """
    if not PYARUD_OK or PYARUD_VIA_SUBPROCESS:
        return {"pass": None, "reason": "pyarud_unavailable"}
    
    # ── Fill in from Cell 3-B/C ───────────────────────────────────────────────
    SCAN_FUNC   = "analyze"   # ← function name
    FEET_ATTR   = "feet"      # ← attribute holding list of feet
    STATUS_ATTR = "status"    # ← foot attribute: "ok" / "broken" / "missing" / "extra_bits"
    ZIHAF_ATTR  = "zihaf"     # ← foot attribute: zihāf name or None
    NAME_ATTR   = "name"      # ← foot attribute: tafʿīla name
    SEQ_ATTR    = "seq"       # ← foot attribute: position index
    METER_ATTR  = "meter"     # ← result attribute: detected meter name
    # ─────────────────────────────────────────────────────────────────────────
    
    cleaned     = normalize_for_scanning(hemistich)
    func        = getattr(pyarud, SCAN_FUNC)
    allowed_z   = PERMITTED_ZIHAFAT.get(declared_meter, set())
    
    try:
        result = func(cleaned)
    except Exception as e:
        return {"pass": False, "reason": f"scan_error:{e}", "violations": []}
    
    detected_meter = getattr(result, METER_ATTR, None)
    meter_match    = str(detected_meter).strip() == declared_meter.strip()
    feet           = getattr(result, FEET_ATTR, [])
    
    violations = []
    
    for foot in feet:
        status = getattr(foot, STATUS_ATTR, "ok")
        zihaf  = getattr(foot, ZIHAF_ATTR, None)
        name   = getattr(foot, NAME_ATTR, "?")
        seq    = getattr(foot, SEQ_ATTR, "?")
        
        if status in ("broken", "missing", "extra_bits"):
            violations.append({
                "foot_seq":  seq,
                "foot_name": name,
                "status":    status,
                "zihaf":     zihaf,
                "reason":    f"status_{status}",
            })
        elif zihaf and zihaf not in allowed_z:
            # PyArud accepted it classically, but it's outside our closed allowlist
            violations.append({
                "foot_seq":  seq,
                "foot_name": name,
                "status":    "unlisted_zihaf",
                "zihaf":     zihaf,
                "reason":    f"unlisted_zihaf:{zihaf}",
            })
    
    if not meter_match:
        violations.insert(0, {
            "foot_seq":  0,
            "foot_name": "—",
            "status":    "wrong_meter",
            "zihaf":     None,
            "reason":    f"detected:{detected_meter}",
        })
    
    return {
        "pass":           len(violations) == 0,
        "violations":     violations,
        "detected_meter": detected_meter,
        "meter_match":    meter_match,
        "foot_count":     len(feet),
    }


# Quick test
if PYARUD_OK and not PYARUD_VIA_SUBPROCESS:
    print("Deep scan results:\n")
    for text, meter, expected in TEST_VERSES:
        r = deep_scan_pyarud(text, meter)
        icon = "✅" if r["pass"] else "❌"
        print(f"{icon} [{expected}] {meter}")
        print(f"  {text[:55]}...")
        if not r["pass"]:
            for v in r["violations"]:
                print(f"  → foot {v['foot_seq']} ({v['foot_name']}): {v['reason']}")
        print()
else:
    print("PyArud not available — deep_scan_pyarud() defined but will return 'unavailable'.")
```

---

### Cell 3-F — Subprocess wrapper (if PyArud runs via python3.12 only)

```python
# Use this if PYARUD_VIA_SUBPROCESS is True.
# We write a small helper script and call it with python3.12.

import subprocess
import json
import tempfile
import os

PYARUD_HELPER_SCRIPT = """
import sys
import json
import pyarud

text           = sys.argv[1]
declared_meter = sys.argv[2]

PERMITTED_ZIHAFAT = {
    "الطويل":   ["القبض"],
    "البسيط":   ["الخبن", "الطي"],
    "الكامل":   ["الإضمار", "الوقص"],
    "الرجز":    ["الخبن"],
    "المتقارب": ["القبض"],
    "الوافر":   ["العقل"],
    "الخفيف":   ["الخبن", "الكف"],
    "السريع":   ["الطي", "الخبن"],
}

# ── adjust attribute names based on your Cell 3-B/C findings ─────────────
SCAN_FUNC   = "analyze"
FEET_ATTR   = "feet"
STATUS_ATTR = "status"
ZIHAF_ATTR  = "zihaf"
NAME_ATTR   = "name"
SEQ_ATTR    = "seq"
METER_ATTR  = "meter"
# ─────────────────────────────────────────────────────────────────────────

func      = getattr(pyarud, SCAN_FUNC)
result    = func(text)
detected  = str(getattr(result, METER_ATTR, ""))
feet      = getattr(result, FEET_ATTR, [])
allowed_z = PERMITTED_ZIHAFAT.get(declared_meter, [])

violations = []
for foot in feet:
    status = getattr(foot, STATUS_ATTR, "ok")
    zihaf  = getattr(foot, ZIHAF_ATTR, None)
    name   = getattr(foot, NAME_ATTR, "?")
    seq    = getattr(foot, SEQ_ATTR, 0)
    if status in ("broken", "missing", "extra_bits"):
        violations.append({"foot_seq": seq, "foot_name": name,
                            "status": status, "zihaf": zihaf,
                            "reason": f"status_{status}"})
    elif zihaf and zihaf not in allowed_z:
        violations.append({"foot_seq": seq, "foot_name": name,
                            "status": "unlisted_zihaf", "zihaf": zihaf,
                            "reason": f"unlisted_zihaf:{zihaf}"})

meter_match = detected.strip() == declared_meter.strip()
if not meter_match:
    violations.insert(0, {"foot_seq": 0, "foot_name": "—",
                           "status": "wrong_meter", "zihaf": None,
                           "reason": f"detected:{detected}"})

print(json.dumps({
    "pass": len(violations) == 0,
    "violations": violations,
    "detected_meter": detected,
    "meter_match": meter_match,
    "foot_count": len(feet),
}))
"""

# Write helper script to a temp file
helper_path = "/tmp/pyarud_helper.py"
with open(helper_path, "w", encoding="utf-8") as f:
    f.write(PYARUD_HELPER_SCRIPT)

def deep_scan_pyarud_subprocess(hemistich: str, declared_meter: str) -> dict:
    """PyArud via python3.12 subprocess — use when PYARUD_VIA_SUBPROCESS is True."""
    if not PYARUD_VIA_SUBPROCESS:
        return deep_scan_pyarud(hemistich, declared_meter)   # use direct import
    
    cleaned = normalize_for_scanning(hemistich)
    try:
        proc = subprocess.run(
            ["python3.12", helper_path, cleaned, declared_meter],
            capture_output=True, text=True, timeout=10
        )
        if proc.returncode != 0:
            return {"pass": False, "reason": f"subprocess_error:{proc.stderr[:200]}",
                    "violations": []}
        return json.loads(proc.stdout)
    except Exception as e:
        return {"pass": False, "reason": f"exception:{e}", "violations": []}


# Test
print("Subprocess scan results:\n")
for text, meter, expected in TEST_VERSES:
    r = deep_scan_pyarud_subprocess(text, meter)
    icon = "✅" if r.get("pass") else "❌"
    print(f"{icon} [{expected}] {meter}: {text[:45]}...")
    if not r.get("pass"):
        for v in r.get("violations", []):
            print(f"   → {v.get('reason', '?')}")
    print()
```

> **🔍 Observe:**  
> - Does the subprocess approach add noticeable latency? (Run `%%time` at the top of the cell.)  
> - If latency is an issue, a persistent subprocess with stdin/stdout communication  
>   can replace the per-call approach — but only optimize if needed.

---

---

## PART 4 — Full Pipeline Integration

---

### Cell 4-A — Unified verification function

```python
def verify_hemistich(
    text: str,
    declared_meter: str,
    use_fast_gate: bool = True,
) -> dict:
    """
    Full two-stage prosodic verification.
    
    Stage 1 (Aruudy fast gate):  Does any meter match at all?
    Stage 2 (PyArud deep scan):  Foot-level check + closed zihāf validation.
    
    Returns:
      pass          (bool)   — True only if both stages pass
      stage         (str)    — which stage produced the verdict
      fast_gate     (dict)   — Stage 1 result
      deep_scan     (dict)   — Stage 2 result (None if fast gate failed)
      violations    (list)   — merged violation list for LLM re-compose payload
      hemistich     (str)    — the (normalized) input
      declared_meter(str)
    """
    normalized = normalize_for_scanning(text)
    
    fast_result = None
    deep_result = None
    
    # ── Stage 1: Aruudy fast gate ─────────────────────────────────────────────
    if use_fast_gate and ARUUDY_OK:
        fast_result = fast_gate_aruudy(normalized, declared_meter)
        if not fast_result["pass"]:
            return {
                "pass":           False,
                "stage":          "fast_gate",
                "fast_gate":      fast_result,
                "deep_scan":      None,
                "violations":     [{"reason": fast_result["reason"]}],
                "hemistich":      normalized,
                "declared_meter": declared_meter,
            }
    
    # ── Stage 2: PyArud deep scan ─────────────────────────────────────────────
    if PYARUD_OK:
        scan_func   = deep_scan_pyarud_subprocess if PYARUD_VIA_SUBPROCESS else deep_scan_pyarud
        deep_result = scan_func(normalized, declared_meter)
    else:
        # PyArud unavailable — rely on fast gate only
        if fast_result:
            return {
                "pass":           fast_result["pass"] and fast_result["meter_match"],
                "stage":          "fast_gate_only",
                "fast_gate":      fast_result,
                "deep_scan":      None,
                "violations":     [] if (fast_result["pass"] and fast_result["meter_match"]) else [{"reason": "fast_gate_fail"}],
                "hemistich":      normalized,
                "declared_meter": declared_meter,
            }
        return {"pass": None, "stage": "no_scanner", "violations": [],
                "hemistich": normalized, "declared_meter": declared_meter}
    
    return {
        "pass":           deep_result.get("pass", False),
        "stage":          "deep_scan",
        "fast_gate":      fast_result,
        "deep_scan":      deep_result,
        "violations":     deep_result.get("violations", []),
        "hemistich":      normalized,
        "declared_meter": declared_meter,
    }


# ── Run on all test verses ────────────────────────────────────────────────────
print("Full pipeline results:\n")
for text, meter, expected in TEST_VERSES:
    r = verify_hemistich(text, meter)
    icon  = "✅" if r["pass"] else "❌"
    match = icon == "✅" and expected == "should_pass" \
         or icon == "❌" and expected == "should_fail"
    result_label = "CORRECT" if match else "⚠️ WRONG VERDICT"
    
    print(f"{icon}  [{result_label}]  stage={r['stage']}")
    print(f"    {text[:55]}...")
    if r["violations"]:
        for v in r["violations"]:
            print(f"    → {v.get('reason', str(v))}")
    print()
```

---

### Cell 4-B — Scan a full song XML output

```python
import xml.etree.ElementTree as ET

SAMPLE_XML = """
<song>
  <section type="verse" n="1" concept="test">
    <couplet n="1">
      <hemistich pos="1">إِنَّ الصَّوْتَ بِغَيْرِ قَاعِدَةٍ خَاوِي</hemistich>
      <hemistich pos="2">يَبْدُو نَحِيفاً في المَسَالِكِ وَالأَعْمَاقِ</hemistich>
    </couplet>
    <couplet n="2">
      <hemistich pos="1">إِنَّ الصَّوْتَ الجَمِيلَ بِغَيْرِ قَاعِدَةٍ خَاوِي</hemistich>
      <hemistich pos="2">يَبْدُو نَحِيفاً في المَسَالِكِ</hemistich>
    </couplet>
  </section>
</song>
"""

# Paste your actual LLM XML output here instead of the sample above.
# Replace SAMPLE_XML with a triple-quoted string of the <song>...</song> block.

DECLARED_METER = "البسيط"

def scan_song_xml(xml_string: str, declared_meter: str) -> dict:
    """
    Parse a <song> XML block and verify every hemistich.
    Returns:
      total      — number of hemistichs scanned
      passed     — number that passed
      broken     — list of broken hemistich records for LLM re-escalation
    """
    root = ET.fromstring(xml_string)
    
    broken  = []
    passed  = 0
    total   = 0
    
    for section in root.iter("section"):
        sec_type = section.get("type", "?")
        sec_n    = section.get("n", "")
        concept  = section.get("concept", "")
        
        for couplet in section.iter("couplet"):
            coup_n = couplet.get("n", "")
            
            for hemistich in couplet.iter("hemistich"):
                pos  = hemistich.get("pos", "?")
                text = (hemistich.text or "").strip()
                if not text:
                    continue
                
                total += 1
                result = verify_hemistich(text, declared_meter)
                
                if result["pass"]:
                    passed += 1
                else:
                    broken.append({
                        "section":  sec_type,
                        "section_n": sec_n,
                        "concept":  concept,
                        "couplet":  coup_n,
                        "pos":      pos,
                        "text":     text,
                        "violations": result["violations"],
                        "stage":    result["stage"],
                    })
    
    return {"total": total, "passed": passed, "broken": broken}


# Run
scan_result = scan_song_xml(SAMPLE_XML, DECLARED_METER)

print(f"Scan complete: {scan_result['passed']}/{scan_result['total']} passed\n")

if scan_result["broken"]:
    print("Broken hemistichs (LLM re-escalation candidates):\n")
    for b in scan_result["broken"]:
        print(f"  Section: {b['section']} n={b['section_n']}  |  Couplet: {b['couplet']}  |  Pos: {b['pos']}")
        print(f"  Text:    {b['text']}")
        for v in b["violations"]:
            print(f"  Violation: {v.get('reason', str(v))}")
        print()
else:
    print("All hemistichs passed — no LLM re-escalation needed.")
```

> **🔍 Observe:**  
> - Replace `SAMPLE_XML` with the actual XML your LLM produces.  
> - The `scan_result["broken"]` list is what you'd send back to the LLM.  
>   Is the violation information specific enough to guide re-composition?

---

### Cell 4-C — Generate an LLM re-escalation payload

```python
def build_correction_payload(scan_result: dict, declared_meter: str) -> str:
    """
    Build a minimal XML payload to send back to the LLM for re-composition.
    Only includes broken hemistichs — not the full song.
    """
    if not scan_result["broken"]:
        return "<correction_request><status>all_passed</status></correction_request>"
    
    lines = [f'<correction_request meter="{declared_meter}">']
    
    for b in scan_result["broken"]:
        violation_strs = " | ".join(v.get("reason", str(v)) for v in b["violations"])
        lines.append(
            f'  <broken_hemistich'
            f' section="{b["section"]}"'
            f' couplet="{b["couplet"]}"'
            f' pos="{b["pos"]}"'
            f' violation="{violation_strs}">'
        )
        lines.append(f'    {b["text"]}')
        lines.append( '  </broken_hemistich>')
    
    lines.append('</correction_request>')
    return "\n".join(lines)


payload = build_correction_payload(scan_result, DECLARED_METER)
print("LLM re-escalation payload:\n")
print(payload)
```

---

---

## PART 5 — Observations Worksheet

> Fill this in as you run each cell. Collect the answers here before making  
> the final library selection decision.

---

### Cell 5-A — Print summary of findings

```python
print("=" * 65)
print("LIBRARY EXPLORATION SUMMARY")
print("=" * 65)
print()

print("1. AVAILABILITY IN THIS COLAB RUNTIME")
print(f"   pyarabic : {'✅ available' if PYARABIC_OK else '❌ unavailable'}")
print(f"   aruudy   : {'✅ available' if ARUUDY_OK else '❌ unavailable'}")
print(f"   pyarud   : {'✅ direct' if (PYARUD_OK and not PYARUD_VIA_SUBPROCESS) else '⚠️ subprocess only' if PYARUD_VIA_SUBPROCESS else '❌ unavailable'}")
print()

# Fill these in manually after running the cells above:
observations = {
    "PyArabic — normalization changed any verse":           "?",  # yes / no
    "PyArabic — any unexpected side effects noticed":       "?",  # yes / no / describe
    "Aruudy — meter detection function name":               "?",  # e.g. get_ameter
    "Aruudy — meter names in Arabic (match declared)":      "?",  # yes / no / translation needed
    "Aruudy — prosodic transcription looks correct":        "?",  # yes / no
    "Aruudy — broken verse correctly fails fast gate":      "?",  # yes / no
    "PyArud — scan function name":                          "?",  # e.g. analyze
    "PyArud — foot status values returned":                 "?",  # e.g. ok, broken, ...
    "PyArud — zihāf names in Arabic or Latin":              "?",  # Arabic / Latin
    "PyArud — broken verse: specific foot identified":      "?",  # yes / no
    "PyArud — zihāf verse: passes with zihāf annotation":  "?",  # yes / no
    "Pipeline — any false positives on correct verses":     "?",  # yes / no
    "Pipeline — any false negatives on broken verse":       "?",  # yes / no
    "Subprocess latency for PyArud (if used)":              "?",  # e.g. ~50ms per call
}

print("2. OBSERVATIONS (fill in manually after running cells):")
for question, answer in observations.items():
    flag = "⚠️" if answer == "?" else ("✅" if answer in ("yes", "no", "Arabic", "Latin") else "📝")
    print(f"   {flag}  {question}")
    print(f"        → {answer}")
    print()
```

---

### Cell 5-B — Decision matrix

```python
# After filling in the observations above, use this to generate a recommendation.

print("=" * 65)
print("DECISION MATRIX")
print("=" * 65)
print("""
CRITERION                            PYARABIC  ARUUDY    PYARUD
─────────────────────────────────────────────────────────────────
Works in Colab runtime               [  ?  ]   [  ?  ]   [  ?  ]
Foot-level violation detail          [ N/A ]   [  ✗  ]   [  ?  ]
Meter name matches system prompt     [ N/A ]   [  ?  ]   [  ?  ]
Zihāf names usable for allowlist     [ N/A ]   [ N/A ]   [  ?  ]
Correctly fails broken verse         [ N/A ]   [  ?  ]   [  ?  ]
False positive rate (correct verses) [ N/A ]   [  ?  ]   [  ?  ]
License acceptable                   [ GPL ]   [Apache]  [Apache]
─────────────────────────────────────────────────────────────────
Fill in ✅ / ❌ / ⚠️ after running the cells above.
""")

print("""PIPELINE RECOMMENDATION (fill in after testing):
─────────────────────────────────────────────────────────────────
Normalization layer  →  PyArabic  (replace with custom if GPL concern)
Fast gate            →  Aruudy    if meter detection works correctly
                        SKIP      if Aruudy unreliable or unavailable
Deep scan            →  PyArud    (direct import or subprocess)
                        Aruudy    as fallback if PyArud unavailable
Zihāf allowlist      →  custom wrapper around PyArud (always needed)
─────────────────────────────────────────────────────────────────
""")
```

---

---

## Appendix A — Quick PyArabic Reference

These are the functions most relevant to the pipeline, confirmed stable across PyArabic versions:

```python
import pyarabic.araby as araby

# Remove tatweel (ـ)
araby.strip_tatweel(text)

# Remove ALL tashkeel (diacritics) — use to get bare consonant skeleton
araby.strip_tashkeel(text)

# Remove only shadda, keep other diacritics
araby.strip_shadda(text)

# Normalize hamza forms (أ إ آ → unified)
araby.normalize_hamza(text)

# Check if character is in Arabic Unicode range
araby.is_arabicrange(char)

# Arabic-aware tokenization
araby.tokenize(text)

# Constants useful for manual diacritic handling:
araby.FATHA     # َ
araby.KASRA     # ِ
araby.DAMMA     # ُ
araby.SUKUN     # ْ
araby.SHADDA    # ّ
araby.HARAKAT   # set of all short vowel marks
araby.TANWIN    # set of tanwin marks
```

---

## Appendix B — Meter Name Reference

Use this table to map detected meter names to the system prompt's declared names, in case libraries return different string forms:

| System Prompt Name | Common Latin Transliteration | Alternate Arabic Spellings |
|--------------------|------------------------------|---------------------------|
| الطويل             | taweel / al-tawil            | الطويل                   |
| البسيط             | baseet / al-basit            | البسيط                   |
| الكامل             | kamel / al-kamil             | الكامل                   |
| الرجز              | rajaz / al-rajaz             | الرجز                    |
| المتقارب           | mutaqarib                    | المتقارب                 |
| الوافر             | wafir / al-wafir             | الوافر                   |
| الخفيف             | khafeef / al-khafif          | الخفيف                   |
| السريع             | saree / al-saric             | السريع                   |

If a library returns Latin transliterations, add a translation dict in Cell 3-E / Cell 2-E.

---

## Appendix C — Known PyArud API Uncertainty

PyArud's documentation is thin. The function signatures below are derived from source code inspection as of the library's last public release. **Verify everything in Cell 3-A before trusting these.**

```python
# Most likely top-level scan function (verify in Cell 3-A):
pyarud.analyze(hemistich_text)

# Result object likely has:
result.meter        # detected meter name (str)
result.feet         # list of foot objects
result.is_valid     # bool shortcut (if present)

# Each foot object likely has:
foot.name           # tafʿīla name (str), e.g. "مَفَاعِيلُنْ"
foot.status         # "ok" | "broken" | "missing" | "extra_bits"
foot.zihaf          # zihāf name or None
foot.pattern        # ∪/– pattern string
foot.realized       # what was actually found in the text
```

If the API differs, the attribute names in Cells 3-D and 3-E have clearly marked  
`# ← fill in from Cell 3-C` comments — update those and everything downstream adapts.
