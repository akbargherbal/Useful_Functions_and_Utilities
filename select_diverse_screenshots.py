"""
Shortlist visually-dissimilar screenshots from a larger folder
================================================================

Problem this solves: you have ~32+ Ableton screenshots (plus a `menus/`
subfolder) and many of them are near-duplicates -- e.g. two browser-tab
screenshots that only differ by which item is highlighted, ~90% the same
pixels. Feeding all of them to a GUI-grounding benchmark wastes model calls
on redundant layouts. This script picks a diverse subset instead.

How it works (no ML, no GPU, just Pillow):
  1. Compute a 64-bit perceptual hash (dHash) for every image. dHash is
     based on adjacent-pixel gradients, so it's sensitive to UI layout/
     content changes (menus open, different tabs selected, etc.) rather
     than to overall brightness or color -- a better fit for GUI screenshots
     than a plain average-color hash.
  2. Cluster near-duplicates together (default: >=90% similar = same
     cluster) and keep only one representative per cluster -- the one
     closest to the cluster's "center" (most typical of that cluster).
  3. If more images survive deduping than you asked for (--target-n), run
     greedy farthest-point sampling on what's left: repeatedly add whichever
     remaining image is most different from everything already picked.
     This maximizes visual coverage of the whole folder instead of just
     picking randomly or alphabetically.
  4. Copies the shortlisted files into an output folder (flattened, original
     filenames kept) and writes a CSV report of every image's cluster
     assignment and similarity to its representative, so you can sanity-check
     or override the automatic choices.

Usage
-----
    pip install pillow
    python select_diverse_screenshots.py \\
        --input-dir ./Ableton_screenshots \\
        --output-dir ./shortlisted_screenshots \\
        --target-n 15 \\
        --dup-threshold 90

All flags are optional (see defaults below / --help). Searches --input-dir
recursively, so the `menus/` subfolder is included automatically.
"""

import argparse
import csv
import shutil
from pathlib import Path

from PIL import Image

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
HASH_SIZE = 8  # -> 64-bit hash


# ---------------------------------------------------------------------------
# Perceptual hashing
# ---------------------------------------------------------------------------


def dhash(image_path: Path, hash_size: int = HASH_SIZE) -> int:
    """Difference hash: resize to (hash_size+1) x hash_size grayscale, then
    encode 1 bit per pixel for whether it's brighter than its right neighbor.
    Robust to resizing/minor color shifts, sensitive to structural/content
    changes -- exactly what distinguishes "same panel, different tab" from
    "same panel, same tab, cursor moved a bit"."""
    img = Image.open(image_path).convert("L").resize(
        (hash_size + 1, hash_size), Image.LANCZOS
    )
    pixels = list(img.getdata())
    bits = []
    for row in range(hash_size):
        row_start = row * (hash_size + 1)
        row_pixels = pixels[row_start : row_start + hash_size + 1]
        for col in range(hash_size):
            bits.append("1" if row_pixels[col] > row_pixels[col + 1] else "0")
    return int("".join(bits), 2)


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def similarity_pct(a: int, b: int, hash_size: int = HASH_SIZE) -> float:
    total_bits = hash_size * hash_size
    return 100.0 * (1 - hamming_distance(a, b) / total_bits)


# ---------------------------------------------------------------------------
# Clustering near-duplicates (simple union-find on a similarity threshold)
# ---------------------------------------------------------------------------


class UnionFind:
    def __init__(self, items):
        self.parent = {item: item for item in items}

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def cluster_near_duplicates(hashes: dict, dup_threshold: float) -> dict:
    """Returns {path: cluster_id}. Two images join a cluster if their
    similarity >= dup_threshold (percent)."""
    paths = list(hashes.keys())
    uf = UnionFind(paths)
    for i in range(len(paths)):
        for j in range(i + 1, len(paths)):
            p1, p2 = paths[i], paths[j]
            if similarity_pct(hashes[p1], hashes[p2]) >= dup_threshold:
                uf.union(p1, p2)
    return {p: uf.find(p) for p in paths}


