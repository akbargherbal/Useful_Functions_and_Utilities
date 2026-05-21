import yt_dlp
import os
import re
import sys
import json
import signal
import logging
import click
from datetime import datetime


# ─────────────────────────────────────────────
#  Globals (used by signal handler)
# ─────────────────────────────────────────────
_logger: logging.Logger | None = None
_manifest_path: str | None = None
_manifest: dict = {}
_start_time: datetime | None = None
_interrupted = False


# ─────────────────────────────────────────────
#  1. LOGGER SETUP
# ─────────────────────────────────────────────
def setup_logger(output_folder: str) -> tuple[logging.Logger, str]:
    """Sets up a logger that writes to both the console and a timestamped log file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(output_folder, f"DOWNLOAD_LOG_{timestamp}.txt")

    logger = logging.getLogger("yt_dlp_logger")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers if called again
    if logger.handlers:
        logger.handlers.clear()

    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(console_handler)

    return logger, log_filename


# ─────────────────────────────────────────────
#  2. JSON MANIFEST
# ─────────────────────────────────────────────
def load_manifest(manifest_path: str) -> dict:
    """Loads an existing manifest or returns a fresh one."""
    if os.path.exists(manifest_path):
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"runs": [], "items": {}}


def save_manifest(manifest_path: str, manifest: dict) -> None:
    """Saves the manifest to disk."""
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def update_item(video_id: str, status: str, title: str = "", filepath: str = "", error: str = "") -> None:
    """Updates a single item entry in the in-memory manifest and persists it."""
    global _manifest, _manifest_path
    _manifest["items"][video_id] = {
        "title": title,
        "video_id": video_id,
        "status": status,           # "success" | "failed" | "skipped"
        "filepath": filepath,
        "error": error,
        "timestamp": datetime.now().isoformat(),
    }
    if _manifest_path:
        save_manifest(_manifest_path, _manifest)


# ─────────────────────────────────────────────
#  3. FRESH-START PROMPT
# ─────────────────────────────────────────────
def ask_fresh_start(archive_path: str, manifest_path: str, output_folder: str) -> bool:
    """
    If prior download data exists, asks the user whether to resume or start fresh.
    Returns True if the user wants a fresh start (overwrite), False to resume.
    """
    if not os.path.exists(archive_path) and not os.path.exists(manifest_path):
        return False  # Nothing to resume from — start fresh silently

    prior_manifest = load_manifest(manifest_path)
    successes = sum(1 for v in prior_manifest["items"].values() if v["status"] == "success")
    total = len(prior_manifest["items"])

    click.echo("\n" + "─" * 55)
    click.echo(f"  Prior download session detected in: {output_folder}/")
    click.echo(f"  {successes} succeeded, {total - successes} failed/other out of {total} tracked.")
    click.echo("─" * 55)
    click.echo("  [R] Resume    — skip already-downloaded files (default)")
    click.echo("  [O] Overwrite — delete history and start from scratch")
    click.echo("─" * 55)

    choice = click.prompt(
        "  Your choice",
        type=click.Choice(["R", "r", "O", "o"], case_sensitive=False),
        default="R",
        show_default=True,
        show_choices=False,
    ).lower()

    if choice == "o":
        if click.confirm("  This will delete the download archive and manifest. Are you sure?", default=False):
            for path in [archive_path, manifest_path]:
                if os.path.exists(path):
                    os.remove(path)
            click.echo("\n  History cleared — starting fresh.\n")
            return True
        else:
            click.echo("  Cancelled — resuming instead.\n")

    click.echo("\n  Resuming — already-downloaded files will be skipped.\n")
    return False


# ─────────────────────────────────────────────
#  4. yt-dlp HOOKS (for manifest tracking)
# ─────────────────────────────────────────────
def make_hooks(logger: logging.Logger) -> dict:
    """Returns yt-dlp hooks that update the manifest on download events."""

    def progress_hook(d: dict) -> None:
        if d["status"] == "finished":
            info = d.get("info_dict", {})
            video_id = info.get("id", "unknown")
            title = info.get("title", "Unknown Title")
            filepath = d.get("filename", "")
            logger.info(f"  Finished: {title}")
            update_item(video_id, "success", title, filepath)

        elif d["status"] == "error":
            info = d.get("info_dict", {})
            video_id = info.get("id", "unknown")
            title = info.get("title", "Unknown Title")
            logger.warning(f"  Failed:   {title}")
            update_item(video_id, "failed", title, error="Download error reported by yt-dlp")

    def postprocessor_hook(d: dict) -> None:
        if d["status"] == "finished":
            info = d.get("info_dict", {})
            video_id = info.get("id", "unknown")
            if video_id in _manifest.get("items", {}):
                # Update filepath to the final converted MP3
                _manifest["items"][video_id]["filepath"] = d.get("filepath", "")
                if _manifest_path:
                    save_manifest(_manifest_path, _manifest)

    return {
        "progress_hooks": [progress_hook],
        "postprocessor_hooks": [postprocessor_hook],
    }


# ─────────────────────────────────────────────
#  5. SIGNAL HANDLER — graceful Ctrl+C
# ─────────────────────────────────────────────
def setup_signal_handler() -> None:
    """Registers a SIGINT handler so Ctrl+C prints a summary instead of crashing."""
    def handle_interrupt(sig, frame):
        global _interrupted
        _interrupted = True
        click.echo("\n\n  Interrupted! Finishing current file then stopping...\n")

    signal.signal(signal.SIGINT, handle_interrupt)


# ─────────────────────────────────────────────
#  6. PROGRESS SUMMARY
# ─────────────────────────────────────────────
def print_summary(manifest: dict, start_time: datetime, logger: logging.Logger) -> None:
    """Prints and logs a formatted summary of the download session."""
    items = manifest.get("items", {})
    successes = [v for v in items.values() if v["status"] == "success"]
    failures  = [v for v in items.values() if v["status"] == "failed"]
    skipped   = [v for v in items.values() if v["status"] == "skipped"]
    elapsed   = datetime.now() - start_time
    mins, secs = divmod(int(elapsed.total_seconds()), 60)

    lines = [
        "",
        "=" * 55,
        "  DOWNLOAD SUMMARY",
        "=" * 55,
        f"  Succeeded : {len(successes)}",
        f"  Failed    : {len(failures)}",
        f"  Skipped   : {len(skipped)}",
        f"  Total     : {len(items)}",
        f"  Duration  : {mins}m {secs}s",
        "-" * 55,
    ]

    if failures:
        lines.append("  Failed items:")
        for item in failures:
            lines.append(f"    - {item['title']}")
            if item.get("error"):
                lines.append(f"      Error: {item['error']}")
        lines.append("-" * 55)

    lines.append("")
    output = "\n".join(lines)

    # Use click.echo with colour highlights for the console
    click.echo(click.style("\n" + "=" * 55, fg="cyan"))
    click.echo(click.style("  DOWNLOAD SUMMARY", fg="cyan", bold=True))
    click.echo(click.style("=" * 55, fg="cyan"))
    click.echo(click.style(f"  Succeeded : {len(successes)}", fg="green"))
    click.echo(click.style(f"  Failed    : {len(failures)}", fg="red" if failures else "white"))
    click.echo(click.style(f"  Skipped   : {len(skipped)}", fg="yellow"))
    click.echo(f"  Total     : {len(items)}")
    click.echo(f"  Duration  : {mins}m {secs}s")
    click.echo(click.style("-" * 55, fg="cyan"))
    if failures:
        click.echo(click.style("  Failed items:", fg="red"))
        for item in failures:
            click.echo(click.style(f"    - {item['title']}", fg="red"))
            if item.get("error"):
                click.echo(f"      Error: {item['error']}")
        click.echo(click.style("-" * 55, fg="cyan"))
    click.echo("")

    # Log the plain version to file
    logger.info(output)


# ─────────────────────────────────────────────
#  4b. RETRY QUEUE for failed items
# ─────────────────────────────────────────────
def retry_failed(manifest: dict, ydl_opts: dict, logger: logging.Logger) -> None:
    """Offers to retry all items marked as 'failed' in the manifest."""
    failures = [v for v in manifest.get("items", {}).values() if v["status"] == "failed"]
    if not failures:
        return

    if not click.confirm(f"\n  {len(failures)} item(s) failed. Retry them now?", default=True):
        logger.info("Skipping retry of failed items.")
        return

    failed_urls = [
        f"https://www.youtube.com/watch?v={item['video_id']}"
        for item in failures
    ]
    logger.info(f"\nRetrying {len(failed_urls)} failed item(s)...\n")

    # Reset their status before retrying
    for item in failures:
        update_item(item["video_id"], "retrying", item["title"])

    # Remove the archive restriction so yt-dlp doesn't skip them
    retry_opts = {k: v for k, v in ydl_opts.items() if k != "download_archive"}

    try:
        with yt_dlp.YoutubeDL(retry_opts) as ydl:
            ydl.download(failed_urls)
        logger.info("Retry pass completed.")
    except Exception as e:
        logger.error(f"Error during retry: {e}")


# ─────────────────────────────────────────────
#  MAIN DOWNLOADER
# ─────────────────────────────────────────────
def download_playlist_as_mp3(
    playlist_url: str,
    output_folder: str,
    quality: str,
    force_fresh: bool,
) -> None:
    global _logger, _manifest_path, _manifest, _start_time

    # Create output directory
    os.makedirs(output_folder, exist_ok=True)

    # Persistent file paths
    archive_path  = os.path.join(output_folder, "downloaded_archive.txt")
    manifest_path = os.path.join(output_folder, "manifest.json")
    _manifest_path = manifest_path

    # Logger must be set up before anything else
    logger, log_filename = setup_logger(output_folder)
    _logger = logger

    # ── Feature 3: Fresh-start or resume ──
    if force_fresh:
        for path in [archive_path, manifest_path]:
            if os.path.exists(path):
                os.remove(path)
        logger.info("--fresh flag: cleared prior history.")
    else:
        ask_fresh_start(archive_path, manifest_path, output_folder)

    # Load (or initialise) the manifest and record this run
    _manifest = load_manifest(manifest_path)
    _manifest.setdefault("runs", []).append({
        "started": datetime.now().isoformat(),
        "playlist_url": playlist_url,
    })
    save_manifest(manifest_path, _manifest)

    # ── Feature 6: Graceful Ctrl+C ──
    setup_signal_handler()
    _start_time = datetime.now()

    # ── yt-dlp options ──
    hooks = make_hooks(logger)
    ydl_opts = {
        "format": "bestaudio/best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": quality,
            }
        ],
        "outtmpl": os.path.join(output_folder, "%(playlist_index)02d - %(title)s.%(ext)s"),
        # Feature 1: resume support via archive file
        "download_archive": archive_path,
        "ignoreerrors": True,
        "quiet": False,
        "sleep_interval": 5,
        "max_sleep_interval": 8,
        "logger": logger,
        "extractor_args": {"youtube": {"player_client": ["android", "mweb", "web"]}},
        **hooks,
    }

    logger.info("\n" + "=" * 55)
    logger.info(f"  Playlist : {playlist_url}")
    logger.info(f"  Output   : {os.path.abspath(output_folder)}")
    logger.info(f"  Quality  : {quality} kbps")
    logger.info(f"  Log file : {os.path.abspath(log_filename)}")
    logger.info(f"  Manifest : {os.path.abspath(manifest_path)}")
    logger.info(f"  Archive  : {os.path.abspath(archive_path)}")
    logger.info(f"  Delay    : 5-8 seconds between tracks")
    logger.info("=" * 55 + "\n")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([playlist_url])

        if not _interrupted:
            logger.info("Main download pass completed.")

    except SystemExit:
        pass  # yt-dlp raises SystemExit on some interruptions
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        # Feature 5: always print summary, even on Ctrl+C
        print_summary(_manifest, _start_time, logger)

        # Feature 4b: offer retry only if run completed (not interrupted)
        if not _interrupted:
            retry_failed(_manifest, ydl_opts, logger)

        # Stamp the end time into the manifest
        _manifest["runs"][-1]["ended"] = datetime.now().isoformat()
        save_manifest(manifest_path, _manifest)


# ─────────────────────────────────────────────
#  7. CLI / URL INPUT
# ─────────────────────────────────────────────
YOUTUBE_URL_RE = re.compile(
    r"(https?://)?(www\.)?(youtube\.com/(playlist\?|watch\?)|youtu\.be/)[\w\-&=]+"
)


def validate_url(ctx, param, value):
    """Click callback that validates a YouTube URL."""
    if value and not YOUTUBE_URL_RE.match(value):
        raise click.BadParameter("That doesn't look like a valid YouTube playlist URL.")
    return value


# ─────────────────────────────────────────────
#  ENTRY POINT  (Click command)
# ─────────────────────────────────────────────
@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("url", required=False, callback=validate_url, is_eager=True, expose_value=True)
@click.option(
    "--output", "-o",
    default="downloads",
    show_default=True,
    metavar="FOLDER",
    help="Destination folder for MP3 files.",
)
@click.option(
    "--quality", "-q",
    default="192",
    show_default=True,
    type=click.Choice(["128", "192", "256", "320"]),
    help="MP3 bitrate in kbps.",
)
@click.option(
    "--fresh",
    is_flag=True,
    default=False,
    help="Skip the resume prompt and force a fresh download.",
)
@click.version_option("2.0.0", prog_name="yt-playlist-mp3")
def cli(url: str | None, output: str, quality: str, fresh: bool) -> None:
    """
    Download a YouTube playlist as MP3 files.

    If URL is omitted you will be prompted to enter one interactively.

    \b
    Examples:
      python yt_playlist_mp3_downloader.py
      python yt_playlist_mp3_downloader.py 'https://youtube.com/playlist?list=...'
      python yt_playlist_mp3_downloader.py 'https://...' --output MyAlbum --quality 320
      python yt_playlist_mp3_downloader.py 'https://...' --fresh
    """
    if not url:
        click.echo("\n  " + click.style("YouTube Playlist MP3 Downloader", bold=True))
        click.echo("  " + "─" * 45)
        while True:
            url = click.prompt("  Paste your YouTube playlist URL").strip()
            if YOUTUBE_URL_RE.match(url):
                break
            click.echo(click.style(
                "  That doesn't look like a valid YouTube URL. Please try again.\n",
                fg="red",
            ))

    download_playlist_as_mp3(
        playlist_url=url,
        output_folder=output,
        quality=quality,
        force_fresh=fresh,
    )


if __name__ == "__main__":
    cli()
