# Session 2 Handover — IQAA-BENCH
**Date:** 2026-04-30
**Session type:** Phase 1 — Script adaptation + smoke test (Phase 1 complete and confirmed)

---

## 1. What We Did

- Read and confirmed all session context: `CLIENT_BRIEF.md`, phased plan, `music_caption.py`, `Music_Captioning.md`, and library version output
- Identified two directory/path discrepancies between the git repo and Colab — resolved: Colab uses a flat structure (`./downloads/`, `./test_one/`, `./music_caption.py` at root); the local Windows repo at `C:\Users\DELL\Jupyter_Notebooks\iqaa-bench` uses `DATA/downloads/` — irrelevant to Colab execution
- Identified a filename format discrepancy not captured in Session 1: actual MP3 filenames carry a numeric prefix (`01 - Ayub...`) and use a Unicode fraction slash `⧸` (U+2044) instead of `/`; the Phase 3 ground truth parser must account for both
- Confirmed `transformers 5.0.0` — `AudioFlamingo3ForConditionalGeneration` import **confirmed working**
- Wrote the Phase 1 adapted script: added `--mode eval` with 4 evaluation prompts, single 22s start window, and clean mode branching; zero changes to `quick` and `detailed` paths
- **Ran the smoke test on Colab T4 — succeeded cleanly. Phase 1 done.**

---

## 2. Artefacts Produced

| File | Role |
|---|---|
| `music_caption.py` (modified) | Phase 1 deliverable — adds `--mode eval`; confirmed working on Colab T4 |
| `test_one/36 - Maqsum (4⧸4) (100bpm).json` | Phase 1 smoke test output — schema confirmed |
| `test_one/caption_audio_20260430_095650.log` | Smoke test log |
| GCS backup | All results synced to `gs://akbar-december-2024-backup/IQAA_BENCH_RESULTS/` |

---

## 3. Key Numbers

| Item | Value |
|---|---|
| Changes to `music_caption.py` | 4 (PROMPTS_EVAL dict, select_eval_chunk fn, process_file branch, CLI choices) |
| Eval mode inference calls per track | 4 |
| Eval mode inference calls — 18-track pilot | 72 |
| Eval mode inference calls — full 50-track run | 200 |
| Eval window duration | 22s from track start |
| OOM events this session | 0 |
| Model load time | ~75s (09:57:04 → 09:58:19) |
| Inference time for 4 prompts × 1 track | ~14s (09:58:20 → 09:58:34) |

---

## 4. Smoke Test Output — Maqsum 100bpm

```
[DESCRIPTION]    Complex, interlocking rhythmic patterns; high rhythmic density;
                 intricate percussive textures; driving, energetic pulse
[STRUCTURAL]     The beats per minute for this music is 100.0
[RHYTHMIC_IDENTITY]  Maqsum, doum on beat 1, tek on beat 3, doum-tek syncopation, 4/4 cycle
[TIMBRAL_CULTURAL]   darbuka with crisp tek, riq with finger rolls,
                     Arabic folkloric style, urban ensemble feel
```

**Quality notes (for Phase 3 scorer design):**
- `rhythmic_identity` nailed Maqsum perfectly — name, stroke pattern, and cycle all correct. Tier 1 candidate.
- `timbral_cultural` accurate and specific — darbuka + riq named correctly, regional style correct. Tier 1 candidate.
- `description` was vague and generic — no rhythm name, no structural content. Tier 3 candidate.
- `structural` **format problem** — returned prose ("The beats per minute for this music is 100.0") instead of compact tags; BPM correct but **time signature entirely absent**. The Phase 3 Claude judge must parse prose BPM values, not just tag-format numbers. Rule-based time-sig scoring will score this as a miss.

---

## 5. Current Project State

| Script | State |
|---|---|
| `music_caption.py` | Phase 1 complete. **Confirmed working on Colab T4. No OOM. No import errors.** |
| `score_results.py` | Does not exist — Phase 3 deliverable |

