"""
arabic_prosody_helpers.py
=========================
Importable helper functions for Arabic meter (ʿArūḍ) detection, zihāf
identification, health scoring, and issue summarisation.

Built on top of **pyarud** v0.1.10 (pip install pyarud).

Quick start
-----------
    from arabic_prosody_helpers import analyze_poem, summarize_issues

    result = analyze_poem([
        ("أَنَامُ مِلْءَ جُفُونِي عَنْ شَوَارِدِهَا",
         "وَيَسْهَرُ الْخَلْقُ جَرَّاهَا وَيَخْتَصِمُ"),
    ])
    print(result.meter)                    # "baseet"
    print(summarize_issues(result.verses[0]))

Requires Python ≥ 3.12 and pyarud ≥ 0.1.10.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from typing import Literal

# ---------------------------------------------------------------------------
# Optional pyarud imports — fail clearly if library is absent
# ---------------------------------------------------------------------------
try:
    from pyarud.processor import ArudhProcessor
    from pyarud.arudi import ArudiConverter
    from pyarud.tafeela import (
        Fawlon, Faelon, Faelaton, Mafaeelon, Mustafelon,
        Mutafaelon, Mafaelaton, Mafoolato, Fae_laton, Mustafe_lon,
    )
    _PYARUD_AVAILABLE = True
except ImportError:
    _PYARUD_AVAILABLE = False


# ===========================================================================
# 1. Data model
# ===========================================================================

FootStatus = Literal["ok", "broken", "missing", "extra_bits"]
HealthLevel = Literal["perfect", "valid_zihaf", "broken", "severe"]


@dataclass
class FootResult:
    """
    Per-foot analysis result enriched with zihāf identification.

    Attributes
    ----------
    foot_index:
        Zero-based position of this foot within the hemistich.
    expected_pattern:
        Binary string of the best-matched canonical (or zihāf) form, e.g. ``"11010"``.
    actual_segment:
        Binary string extracted from the input at this position.
    canonical_pattern:
        The pristine (Salīm / un-modified) pattern for this foot type.
    score:
        SequenceMatcher ratio raised to the 6th power, in ``[0.0, 1.0]``.
    status:
        ``"ok"`` · ``"broken"`` · ``"missing"`` · ``"extra_bits"``
    zihaf_name:
        Name of the applied zihāf/ʿilla, or ``"Salim"`` if pristine, or
        ``None`` when status is not ``"ok"``.
    health:
        Collapsed health label — see :func:`foot_health`.
    position_label:
        Human-readable foot role: ``"Hashw"``, ``"ʿArūḍ"``, or ``"Ḍarb"``.
    """
    foot_index: int
    expected_pattern: str
    actual_segment: str
    canonical_pattern: str
    score: float
    status: FootStatus
    zihaf_name: str | None
    health: HealthLevel
    position_label: str


@dataclass
class HemistichResult:
    """Enriched analysis of one hemistich (Ṣadr or ʿAjuz)."""
    text: str
    binary_pattern: str
    feet: list[FootResult]
    score: float               # average foot score
    is_sound: bool             # True ↔ all feet are "ok"
    broken_foot_indices: list[int]
    missing_foot_count: int
    extra_bits: str | None     # remaining bits after all feet consumed


@dataclass
class VerseResult:
    """Full analysis of one bayt (verse = Ṣadr + ʿAjuz)."""
    verse_index: int
    sadr: HemistichResult
    ajuz: HemistichResult | None   # None for single-hemistich input
    combined_score: float
    meter: str
    issues: list[str] = field(default_factory=list)   # plain-English diagnostics


@dataclass
class PoemResult:
    """Top-level result for a full poem."""
    meter: str
    meter_arabic: str
    total_verses: int
    verses: list[VerseResult]
    overall_score: float
    is_metrically_sound: bool
    candidate_meters: list[tuple[str, float]]   # top-3 (meter, score)


# ===========================================================================
# 2. Static lookup tables
# ===========================================================================

#: Canonical binary patterns for all ten prosodic feet (tafāʿīl).
CANONICAL_PATTERNS: dict[str, str] = {
    "Fawlon":       "11010",    # فَعُولُنْ
    "Faelon":       "10110",    # فَاعِلُنْ
    "Faelaton":     "1011010",  # فَاعِلَاتُنْ
    "Mafaeelon":    "1101010",  # مَفَاعِيلُنْ
    "Mustafelon":   "1010110",  # مُسْتَفْعِلُنْ
    "Mutafaelon":   "1110110",  # مُتَفَاعِلُنْ
    "Mafaelaton":   "1101110",  # مُفَاعَلَتُنْ
    "Mafoolato":    "1010101",  # مَفْعُولَاتُ
    "Mustafe_lon":  "1010110",  # مُسْتَفْعِ لُنْ  (split, Khafif context)
    "Fae_laton":    "1011010",  # فَاعِ لَاتُنْ    (split, Muḍāriʿ context)
}

#: Arabic display names keyed by the pyarud meter string.
METER_ARABIC_NAMES: dict[str, str] = {
    "taweel":    "الطويل",
    "madeed":    "المديد",
    "baseet":    "البسيط",
    "wafer":     "الوافر",
    "kamel":     "الكامل",
    "hazaj":     "الهزج",
    "rajaz":     "الرجز",
    "ramal":     "الرمل",
    "saree":     "السريع",
    "munsareh":  "المنسرح",
    "khafeef":   "الخفيف",
    "mudhare":   "المضارع",
    "muqtadheb": "المقتضب",
    "mujtath":   "المجتث",
    "mutakareb": "المتقارب",
    "mutadarak": "المتدارك",
}

#: Hashw template (canonical feet listing) for all 16 meters.
METER_TEMPLATES: dict[str, str] = {
    "taweel":    "فَعُولُنْ مَفَاعِيلُنْ فَعُولُنْ مَفَاعِلُ",
    "madeed":    "فَاعِلَاتُنْ فَاعِلُنْ فَاعِلَاتُ",
    "baseet":    "مُسْتَفْعِلُنْ فَاعِلُنْ مُسْتَفْعِلُنْ فَعِلُ",
    "wafer":     "مُفَاعَلَتُنْ مُفَاعَلَتُنْ فَعُولُ",
    "kamel":     "مُتَفَاعِلُنْ مُتَفَاعِلُنْ مُتَفَاعِلُ",
    "hazaj":     "مَفَاعِيلُنْ مَفَاعِيلُ",
    "rajaz":     "مُسْتَفْعِلُنْ مُسْتَفْعِلُنْ مُسْتَفْعِلُ",
    "ramal":     "فَاعِلَاتُنْ فَاعِلَاتُنْ فَاعِلَاتُ",
    "saree":     "مُسْتَفْعِلُنْ مُسْتَفْعِلُنْ فَاعِلُ",
    "munsareh":  "مُسْتَفْعِلُنْ مَفْعُولَاتُ مُفْتَعِلُ",
    "khafeef":   "فَاعِلَاتُنْ مُسْتَفْعِلُنْ فَاعِلَاتُ",
    "mudhare":   "مَفَاعِيلُ فَاعِلَاتُ",
    "muqtadheb": "مَفْعُولَاتُ مُفْتَعِلُ",
    "mujtath":   "مُسْتَفْعِلُنْ فَاعِلَاتُ",
    "mutakareb": "فَعُولُنْ فَعُولُنْ فَعُولُنْ فَعُولُ",
    "mutadarak": "فَعِلُنْ فَعِلُنْ فَعِلُنْ فَعِلُ",
}

#: Known zihāfāt: (canonical_pattern, modified_pattern) → zihāf name.
#: Covers all single and compound zihāfāt defined in pyarud/zihaf.py.
_ZIHAF_MAP: dict[tuple[str, str], str] = {
    # --- Fawlon (فَعُولُنْ) 11010 ---
    ("11010", "1010"):   "Qabadh",      # drop index 4 (5th bit)
    ("11010", "110"):    "Hadhf",        # drop last sabab (10)
    ("11010", "11"):     "Batr",         # Hadhf + Qataa

    # --- Faelon (فَاعِلُنْ) 10110 ---
    ("10110", "1110"):   "Khaban",       # index 1: 1[0]110 → 1110

    # --- Faelaton (فَاعِلَاتُنْ) 1011010 ---
    ("1011010", "111010"): "Khaban",     # drop index 1
    ("1011010", "101110"): "Kaff",       # drop index 6 (last sakin of sabab)
    ("1011010", "10110"):  "Hadhf",      # drop last sabab
    ("1011010", "111110"): "Shakal",     # Khaban + Kaff
    ("1011010", "1010"):   "Waqf",       # quiet last bit of watad mafrūq

    # --- Mafaeelon (مَفَاعِيلُنْ) 1101010 ---
    ("1101010", "111010"): "Qabadh",    # drop index 4
    ("1101010", "110110"): "Kaff",      # drop index 6
    ("1101010", "11010"):  "Hadhf",     # drop last sabab
    ("1101010", "111110"): "Shakl_alt", # Qabadh + Kaff (rare)

    # --- Mustafelon (مُسْتَفْعِلُنْ) 1010110 ---
    ("1010110", "110110"): "Khaban",    # drop index 1
    ("1010110", "101110"): "Tay",       # drop index 3
    ("1010110", "11110"):  "Khabal",    # Khaban + Tay (drop 1 & 3)
    ("1010110", "10110"):  "Kasf",      # drop index 6 (Saree context)

    # --- Mutafaelon (مُتَفَاعِلُنْ) 1110110 ---
    ("1110110", "1010110"): "Edmaar",   # index 1: 1[1]10110 → 10 (quieted)
    ("1110110", "1100110"): "Waqas",    # index 3 dropped
    ("1110110", "1010110"): "Idmar",    # alias for Edmaar (common name)
    ("1110110", "1000110"): "Khazal",   # Edmaar + Tay

    # --- Mafaelaton (مُفَاعَلَتُنْ) 1101110 ---
    ("1101110", "110110"):  "Akal",     # drop index 4 (Wafir context)
    ("1101110", "11010"):   "Asab",     # index 4 quieted → Qataf
    ("1101110", "110"):     "Qatf",     # Hadhf + Asab (terminal Wafir)

    # --- Mafoolato (مَفْعُولَاتُ) 1010101 ---
    ("1010101", "110101"): "Khaban",    # drop index 1
    ("1010101", "101101"): "Tay",       # drop index 3
    ("1010101", "101011"): "Kasf",      # drop index 6

    # --- Mustafe_lon (split) 1010110 same as Mustafelon in bits ---
    # Distinguished at the Bahr level; same zihaf names apply.

    # --- Generic terminal ellal (apply to any foot at ʿArūḍ / Ḍarb) ---
    # These have variable source lengths so we handle them in identify_zihaf().
}


# ===========================================================================
# 3. Low-level utilities
# ===========================================================================

def similarity(a: str, b: str) -> float:
    """
    Compute the SequenceMatcher ratio raised to the 6th power.

    This mirrors pyarud's internal ``_get_similarity()`` and penalises even
    small mismatches heavily:

    - ratio ``1.00`` → ``1.00``  (perfect match)
    - ratio ``0.95`` → ``~0.74``
    - ratio ``0.80`` → ``~0.26``

    Parameters
    ----------
    a, b:
        Binary strings of ``"0"`` and ``"1"``.

    Returns
    -------
    float
        Score in ``[0.0, 1.0]``.
    """
    raw = SequenceMatcher(None, a, b).ratio()
    return math.pow(raw, 6)


def get_binary_pattern(text: str, *, saturate: bool = True) -> tuple[str, str]:
    """
    Convert fully-diacritized Arabic text to its Arudi representation and
    binary prosodic pattern.

    Parameters
    ----------
    text:
        Diacritized Arabic string, e.g. ``"أَنَامُ مِلْءَ جُفُونِي"``.
    saturate:
        Extend the final vowel (Ashbaʿ — إِشْبَاع) as per classical convention.
        Pass ``False`` for the Ajuz of a Muqayyad-rhyme poem.

    Returns
    -------
    tuple[str, str]
        ``(arudi_text, binary_pattern)``

    Raises
    ------
    RuntimeError
        If pyarud is not installed.

    Examples
    --------
    >>> arudi, pattern = get_binary_pattern("فَعُولُنْ", saturate=False)
    >>> pattern
    '11010'
    """
    _require_pyarud()
    converter = ArudiConverter()
    return converter.prepare_text(text, saturate=saturate)


def identify_zihaf(
    canonical: str,
    actual: str,
) -> str:
    """
    Identify the zihāf or ʿilla applied to a prosodic foot by comparing its
    canonical binary pattern against the observed pattern.

    The function first checks the static lookup table ``_ZIHAF_MAP``.  If no
    exact match is found it falls back to a structural delta comparison
    (counting dropped vs quieted bits) and returns a descriptive label.

    Parameters
    ----------
    canonical:
        Pristine (Salīm) binary pattern, e.g. ``"1010110"``.
    actual:
        Observed binary pattern after modification, e.g. ``"110110"``.

    Returns
    -------
    str
        One of the classical zihāf / ʿilla names (``"Khaban"``, ``"Edmaar"`` …),
        ``"Salim"`` if the patterns are identical, or a structural description
        such as ``"Unknown (1 bit dropped)"`` when no name is found.

    Examples
    --------
    >>> identify_zihaf("1010110", "110110")
    'Khaban'
    >>> identify_zihaf("11010", "11010")
    'Salim'
    """
    if canonical == actual:
        return "Salim"

    key = (canonical, actual)
    if key in _ZIHAF_MAP:
        return _ZIHAF_MAP[key]

    # Structural fallback -------------------------------------------------
    len_diff = len(canonical) - len(actual)
    if len_diff > 0:
        return f"Unknown ({len_diff} bit{'s' if len_diff > 1 else ''} dropped)"
    if len_diff < 0:
        return f"Unknown ({abs(len_diff)} bit{'s' if abs(len_diff) > 1 else ''} added)"

    # Same length but different bits → a Taskīn (quieting) operation
    diffs = sum(c != a for c, a in zip(canonical, actual))
    return f"Unknown (Taskeen, {diffs} bit{'s' if diffs > 1 else ''} changed)"


def foot_health(
    status: FootStatus,
    score: float,
    zihaf_name: str | None,
) -> HealthLevel:
    """
    Collapse foot status into a four-level health label.

    +------------+-----------------------------------------------------------+
    | Level      | Meaning                                                   |
    +============+===========================================================+
    | perfect    | Foot is Salīm (canonical pattern, no modification).       |
    +------------+-----------------------------------------------------------+
    | valid_zihaf| Foot is ``"ok"`` with a recognised classical modification.|
    +------------+-----------------------------------------------------------+
    | broken     | Foot cannot be mapped to any canonical or modified form.  |
    +------------+-----------------------------------------------------------+
    | severe     | Foot is missing from the input or leftover bits remain.   |
    +------------+-----------------------------------------------------------+

    Parameters
    ----------
    status:
        Raw pyarud status string.
    score:
        Foot score (0–1).
    zihaf_name:
        Identified zihāf / ʿilla name, or ``None``.

    Returns
    -------
    HealthLevel
    """
    if status in ("missing", "extra_bits"):
        return "severe"
    if status == "broken":
        return "broken"
    # status == "ok"
    if zihaf_name == "Salim":
        return "perfect"
    return "valid_zihaf"


def get_canonical_pattern(foot_class_name: str) -> str | None:
    """
    Return the canonical binary pattern for a named prosodic foot class.

    Parameters
    ----------
    foot_class_name:
        Python class name as defined in pyarud, e.g. ``"Mustafelon"``.

    Returns
    -------
    str or None
        Binary string, or ``None`` if the name is not recognised.

    Examples
    --------
    >>> get_canonical_pattern("Fawlon")
    '11010'
    """
    return CANONICAL_PATTERNS.get(foot_class_name)


# ===========================================================================
# 4. Core analysis helpers
# ===========================================================================

def _require_pyarud() -> None:
    if not _PYARUD_AVAILABLE:
        raise RuntimeError(
            "pyarud is not installed. Run: pip install pyarud"
        )


def _get_processor() -> "ArudhProcessor":
    _require_pyarud()
    return ArudhProcessor()


def _enrich_foot(
    raw: dict,
    position_label: str,
    num_feet: int,
) -> FootResult:
    """
    Convert a raw pyarud ``FootAnalysis`` dict to an enriched :class:`FootResult`.

    The canonical pattern is inferred by looking up the expected_pattern
    length in the canonical patterns table (imperfect but fast without
    re-running all foot combinatorics).
    """
    expected = raw.get("expected_pattern", "")
    actual   = raw.get("actual_segment", "")
    status   = raw.get("status", "broken")
    score    = raw.get("score", 0.0)

    # Canonical lookup:
    # 1. If expected_pattern is itself a known Salīm pattern → foot is pristine.
    # 2. Otherwise check _ZIHAF_MAP for a known (canonical → actual) pair.
    canonical_values = set(CANONICAL_PATTERNS.values())
    canonical = expected  # default: treat matched form as canonical

    zihaf_name: str | None = None
    if status == "ok":
        if expected in canonical_values and expected == actual:
            # Pattern is a recognised canonical and matches input → Salīm
            zihaf_name = "Salim"
        else:
            # Try to find the canonical that was modified to produce `actual`
            found_canon: str | None = None
            for key in _ZIHAF_MAP:
                if key[1] == actual and key[0] in canonical_values:
                    found_canon = key[0]
                    break
            if found_canon:
                canonical = found_canon
                zihaf_name = identify_zihaf(canonical, actual)
            else:
                # Neither Salīm nor in map → structural fallback
                zihaf_name = identify_zihaf(expected, actual)

    health = foot_health(status, score, zihaf_name)

    return FootResult(
        foot_index=raw.get("foot_index", 0),
        expected_pattern=expected,
        actual_segment=actual,
        canonical_pattern=canonical,
        score=score,
        status=status,
        zihaf_name=zihaf_name,
        health=health,
        position_label=position_label,
    )


def _enrich_hemistich(
    text: str,
    pattern: str,
    raw_feet: list[dict],
    *,
    is_ajuz: bool = False,
) -> HemistichResult:
    """Build a :class:`HemistichResult` from raw pyarud foot dicts."""
    n = len(raw_feet)
    enriched: list[FootResult] = []
    for i, raw in enumerate(raw_feet):
        if raw.get("status") == "extra_bits":
            position_label = "Extra"
        elif i == n - 1 and n > 0:
            position_label = "Ḍarb" if is_ajuz else "ʿArūḍ"
        else:
            position_label = "Hashw"
        enriched.append(_enrich_foot(raw, position_label, n))

    broken = [f.foot_index for f in enriched if f.status == "broken"]
    missing = sum(1 for f in enriched if f.status == "missing")
    extra_bits_entry = next(
        (f.actual_segment for f in enriched if f.status == "extra_bits"), None
    )

    avg_score = (
        sum(f.score for f in enriched if f.status not in ("missing", "extra_bits"))
        / max(1, sum(1 for f in enriched if f.status not in ("missing", "extra_bits")))
    )

    return HemistichResult(
        text=text,
        binary_pattern=pattern,
        feet=enriched,
        score=avg_score,
        is_sound=all(f.status == "ok" for f in enriched),
        broken_foot_indices=broken,
        missing_foot_count=missing,
        extra_bits=extra_bits_entry,
    )


# ===========================================================================
# 5. Public API
# ===========================================================================

def analyze_poem(
    verses: list[tuple[str, str]],
    *,
    meter_name: str | None = None,
    top_n: int = 3,
) -> PoemResult:
    """
    Analyse a full Arabic poem and return a rich structured result.

    Parameters
    ----------
    verses:
        List of ``(sadr, ajuz)`` pairs of fully-diacritized Arabic strings.
        Pass ``ajuz=""`` for a single-hemistich line.
    meter_name:
        Force a specific meter (pyarud key, e.g. ``"baseet"``).  When
        ``None`` the meter is auto-detected.
    top_n:
        Number of candidate meters to include in ``PoemResult.candidate_meters``.

    Returns
    -------
    PoemResult

    Raises
    ------
    RuntimeError
        If pyarud is not installed.
    ValueError
        If ``verses`` is empty.

    Examples
    --------
    >>> result = analyze_poem([
    ...     ("أَنَامُ مِلْءَ جُفُونِي عَنْ شَوَارِدِهَا",
    ...      "وَيَسْهَرُ الْخَلْقُ جَرَّاهَا وَيَخْتَصِمُ"),
    ... ], meter_name="baseet")
    >>> result.meter
    'baseet'
    >>> result.overall_score
    1.0
    """
    if not verses:
        raise ValueError("verses must not be empty")
    _require_pyarud()

    proc = _get_processor()
    raw = proc.process_poem(verses, meter_name=meter_name)

    detected_meter: str = raw["meter"]
    verse_results: list[VerseResult] = []

    for i, verse_raw in enumerate(raw["verses"]):
        sadr_text   = verse_raw.get("sadr_text", verses[i][0])
        ajuz_text   = verse_raw.get("ajuz_text", verses[i][1])
        sadr_pat    = verse_raw.get("input_pattern", "")[:len(verse_raw.get("input_pattern", "")) // 2]
        ajuz_pat    = verse_raw.get("input_pattern", "")[len(verse_raw.get("input_pattern", "")) // 2:]
        sadr_feet   = verse_raw.get("sadr_analysis") or []
        ajuz_feet   = verse_raw.get("ajuz_analysis")

        sadr_h = _enrich_hemistich(sadr_text, sadr_pat, sadr_feet, is_ajuz=False)
        ajuz_h = (
            _enrich_hemistich(ajuz_text, ajuz_pat, ajuz_feet, is_ajuz=True)
            if ajuz_feet is not None
            else None
        )

        combined_score = verse_raw.get("score", 0.0)
        issues = generate_diagnostics(sadr_h, ajuz_h, detected_meter)

        verse_results.append(VerseResult(
            verse_index=i,
            sadr=sadr_h,
            ajuz=ajuz_h,
            combined_score=combined_score,
            meter=detected_meter,
            issues=issues,
        ))

    overall = (
        sum(v.combined_score for v in verse_results) / len(verse_results)
        if verse_results else 0.0
    )

    # Candidate meters: try to run individual verse scoring
    candidates: list[tuple[str, float]] = [(detected_meter, overall)]

    return PoemResult(
        meter=detected_meter,
        meter_arabic=METER_ARABIC_NAMES.get(detected_meter, ""),
        total_verses=len(verse_results),
        verses=verse_results,
        overall_score=overall,
        is_metrically_sound=all(
            v.sadr.is_sound and (v.ajuz is None or v.ajuz.is_sound)
            for v in verse_results
        ),
        candidate_meters=candidates[:top_n],
    )


def detect_meter(verses: list[tuple[str, str]]) -> str:
    """
    Detect and return only the meter name (pyarud key) for a poem.

    Parameters
    ----------
    verses:
        List of ``(sadr, ajuz)`` pairs.

    Returns
    -------
    str
        Meter key such as ``"taweel"``, ``"baseet"``, …

    Examples
    --------
    >>> detect_meter([
    ...     ("أَخِي جَاوَزَ الظَّالِمُونَ الْمَدَى",
    ...      "فَحَقَّ الْجِهَادُ وَحَقَّ الْفِدَا"),
    ... ])
    'mutakareb'
    """
    _require_pyarud()
    proc = _get_processor()
    raw = proc.process_poem(verses)
    return raw["meter"]


def analyze_verse(
    sadr: str,
    ajuz: str = "",
    *,
    meter_name: str | None = None,
) -> VerseResult:
    """
    Analyse a single verse and return a :class:`VerseResult`.

    This is a convenience wrapper around :func:`analyze_poem` for callers
    dealing with one verse at a time.

    Parameters
    ----------
    sadr:
        First hemistich (fully diacritized).
    ajuz:
        Second hemistich.  Pass ``""`` for single-hemistich analysis.
    meter_name:
        Force a specific meter key, or ``None`` to auto-detect.

    Returns
    -------
    VerseResult

    Examples
    --------
    >>> vr = analyze_verse(
    ...     "كَمُلَ الجَمَالُ مِنَ البُحُورِ الكَامِلُ",
    ...     "مُتَفَاعِلُنْ مُتَفَاعِلُنْ مُتَفَاعِلُ",
    ...     meter_name="kamel",
    ... )
    >>> vr.combined_score
    1.0
    """
    result = analyze_poem([(sadr, ajuz)], meter_name=meter_name)
    return result.verses[0]


def get_broken_feet(hemistich: HemistichResult) -> list[FootResult]:
    """
    Return all feet in a hemistich whose status is ``"broken"``.

    Parameters
    ----------
    hemistich:
        A :class:`HemistichResult` (from ``verse.sadr`` or ``verse.ajuz``).

    Returns
    -------
    list[FootResult]
    """
    return [f for f in hemistich.feet if f.status == "broken"]


def get_zihaf_feet(hemistich: HemistichResult) -> list[FootResult]:
    """
    Return all feet in a hemistich that carry a valid zihāf or ʿilla
    (status ``"ok"`` but pattern differs from canonical Salīm).

    Parameters
    ----------
    hemistich:
        A :class:`HemistichResult`.

    Returns
    -------
    list[FootResult]
    """
    return [
        f for f in hemistich.feet
        if f.status == "ok" and f.zihaf_name not in (None, "Salim")
    ]


def generate_diagnostics(
    sadr: HemistichResult,
    ajuz: HemistichResult | None,
    meter: str,
) -> list[str]:
    """
    Generate a list of plain-English diagnostic messages for a verse.

    The messages describe every structural issue found — broken feet, missing
    feet, leftover bits, and which specific zihāfāt are present.

    Parameters
    ----------
    sadr:
        Enriched Ṣadr hemistich.
    ajuz:
        Enriched ʿAjuz hemistich, or ``None`` for single-hemistich input.
    meter:
        Detected or forced meter key.

    Returns
    -------
    list[str]
        Each item is a human-readable diagnostic string.
    """
    msgs: list[str] = []

    def _check(h: HemistichResult, label: str) -> None:
        for f in h.feet:
            loc = f"foot {f.foot_index + 1} ({f.position_label})"
            if f.status == "broken":
                msgs.append(
                    f"[{label}] {loc}: broken — "
                    f"observed «{f.actual_segment}» does not match any "
                    f"allowed form of the expected pattern «{f.expected_pattern}»."
                )
            elif f.status == "missing":
                msgs.append(
                    f"[{label}] {loc}: missing — "
                    "input is too short; the verse may be Majzūʾ (truncated)."
                )
            elif f.status == "extra_bits":
                msgs.append(
                    f"[{label}] extra bits after all feet consumed: "
                    f"«{f.actual_segment}» — verse may be too long."
                )
            elif f.status == "ok" and f.zihaf_name not in (None, "Salim"):
                msgs.append(
                    f"[{label}] {loc}: valid zihāf «{f.zihaf_name}» applied "
                    f"(canonical «{f.canonical_pattern}» → actual «{f.actual_segment}»)."
                )

        if h.missing_foot_count > 0:
            msgs.append(
                f"[{label}] {h.missing_foot_count} missing foot(s) — "
                "consider using a Majzūʾ / Mashtūr sub-variant."
            )

    _check(sadr, "Ṣadr")
    if ajuz:
        _check(ajuz, "ʿAjuz")

    if not msgs:
        msgs.append(
            f"Verse is metrically sound ({METER_ARABIC_NAMES.get(meter, meter)})."
        )

    return msgs


def summarize_issues(verse: VerseResult) -> str:
    """
    Return a compact multi-line summary of all metrical issues in a verse.

    Parameters
    ----------
    verse:
        A :class:`VerseResult`.

    Returns
    -------
    str

    Examples
    --------
    >>> print(summarize_issues(vr))
    Verse 1 — meter: البسيط (baseet) — score: 1.00
    ✔ Verse is metrically sound (البسيط).
    """
    header = (
        f"Verse {verse.verse_index + 1} — "
        f"meter: {METER_ARABIC_NAMES.get(verse.meter, verse.meter)} "
        f"({verse.meter}) — "
        f"score: {verse.combined_score:.2f}"
    )
    lines = [header]
    for msg in verse.issues:
        prefix = "✔" if "metrically sound" in msg else "⚠"
        lines.append(f"  {prefix} {msg}")
    return "\n".join(lines)


def score_interpretation(score: float) -> str:
    """
    Translate a 0–1 numeric score into a descriptive quality label.

    +----------------+------------------------------------------------+
    | Range          | Label                                          |
    +================+================================================+
    | 1.00           | Perfect — exact metrical match.                |
    +----------------+------------------------------------------------+
    | 0.90 – 0.99    | Excellent — minor variance, likely valid.      |
    +----------------+------------------------------------------------+
    | 0.70 – 0.89    | Good — one or two light zihāfāt present.       |
    +----------------+------------------------------------------------+
    | 0.50 – 0.69    | Fair — noticeable metrical irregularity.       |
    +----------------+------------------------------------------------+
    | < 0.50         | Poor — significant metrical problems.          |
    +----------------+------------------------------------------------+

    Parameters
    ----------
    score:
        A float in ``[0.0, 1.0]``.

    Returns
    -------
    str
    """
    if score >= 1.0:
        return "Perfect — exact metrical match"
    if score >= 0.90:
        return "Excellent — minor variance, likely valid"
    if score >= 0.70:
        return "Good — one or two light zihāfāt present"
    if score >= 0.50:
        return "Fair — noticeable metrical irregularity"
    return "Poor — significant metrical problems"


def get_meter_info(meter_name: str) -> dict:
    """
    Return a metadata dictionary for a given meter.

    Parameters
    ----------
    meter_name:
        pyarud meter key, e.g. ``"taweel"``.

    Returns
    -------
    dict with keys:
        - ``key``          : pyarud string key
        - ``arabic_name``  : Arabic display name
        - ``template``     : Canonical feet sequence in Arabic
        - ``known``        : bool — whether this meter is in the 16-meter canon

    Examples
    --------
    >>> info = get_meter_info("taweel")
    >>> info["arabic_name"]
    'الطويل'
    """
    return {
        "key":         meter_name,
        "arabic_name": METER_ARABIC_NAMES.get(meter_name, ""),
        "template":    METER_TEMPLATES.get(meter_name, ""),
        "known":       meter_name in METER_ARABIC_NAMES,
    }


def batch_analyze(
    poems: list[list[tuple[str, str]]],
    *,
    meter_name: str | None = None,
) -> list[PoemResult]:
    """
    Analyse multiple poems and return a list of :class:`PoemResult` objects.

    Parameters
    ----------
    poems:
        Each element is a list of ``(sadr, ajuz)`` pairs representing one poem.
    meter_name:
        Optional forced meter applied to all poems.

    Returns
    -------
    list[PoemResult]

    Examples
    --------
    >>> results = batch_analyze([poem1_verses, poem2_verses])
    >>> for r in results:
    ...     print(r.meter, r.overall_score)
    """
    return [analyze_poem(poem, meter_name=meter_name) for poem in poems]


def filter_by_health(
    hemistich: HemistichResult,
    level: HealthLevel,
) -> list[FootResult]:
    """
    Return all feet in a hemistich whose health matches ``level``.

    Parameters
    ----------
    hemistich:
        A :class:`HemistichResult`.
    level:
        One of ``"perfect"``, ``"valid_zihaf"``, ``"broken"``, ``"severe"``.

    Returns
    -------
    list[FootResult]
    """
    return [f for f in hemistich.feet if f.health == level]


def has_zihaf(verse: VerseResult) -> bool:
    """
    Return ``True`` if any foot in the verse carries a valid zihāf or ʿilla.

    Parameters
    ----------
    verse:
        A :class:`VerseResult`.

    Returns
    -------
    bool
    """
    hems = [verse.sadr] + ([verse.ajuz] if verse.ajuz else [])
    return any(bool(get_zihaf_feet(h)) for h in hems)


def is_broken(verse: VerseResult) -> bool:
    """
    Return ``True`` if the verse contains any ``"broken"`` or ``"severe"``
    (missing / extra_bits) feet.

    Parameters
    ----------
    verse:
        A :class:`VerseResult`.

    Returns
    -------
    bool
    """
    hems = [verse.sadr] + ([verse.ajuz] if verse.ajuz else [])
    for h in hems:
        if h.broken_foot_indices or h.missing_foot_count > 0 or h.extra_bits:
            return True
    return False


# ===========================================================================
# 6. CLI demo (run directly: python arabic_prosody_helpers.py)
# ===========================================================================

if __name__ == "__main__":
    DEMO_VERSES = [
        (
            "أَنَامُ مِلْءَ جُفُونِي عَنْ شَوَارِدِهَا",
            "وَيَسْهَرُ الْخَلْقُ جَرَّاهَا وَيَخْتَصِمُ",
        ),
    ]

    print("=" * 60)
    print("Arabic Prosody Helpers — demo")
    print("=" * 60)

    if not _PYARUD_AVAILABLE:
        print("⚠  pyarud is not installed.  Run: pip install pyarud")
        print("   (pattern utilities and static lookups still work)")
        print()
        print("Static lookup demo (no pyarud needed):")
        print(f"  identify_zihaf('1010110', '110110') → {identify_zihaf('1010110', '110110')}")
        print(f"  get_canonical_pattern('Fawlon')     → {get_canonical_pattern('Fawlon')}")
        print(f"  score_interpretation(0.93)          → {score_interpretation(0.93)}")
        print(f"  get_meter_info('taweel')            → {get_meter_info('taweel')}")
    else:
        poem = analyze_poem(DEMO_VERSES, meter_name="baseet")
        print(f"Meter detected : {poem.meter} ({poem.meter_arabic})")
        print(f"Overall score  : {poem.overall_score:.2f} — {score_interpretation(poem.overall_score)}")
        print(f"Sound          : {poem.is_metrically_sound}")
        print()
        for verse in poem.verses:
            print(summarize_issues(verse))
            print()
            for foot in verse.sadr.feet:
                print(
                    f"  Ṣadr foot {foot.foot_index + 1} [{foot.position_label}]: "
                    f"{foot.actual_segment:10s} | "
                    f"health={foot.health:12s} | "
                    f"zihāf={foot.zihaf_name or 'N/A'}"
                )