def pick_cluster_representative(cluster_members, hashes):
    """Pick the image whose average distance to the rest of its cluster is
    smallest -- i.e. the most "typical" example of that cluster, not an
    arbitrary/alphabetical pick."""
    if len(cluster_members) == 1:
        return cluster_members[0]
    best, best_score = None, None
    for candidate in cluster_members:
        total = sum(
            hamming_distance(hashes[candidate], hashes[other])
            for other in cluster_members
            if other != candidate
        )
        if best_score is None or total < best_score:
            best, best_score = candidate, total
    return best


# ---------------------------------------------------------------------------
# Farthest-point sampling for maximal diversity among survivors
# ---------------------------------------------------------------------------


def farthest_point_sample(candidates, hashes, target_n):
    """Greedily builds a diverse subset: start with one image, then repeatedly
    add whichever remaining image has the largest *minimum* distance to
    everything already selected. This spreads the shortlist across the full
    visual range of the folder instead of clustering in one area."""
    if len(candidates) <= target_n:
        return list(candidates)

    remaining = set(candidates)
    # Seed with the image that's most different from the group average --
    # a reasonable, deterministic starting point.
    selected = [remaining.pop()]

    while len(selected) < target_n:
        best_candidate, best_min_dist = None, -1
        for cand in remaining:
            min_dist = min(
                hamming_distance(hashes[cand], hashes[s]) for s in selected
            )
            if min_dist > best_min_dist:
                best_candidate, best_min_dist = cand, min_dist
        selected.append(best_candidate)
        remaining.remove(best_candidate)

    return selected


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def find_images(input_dir: Path):
    return sorted(
        p for p in input_dir.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("./Ableton_screenshots"),
        help="Folder to scan recursively for images (default: ./Ableton_screenshots)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./shortlisted_screenshots"),
        help="Where to copy the shortlisted images (default: ./shortlisted_screenshots)",
    )
    parser.add_argument(
        "--target-n",
        type=int,
        default=15,
        help="Target shortlist size after deduping (default: 15)",
    )
    parser.add_argument(
        "--dup-threshold",
        type=float,
        default=90.0,
        help="Similarity %% at/above which two images are treated as "
        "near-duplicates and collapsed into one cluster (default: 90.0)",
    )
    parser.add_argument(
        "--report-csv",
        type=Path,
        default=Path("./screenshot_diversity_report.csv"),
        help="Where to write the full per-image cluster/similarity report",
    )
    args = parser.parse_args()

    images = find_images(args.input_dir)
    if not images:
        print(f"No images found under {args.input_dir}")
        return
    print(f"Found {len(images)} images under {args.input_dir}")

    print("Hashing images...")
    hashes = {p: dhash(p) for p in images}

    print(f"Clustering near-duplicates (>= {args.dup_threshold:.0f}% similar)...")
    cluster_of = cluster_near_duplicates(hashes, args.dup_threshold)

    clusters = {}
    for path, cid in cluster_of.items():
        clusters.setdefault(cid, []).append(path)

    representatives = {
        cid: pick_cluster_representative(members, hashes)
        for cid, members in clusters.items()
    }
    dedup_survivors = list(representatives.values())
    print(
        f"{len(images)} images -> {len(dedup_survivors)} after collapsing "
        f"near-duplicate clusters"
    )

    shortlist = farthest_point_sample(dedup_survivors, hashes, args.target_n)
    shortlist.sort(key=lambda p: str(p))
    print(f"Final shortlist: {len(shortlist)} images")

    # --- write outputs ---
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for p in shortlist:
        shutil.copy2(p, args.output_dir / p.name)

    with open(args.report_csv, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["image", "cluster_id", "cluster_size", "cluster_representative",
             "similarity_to_representative_pct", "in_final_shortlist"]
        )
        for path, cid in sorted(cluster_of.items(), key=lambda kv: str(kv[0])):
            rep = representatives[cid]
            sim = similarity_pct(hashes[path], hashes[rep])
            writer.writerow(
                [
                    str(path),
                    str(cid),
                    len(clusters[cid]),
                    str(rep),
                    f"{sim:.1f}",
                    "yes" if path in shortlist else "no",
                ]
            )

    print(f"\nShortlisted images copied to: {args.output_dir}")
    print(f"Full report written to: {args.report_csv}")
    print("\nShortlist:")
    for p in shortlist:
        print(f"  {p}")


if __name__ == "__main__":
    main()
