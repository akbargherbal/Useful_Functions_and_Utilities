"""
Arabic Prosody Verification Pipeline
Normalizes LLM Arabic text and verifies meter/zihafat using PyArud.
"""

import sys
import json
import subprocess
import tempfile
import os
import unicodedata
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Environment Setup & Dependency Checks
# ---------------------------------------------------------------------------
PYARABIC_OK = False
PYARUD_OK = False
PYARUD_VIA_SUBPROCESS = False

try:
    import pyarabic.araby as araby
    PYARABIC_OK = True
except ImportError as e:
    print(f"❌ pyarabic — {e}")

try:
    import pyarud
    PYARUD_OK = True
except ImportError as e:
    print(f"⚠️ pyarud — {e}")
    print("   → PyArud needs Python 3.12. Falling back to subprocess mode.")
    PYARUD_VIA_SUBPROCESS = True

# ---------------------------------------------------------------------------
# Constants & Allowlists
# ---------------------------------------------------------------------------
PERMITTED_ZIHAFAT = {
    "الطويل":   {"القبض"},
    "البسيط":   {"الخبن", "الطي"},
    "الكامل":   {"الإضمار", "الوقص"},
    "الرجز":    {"الخبن"},
    "المتقارب": {"القبض"},
    "الوافر":   {"العقل"},
    "الخفيف":   {"الخبن", "الكف"},
    "السريع":   {"الطي", "الخبن"},
}

METER_MAP = {
    "taweel":     "الطويل",
    "baseet":     "البسيط",
    "kamel":      "الكامل",
    "rajaz":      "الرجز",
    "mutaqarib":  "المتقارب",
    "wafir":      "الوافر",
    "khafeef":    "الخفيف",
    "saree":      "السريع",
}

# ---------------------------------------------------------------------------
# Core Pipeline Functions
# ---------------------------------------------------------------------------

def normalize_for_scanning(text: str) -> str:
    """Normalize a fully-diacritized Arabic hemistich before prosodic scanning."""
    if not PYARABIC_OK:
        return text
    text = unicodedata.normalize("NFC", text)
    text = araby.strip_tatweel(text)
    text = araby.normalize_hamza(text)
    for char in ["\u200c", "\u200d", "\u200e", "\u200f", "\ufeff"]:
        text = text.replace(char, "")
    text = " ".join(text.split())
    return text


def _build_result(result: dict, declared_meter: str) -> dict:
    """Shared logic: extract violations from a pyarud result dict."""
    allowed_z = PERMITTED_ZIHAFAT.get(declared_meter, set())
    detected_latin = result.get("meter", "")
    detected_meter = METER_MAP.get(detected_latin, detected_latin)
    meter_match = str(detected_meter).strip() == declared_meter.strip()

    verses = result.get("verses", [])
    feet = verses[0].get("sadr_analysis", []) if verses else []
    violations = []

    for foot in feet:
        status = foot.get("status", "ok")
        zihaf  = foot.get("zihaf", None)
        name   = foot.get("name", "?")
        seq    = foot.get("foot_index", "?")

        if status in ("broken", "missing", "extra_bits"):
            violations.append({
                "foot_seq": seq, "foot_name": name,
                "status": status, "zihaf": zihaf,
                "reason": f"status_{status}",
            })
        elif zihaf and zihaf not in allowed_z:
            violations.append({
                "foot_seq": seq, "foot_name": name,
                "status": "unlisted_zihaf", "zihaf": zihaf,
                "reason": f"unlisted_zihaf:{zihaf}",
            })

    if not meter_match:
        violations.insert(0, {
            "foot_seq": 0, "foot_name": "—",
            "status": "wrong_meter", "zihaf": None,
            "reason": f"detected:{detected_meter}",
        })

    return {
        "pass": len(violations) == 0,
        "violations": violations,
        "detected_meter": detected_meter,
        "meter_match": meter_match,
        "foot_count": len(feet),
    }


# Module-level processor cache for the direct-import path.
_processor = None

def deep_scan_pyarud(hemistich: str, declared_meter: str) -> dict:
    """Foot-by-foot prosodic analysis using direct PyArud import."""
    if not PYARUD_OK or PYARUD_VIA_SUBPROCESS:
        return {"pass": None, "reason": "pyarud_unavailable"}

    global _processor
    from pyarud.processor import ArudhProcessor
    if _processor is None:
        _processor = ArudhProcessor()

    cleaned = normalize_for_scanning(hemistich)
    try:
        result = _processor.process_poem([(cleaned, cleaned)])
    except Exception as e:
        return {"pass": False, "reason": f"scan_error:{e}", "violations": []}

    return _build_result(result, declared_meter)


