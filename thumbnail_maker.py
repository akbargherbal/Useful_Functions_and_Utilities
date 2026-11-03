#!/usr/bin/env python3

"""
Generate one video contact sheet per video.

Requires: opencv-python, Pillow>=9.1 (Pillow>=10.1 for scalable default font).
Optional: ffprobe (from FFmpeg) on PATH for accurate durations.

Usage:
    python thumbnail_maker.py
    python thumbnail_maker.py --input vid_folder --output thumb_folder
    python thumbnail_maker.py --cols 6 --rows 6
    python thumbnail_maker.py --recursive
    python thumbnail_maker.py --overwrite
    python thumbnail_maker.py --letterbox
    python thumbnail_maker.py --include-ts
"""

import argparse
import logging
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".wmv",
    ".flv",
    ".webm",
    ".m4v",
    ".mpg",
    ".mpeg",
    ".3gp",
}

# ".ts" is also TypeScript, so it is opt-in via --include-ts.
TS_EXTENSION = ".ts"

FONT_SIZE = 16
BACKGROUND = (25, 25, 25)
TEXT_COLOR = (230, 230, 230)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Generate thumbnail contact sheets for videos."
    )

    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=Path("vid_folder"),
        help="Input video folder (default: vid_folder)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("thumb_folder"),
        help="Output folder (default: thumb_folder)",
    )

    parser.add_argument("--cols", type=int, default=5, help="Columns (default: 5)")
    parser.add_argument("--rows", type=int, default=5, help="Rows (default: 5)")

    parser.add_argument("--width", type=int, default=320, help="Thumbnail width")
    parser.add_argument("--height", type=int, default=180, help="Thumbnail height")

    parser.add_argument(
        "--quality", type=int, default=90, help="JPEG quality, 1-95 (default: 90)"
    )

    parser.add_argument(
        "--letterbox",
        action="store_true",
        help="Pad frames to fit instead of cropping them",
    )

    parser.add_argument(
        "--include-ts",
        action="store_true",
        help="Also treat .ts files as video (off by default: TypeScript clash)",
    )

    parser.add_argument(
        "-r", "--recursive", action="store_true", help="Search input folder recursively"
    )

    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing contact sheets"
    )

    parser.add_argument(
        "--log-file", type=Path, default=None, help="Optional log file path"
    )

    parser.add_argument(
        "--debug", action="store_true", help="Debug logging with full tracebacks"
    )

    return parser


def parse_args():
    parser = build_parser()
    args = parser.parse_args()

    if args.cols < 1 or args.rows < 1:
        parser.error("rows and columns must be positive.")
    if args.width < 1 or args.height < 1:
        parser.error("thumbnail dimensions must be positive.")
    if not 1 <= args.quality <= 95:
        parser.error("quality must be between 1 and 95.")

    return args


def setup_logging(log_file=None, debug=False):
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )


def get_videos(input_dir, recursive=False, include_ts=False):
    extensions = set(VIDEO_EXTENSIONS)
    if include_ts:
        extensions.add(TS_EXTENSION)

    iterator = input_dir.rglob("*") if recursive else input_dir.iterdir()

    return sorted(
        (p for p in iterator if p.is_file() and p.suffix.lower() in extensions),
        key=lambda p: str(p).lower(),
    )


def load_font(size=FONT_SIZE):
    """Load a readable font, falling back gracefully."""
    for name in ("DejaVuSans.ttf", "Arial.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue

    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1
    except TypeError:
        return ImageFont.load_default()


def probe_duration(video_path):
    """Return container duration in seconds via ffprobe, or None."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return None

    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        value = float(result.stdout.strip())
    except (subprocess.SubprocessError, ValueError, OSError):
        return None

    return value if math.isfinite(value) and value > 0 else None


def format_time(seconds):
    seconds = int(seconds)
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)

    if hours:
        return f"{hours:d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def truncate_text(draw, text, font, max_width):
    if draw.textlength(text, font=font) <= max_width:
        return text

    while text and draw.textlength(text + "...", font=font) > max_width:
        text = text[:-1]

    return text + "..."


def extract_frame(cap, frame_index, fps):
    """
    Extract the frame at frame_index.

    Returns (PIL image, actual time in seconds) or None. The time is derived
    from the position the decoder actually landed on, not the requested one.
    """
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
    success, frame = cap.read()

    if not success or frame is None:
        return None

    # After read(), POS_FRAMES points at the *next* frame.
    actual_index = max(cap.get(cv2.CAP_PROP_POS_FRAMES) - 1, 0)
    actual_seconds = actual_index / fps

    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame), actual_seconds


def fit_frame(frame, size, letterbox):
    if letterbox:
        return ImageOps.pad(
            frame, size, method=Image.Resampling.LANCZOS, color=(0, 0, 0)
        )
    return ImageOps.fit(frame, size, method=Image.Resampling.LANCZOS)


def save_atomically(sheet, output_path, quality):
    """Save to a temp file, then move into place. Respects the umask."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=".jpg",
            prefix=".contact_sheet_",
            dir=output_path.parent,
            delete=False,
        ) as temp:
            temp_path = Path(temp.name)

        sheet.save(temp_path, format="JPEG", quality=quality, optimize=True)

        # NamedTemporaryFile creates 0600 files; match a normal save instead.
        umask = os.umask(0)
        os.umask(umask)
        try:
            os.chmod(temp_path, 0o666 & ~umask)
        except OSError:
            pass

        temp_path.replace(output_path)

    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink()