Active phase: **Phase 1 complete ✅ — ready to proceed to Phase 2 (18-track pilot).**

---

## 6. Next Session Work Items

1. Attach `music_caption.py` and this handover to the new session
2. Build the 18-track pilot directory from `./downloads/` (see track list below)
3. Run the 18-track pilot command
4. Paste resulting JSONs (or a representative sample) and last 30 lines of log
5. If no OOM → Phase 2 done; proceed to Phase 3 (scoring pipeline)
6. If OOM → `nvidia-smi | head -5` and ZAP before adjusting anything

**18-track pilot list:**

*Breadth — one per rhythm at 100bpm (11 tracks):*
02, 07, 12, 16, 21, 26, 31, 36, 41, 44, 49

*Consistency — all Maqsum tempo variants (4 tracks):*
35, 36, 37, 38

*Robustness — one Jam per time-sig group (3 tracks):*
05 (Ayub, 2/4), 10 (Baladi, 4/4), 19 (Çiftetelli, 8/4)

**Pilot run commands:**
```bash
mkdir ./pilot_18
# Copy the 18 files by their numeric prefix — adjust if filenames differ
for n in 02 07 12 16 21 26 31 36 41 44 49 35 37 38 05 10 19; do
    cp ./downloads/${n}\ -\ *.mp3 ./pilot_18/ 2>/dev/null || echo "MISSING: $n"
done
ls ./pilot_18/ | wc -l   # must print 18 before proceeding

python music_caption.py --dir ./pilot_18 --mode eval --window-seconds 22
```

---

## 7. Known Issues / Watch Points

- **`structural` prompt format problem** — model returns prose BPM, omits time signature. Do not change the prompt before Phase 2 (need more data). Phase 3 scorer must handle prose BPM via regex and treat missing time signature as a scoring miss, not a parse error
- **200-call full-run estimate** — if client wants to stay within 50–100 call budget, collapse `rhythmic_identity` + `timbral_cultural` into one prompt and `description` + `structural` into one prompt (2 calls/track × 50 = 100). Hold this option until Phase 2 output quality is assessed
- **Masmoudi / Wahda / Bolero gaps** — confirmed playlist limitations; scorer must not treat missing variants as failures; no action needed until Phase 3
- **Colab flat path structure** — Colab root is flat (`./downloads/`, `./test_one/`). The local Windows repo uses `DATA/downloads/`. All Colab commands use the flat paths. Do not confuse the two
- **GCS backup** — results synced to `gs://akbar-december-2024-backup/IQAA_BENCH_RESULTS/` after the smoke test; sync again after Phase 2

---

## Session Handover Protocol

> **This section is the standing protocol for all future sessions. Do not remove it from the phased plan or from any handover document — always include it as a standard format.**

At the end of every session — whether a full phase is complete or not — produce a `Session_N_Handover.md` file before closing. The file must fit on one page and cover:

1. **What we did** — tasks completed, files changed, key decisions made
2. **Artefacts produced** — table of new/modified files and their role
3. **Key numbers** — inference call counts, OOM events, track counts processed, scored, failed
4. **Current project state** — which phase is active, what is the last confirmed working state of each script
5. **Next session work items** — ordered list, first command to run
6. **Known issues / watch points** — anything fragile, deferred, or asymmetric

**Rules:**

- One page. If it runs longer, cut prose, not coverage. Do not count this protocol block toward the page limit — always include it in full.
- Produce the handover even if the session ended early or a phase was abandoned mid-way — document what was attempted and what state the codebase is in.
- The handover replaces memory. Write it as if handing off to someone who has never seen the project — but who has access to the `CLIENT_BRIEF.md` and the phased plan.
- File naming: `Session_N_Handover.md` where N increments per session, not per phase. Multiple sessions may cover the same phase.
- Keep all handover files in the project root alongside the source files.
- The incoming LLM for the next session must read the latest `Session_N_Handover.md` and the phased plan before doing anything else. If neither is attached, invoke ZAP: ask for them explicitly before proceeding.