# ---------------------------------------------------------------------------
# Batch Subprocess Fallback (For Python < 3.12 environments)
#
# Key change from the original: we spawn python3.12 ONCE per batch,
# pass all hemistichs via stdin as JSON, and read all results from stdout.
# This eliminates N×(interpreter startup + import time) overhead.
# ---------------------------------------------------------------------------

# The helper reads a JSON array of {text, meter} from stdin and writes
# a JSON array of result dicts to stdout — one process for the whole batch.
PYARUD_BATCH_HELPER = """
import sys, json
from pyarud.processor import ArudhProcessor

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
METER_MAP = {
    "taweel": "الطويل", "baseet": "البسيط", "kamel": "الكامل",
    "rajaz": "الرجز", "mutaqarib": "المتقارب", "wafir": "الوافر",
    "khafeef": "الخفيف", "saree": "السريع",
}

items = json.loads(sys.stdin.read())
processor = ArudhProcessor()   # instantiated ONCE for the entire batch
results = []

for item in items:
    text           = item["text"]
    declared_meter = item["meter"]
    try:
        result         = processor.process_poem([(text, text)])
        detected_latin = result.get("meter", "")
        detected       = METER_MAP.get(detected_latin, detected_latin)
        allowed_z      = PERMITTED_ZIHAFAT.get(declared_meter, [])
        verses         = result.get("verses", [])
        feet           = verses[0].get("sadr_analysis", []) if verses else []
        violations     = []

        for foot in feet:
            status = foot.get("status", "ok")
            zihaf  = foot.get("zihaf", None)
            name   = foot.get("name", "?")
            seq    = foot.get("foot_index", 0)
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

        results.append({"pass": len(violations) == 0, "violations": violations,
                         "detected_meter": detected, "meter_match": meter_match,
                         "foot_count": len(feet)})
    except Exception as e:
        results.append({"pass": False, "violations": [],
                         "reason": f"scan_error:{str(e)}"})

print(json.dumps(results))
"""

# Write the helper once at import time so repeated calls pay no disk I/O.
_helper_path: str | None = None

def _ensure_helper() -> str:
    global _helper_path
    if _helper_path is None:
        fd, path = tempfile.mkstemp(suffix=".py", prefix="pyarud_batch_")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(PYARUD_BATCH_HELPER)
        _helper_path = path
    return _helper_path


def batch_scan_subprocess(items: list[dict]) -> list[dict]:
    """
    Run pyarud on a list of {text, meter} dicts via a single python3.12 subprocess.
    Returns a list of result dicts in the same order.
    """
    if not items:
        return []

    helper = _ensure_helper()
    payload = json.dumps(items, ensure_ascii=False)

    try:
        proc = subprocess.run(
            ["python3.12", helper],
            input=payload,
            capture_output=True,
            text=True,
            timeout=60,
            encoding="utf-8",
        )
        if proc.returncode != 0:
            err = proc.stderr[:300]
            return [{"pass": False, "reason": f"subprocess_error:{err}", "violations": []}
                    for _ in items]
        return json.loads(proc.stdout)
    except Exception as e:
        return [{"pass": False, "reason": f"exception:{e}", "violations": []}
                for _ in items]


# ---------------------------------------------------------------------------
# High-Level Verification API
# ---------------------------------------------------------------------------

def verify_hemistich(text: str, declared_meter: str) -> dict:
    """Verify a single hemistich. Prefer verify_hemistichs() for bulk use."""
    results = verify_hemistichs([(text, declared_meter)])
    return results[0]


def verify_hemistichs(pairs: list[tuple[str, str]]) -> list[dict]:
    """
    Verify multiple (hemistich, meter) pairs efficiently.

    In subprocess mode this costs ONE python3.12 spawn regardless of batch size,
    vs the original N spawns.  In direct-import mode the processor is reused.

    Args:
        pairs: list of (hemistich_text, declared_meter) tuples

    Returns:
        list of result dicts with keys: pass, violations, hemistich, declared_meter
    """
    normalized = [(normalize_for_scanning(text), meter) for text, meter in pairs]

    if PYARUD_VIA_SUBPROCESS:
        items = [{"text": t, "meter": m} for t, m in normalized]
        raw_results = batch_scan_subprocess(items)
        return [
            {
                "pass": r.get("pass", False),
                "violations": r.get("violations", []),
                "hemistich": t,
                "declared_meter": m,
            }
            for (t, m), r in zip(normalized, raw_results)
        ]

    if PYARUD_OK:
        return [
            {
                **deep_scan_pyarud(t, m),
                "hemistich": t,
                "declared_meter": m,
            }
            for t, m in normalized
        ]

    # No scanner available
    return [
        {"pass": None, "stage": "no_scanner", "violations": [],
         "hemistich": t, "declared_meter": m}
        for t, m in normalized
    ]


# ---------------------------------------------------------------------------
# XML Parsing
# ---------------------------------------------------------------------------