def make_contact_sheet(video_path, output_path, args):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError("Could not open video")

    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # `not (x > 0)` also rejects NaN, which `x <= 0` does not.
        if not (fps > 0):
            raise RuntimeError("Invalid frame rate")

        probed = probe_duration(video_path)

        if not (total_frames > 0):
            if probed is None:
                raise RuntimeError("Invalid frame count and no ffprobe duration")
            total_frames = probed * fps

        total_frames = int(total_frames)
        duration = probed if probed is not None else total_frames / fps

        if not (duration > 0):
            raise RuntimeError("Video has zero duration")

        max_frame = max(int(duration * fps) - 1, 0)
        max_frame = min(max_frame, max(total_frames - 1, 0))

        total_slots = args.cols * args.rows

        # Sample evenly throughout the video, at the middle of each slot.
        frame_indices = [
            min(int(duration * (i + 0.5) / total_slots * fps), max_frame)
            for i in range(total_slots)
        ]

        font = load_font()

        padding = 10
        label_height = FONT_SIZE + 10
        header_height = 2 * FONT_SIZE + 24

        cell_width = args.width
        cell_height = args.height + label_height

        sheet_width = args.cols * cell_width + (args.cols + 1) * padding
        sheet_height = (
            header_height + args.rows * cell_height + (args.rows + 1) * padding
        )

        sheet = Image.new("RGB", (sheet_width, sheet_height), BACKGROUND)
        draw = ImageDraw.Draw(sheet)

        # Header: filename and metadata.
        title = truncate_text(draw, video_path.name, font, sheet_width - 2 * padding)
        info = f"Duration {format_time(duration)}  |  {video_w}x{video_h}  |  {fps:.2f} fps"
        draw.text((padding, padding), title, fill=TEXT_COLOR, font=font)
        draw.text(
            (padding, padding + FONT_SIZE + 6), info, fill=TEXT_COLOR, font=font
        )

        extracted = 0

        for index, frame_index in enumerate(frame_indices):
            try:
                result = extract_frame(cap, frame_index, fps)

                if result is None:
                    logging.warning(
                        "%s: Could not extract frame %d (%.1fs)",
                        video_path.name,
                        frame_index,
                        frame_index / fps,
                    )
                    continue

                frame, actual_seconds = result

                thumbnail = fit_frame(frame, (args.width, args.height), args.letterbox)

                col = index % args.cols
                row = index // args.cols

                x = padding + col * (cell_width + padding)
                y = header_height + padding + row * (cell_height + padding)

                sheet.paste(thumbnail, (x, y))

                draw.text(
                    (x + 2, y + args.height + 3),
                    format_time(actual_seconds),
                    fill=TEXT_COLOR,
                    font=font,
                )

                extracted += 1

            except Exception as exc:
                if args.debug:
                    logging.exception(
                        "%s: Error extracting frame %d", video_path.name, index
                    )
                else:
                    logging.error(
                        "%s: Error extracting frame %d | %s",
                        video_path.name,
                        index,
                        exc,
                    )

        if extracted == 0:
            raise RuntimeError("No frames could be extracted")

        save_atomically(sheet, output_path, args.quality)

        return extracted, total_slots, duration

    finally:
        cap.release()


def main():
    args = parse_args()

    setup_logging(args.log_file, args.debug)

    if not args.input.is_dir():
        logging.error("Input directory does not exist: %s", args.input)
        return 2

    args.output.mkdir(parents=True, exist_ok=True)

    videos = get_videos(args.input, args.recursive, args.include_ts)

    if not videos:
        logging.warning("No videos found in %s", args.input)
        return 0

    logging.info("Found %d video(s)", len(videos))

    successful = 0
    failed = 0
    skipped = 0

    # Track output filenames to prevent collisions (e.g. clip.mp4 + clip.mkv).
    used_outputs = set()

    for index, video in enumerate(videos, 1):
        # Preserve subfolder structure when using --recursive.
        if args.recursive:
            relative = video.relative_to(args.input)
            output_dir = args.output / relative.parent
        else:
            output_dir = args.output

        output_path = output_dir / f"{video.stem}.jpg"

        logging.info("[%d/%d] Processing: %s", index, len(videos), video)

        try:
            # normcase lowercases only on case-insensitive platforms (Windows).
            output_key = os.path.normcase(str(output_path.resolve()))

            if output_key in used_outputs:
                raise RuntimeError(f"Output filename collision: {output_path}")

            used_outputs.add(output_key)

            if output_path.exists() and not args.overwrite:
                logging.info("Skipping existing: %s", output_path)
                skipped += 1
                continue

            extracted, total, duration = make_contact_sheet(video, output_path, args)

            logging.info(
                "SUCCESS: %s | %d/%d frames | %.1f seconds | %s",
                video.name,
                extracted,
                total,
                duration,
                output_path,
            )

            successful += 1

        except Exception as exc:
            failed += 1

            if args.debug:
                logging.exception("FAILED: %s", video)
            else:
                logging.error("FAILED: %s | %s", video, exc)

            # Continue with the next video.

    logging.info("=" * 60)
    logging.info("PROCESSING COMPLETE")
    logging.info("Total:     %d", len(videos))
    logging.info("Succeeded: %d", successful)
    logging.info("Skipped:   %d", skipped)
    logging.info("Failed:    %d", failed)
    logging.info("=" * 60)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