def scan_song_xml(xml_string: str, declared_meter: str) -> dict:
    """Parse a <song> XML block and verify every hemistich (batched)."""
    root = ET.fromstring(xml_string)
    meta = []   # (sec_type, sec_n, concept, coup_n, pos, text)

    for section in root.iter("section"):
        sec_type = section.get("type", "?")
        sec_n    = section.get("n", "")
        concept  = section.get("concept", "")
        for couplet in section.iter("couplet"):
            coup_n = couplet.get("n", "")
            for hemistich in couplet.iter("hemistich"):
                pos  = hemistich.get("pos", "?")
                text = (hemistich.text or "").strip()
                if text:
                    meta.append((sec_type, sec_n, concept, coup_n, pos, text))

    pairs   = [(text, declared_meter) for *_, text in meta]
    results = verify_hemistichs(pairs)

    broken = []
    passed = 0
    for (sec_type, sec_n, concept, coup_n, pos, text), result in zip(meta, results):
        if result["pass"]:
            passed += 1
        else:
            broken.append({
                "section": sec_type, "section_n": sec_n, "concept": concept,
                "couplet": coup_n, "pos": pos, "text": text,
                "violations": result["violations"],
            })

    return {"total": len(meta), "passed": passed, "broken": broken}


def build_correction_payload(scan_result: dict, declared_meter: str) -> str:
    """Build a minimal XML payload to send back to the LLM for re-composition."""
    if not scan_result["broken"]:
        return "<correction_request><status>all_passed</status></correction_request>"

    lines = [f'<correction_request meter="{declared_meter}">']
    for b in scan_result["broken"]:
        violation_strs = " | ".join(v.get("reason", str(v)) for v in b["violations"])
        lines.append(
            f'  <broken_hemistich section="{b["section"]}" couplet="{b["couplet"]}" '
            f'pos="{b["pos"]}" violation="{violation_strs}">'
        )
        lines.append(f'    {b["text"]}')
        lines.append("  </broken_hemistich>")
    lines.append("</correction_request>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Test Execution Block
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print(f"Python version: {sys.version}\n")

    TEST_VERSES = [
        ("الخَيْلُ وَاللَّيْلُ وَالبَيْدَاءُ تَعْرِفُنِي", "البسيط", "should_pass"),
        ("أَلَا لَيْتَ شِعْرِي هَلْ أَبِيتَنَّ لَيْلَةً",  "الطويل", "should_pass"),
        ("إِنَّ الصَّوْتَ الجَمِيلَ بِغَيْرِ قَاعِدَةٍ خَاوِي", "البسيط", "should_fail"),
        ("كَرَمَ الزَّمَانُ عَلَى الكِرَامِ فَأَكْرَمَا",  "الكامل", "should_pass"),
        ("أَلَا لَيْتَ شِعْرِي هَلْ أَبِيتَنَّ لَيْلَةً",  "الطويل", "should_pass"),
    ]

    import time

    print("--- Running Pipeline Tests (batched) ---")
    t0 = time.perf_counter()
    pairs = [(text, meter) for text, meter, _ in TEST_VERSES]
    all_results = verify_hemistichs(pairs)
    elapsed = time.perf_counter() - t0
    print(f"Batch of {len(pairs)} completed in {elapsed:.2f}s\n")

    for (text, meter, expected), r in zip(TEST_VERSES, all_results):
        icon  = "✅" if r["pass"] else "❌"
        match = (icon == "✅" and expected == "should_pass") or \
                (icon == "❌" and expected == "should_fail")
        label = "CORRECT" if match else "⚠️ WRONG VERDICT"
        print(f"{icon} [{label}] {meter}: {text[:40]}...")
        for v in r.get("violations", []):
            print(f"    → {v.get('reason', str(v))}")
    print()

    SAMPLE_XML = """
    <song>
      <section type="verse" n="1" concept="test">
        <couplet n="1">
          <hemistich pos="1">الخَيْلُ وَاللَّيْلُ وَالبَيْدَاءُ تَعْرِفُنِي</hemistich>
          <hemistich pos="2">وَالسَّيْفُ وَالرُّمْحُ وَالقِرْطَاسُ وَالقَلَمُ</hemistich>
        </couplet>
        <couplet n="2">
          <hemistich pos="1">إِنَّ الصَّوْتَ الجَمِيلَ بِغَيْرِ قَاعِدَةٍ خَاوِي</hemistich>
          <hemistich pos="2">يَبْدُو نَحِيفاً في المَسَالِكِ</hemistich>
        </couplet>
      </section>
    </song>
    """

    print("--- Running XML Parsing Test ---")
    scan_result = scan_song_xml(SAMPLE_XML, "البسيط")
    print(f"Scan complete: {scan_result['passed']}/{scan_result['total']} passed\n")

    if scan_result["broken"]:
        print("Generated LLM Re-escalation Payload:")
        print(build_correction_payload(scan_result, "البسيط"))
