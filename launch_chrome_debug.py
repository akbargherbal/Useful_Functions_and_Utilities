"""
launch_chrome_debug.py
----------------------
Launch Chrome with remote debugging enabled, in a dedicated, fully
independent debug profile -- so it never blocks (or gets blocked by)
your other real Chrome profiles.

Why a dedicated directory instead of the old junction trick?
  Chrome enforces ONE running instance per user-data-dir, via a
  SingletonLock file written inside that directory. Any second Chrome
  launch that resolves to the SAME physical directory hands off to the
  first process instead of starting independently.

  An earlier version of this script pointed the debug instance at a
  directory junction aliased back to the real "User Data" folder, so
  it could see your real profiles while still satisfying Chrome's
  "remote debugging requires a non-default data directory" check.
  That worked for opening the debug port -- but it meant the debug
  instance's SingletonLock and your real Chrome's SingletonLock were
  the exact same file. Once the debug instance owned it, EVERY other
  profile you tried to open got handed off into that one debug-mode
  process instead of opening independently. That's the "can only use
  Profile 8 until I kill Chrome" bug.

  Fix: the debug instance now lives in its own directory tree under
  CHROME_DEBUG_ROOT, never aliased to your real User Data folder. Its
  lock is scoped to itself, so it can't intercept -- or be intercepted
  by -- a launch of any of your real profiles. This also means we no
  longer need to kill every Chrome process on every run: only a stale
  debug instance left over from a previous run is ever killed. Your
  other profiles can stay open the whole time.

--refresh-auth:
  A brand-new debug directory starts logged out. This flag seeds it
  with just the auth-relevant files copied from your real profile:
  Local State, Network/Cookies(+journal), Network/Device Bound
  Sessions(+journal), and Preferences. Typically well under 1 MB --
  it deliberately does NOT copy Cache, IndexedDB, Service Worker, etc.
  (the multi-GB disposable stuff Chrome regenerates on its own).

  This is a one-time-or-occasional step, NOT something that runs on
  every launch. A plain `chrome_debug` never touches your real
  profile and never requires closing it.

  Caveat: Google's Device Bound Session Credentials (DBSC) ties some
  sessions to a hardware-backed key that can't be copied between
  directories. If the debug profile logs itself out after a while
  despite --refresh-auth, that's DBSC -- re-run --refresh-auth
  periodically, or sign in directly in the debug profile once.

Configuration (in priority order):
  1. CLI flags          --port / --profile
  2. Environment vars    CHROME_DEBUG_PORT, CHROME_DEBUG_PROFILE,
                         CHROME_EXECUTABLE, CHROME_USER_DATA_DIR,
                         CHROME_DEBUG_ROOT
  3. .env file           place a .env next to this script (never commit it)
  4. Platform defaults   auto-detected paths for Windows / macOS / Linux

Usage:
    chrome_debug                       # launch / relaunch the debug profile
    chrome_debug --port 9223
    chrome_debug --profile "Profile 3" # which REAL profile this debug profile mirrors
    chrome_debug --refresh-auth        # (re)seed login state from the real profile
    chrome_debug --no-wait             # skip port-readiness check
    chrome_debug --dry-run             # print what would run, don't execute
    chrome_debug --config              # print resolved config and exit
    chrome_debug --force-kill-all      # legacy escape hatch: kill EVERY chrome.exe
"""

import argparse
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

# ── .env loader (no dependencies — pure stdlib) ───────────────────────────────


def load_dotenv(path: pathlib.Path) -> None:
    if not path.is_file():
        return
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


load_dotenv(pathlib.Path(__file__).parent / ".env")


# ── Platform detection ────────────────────────────────────────────────────────


def detect_platform() -> str:
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


PLATFORM = detect_platform()

_CHROME_DEFAULT = {
    "windows": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "macos": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "linux": "google-chrome",
}

_USER_DATA_DEFAULT = {
    "windows": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"),
    "macos": os.path.expanduser("~/Library/Application Support/Google/Chrome"),
    "linux": os.path.expanduser("~/.config/google-chrome"),
}

_DEBUG_ROOT_DEFAULT = {
    "windows": os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome Debug Profiles"),
    "macos": os.path.expanduser(
        "~/Library/Application Support/Google/Chrome Debug Profiles"
    ),
    "linux": os.path.expanduser("~/.config/google-chrome-debug-profiles"),
}

# ── Resolved config ────────────────────────────────────────────────────────────

CHROME_EXECUTABLE = os.environ.get("CHROME_EXECUTABLE") or _CHROME_DEFAULT[PLATFORM]
REAL_USER_DATA = os.environ.get("CHROME_USER_DATA_DIR") or _USER_DATA_DEFAULT[PLATFORM]
DEBUG_ROOT = pathlib.Path(
    os.environ.get("CHROME_DEBUG_ROOT") or _DEBUG_ROOT_DEFAULT[PLATFORM]
)
DEFAULT_PORT = int(os.environ.get("CHROME_DEBUG_PORT", "9222"))
DEFAULT_PROFILE = os.environ.get("CHROME_DEBUG_PROFILE", "Default")

POLL_INTERVAL = 0.5
POLL_TIMEOUT = 30

# Files copied from the real profile by --refresh-auth. Deliberately tiny --
# everything else (Cache, IndexedDB, Service Worker, GPUCache, ...) is left
# behind; Chrome regenerates it on its own.
AUTH_ALLOWLIST = [
    "Network/Cookies",
    "Network/Cookies-journal",
    "Network/Device Bound Sessions",
    "Network/Device Bound Sessions-journal",
    "Preferences",
]


def _resolve_auth_files(real_profile_dir: pathlib.Path) -> list[str]:
    """Older Chrome versions kept Cookies at the profile root instead of Network/."""
    if (
        not (real_profile_dir / "Network" / "Cookies").exists()
        and (real_profile_dir / "Cookies").exists()
    ):
        return [f.replace("Network/", "") for f in AUTH_ALLOWLIST]
    return AUTH_ALLOWLIST


# ── Debug directory ────────────────────────────────────────────────────────────


def get_debug_dir(profile: str) -> pathlib.Path:
    """
    Independent user-data-dir for this debug profile. NOT a junction, NOT
    aliased to REAL_USER_DATA -- a genuinely separate directory, so its
    SingletonLock can never collide with your real profiles' lock.
    """
    return DEBUG_ROOT / profile


# ── Process helpers ────────────────────────────────────────────────────────────


def find_pids_by_cmdline(substring: str) -> list[int]:
    """Return PIDs of chrome.exe processes whose command line contains *substring*."""
    pids: list[int] = []
    if PLATFORM == "windows":
        result = subprocess.run(
            [
                "wmic",
                "process",
                "where",
                "name='chrome.exe'",
                "get",
                "ProcessId,CommandLine",
                "/format:list",
            ],
            capture_output=True,
            text=True,
        )
        for block in result.stdout.split("\n\n"):
            pid, cmdline = "", ""
            for ln in block.splitlines():
                ln = ln.strip()
                if ln.startswith("ProcessId="):
                    pid = ln.split("=", 1)[1]
                elif ln.startswith("CommandLine="):
                    cmdline = ln.split("=", 1)[1]
            if pid and substring.lower() in cmdline.lower():
                try:
                    pids.append(int(pid))
                except ValueError:
                    pass
    else:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "chrome" in line.lower() and substring.lower() in line.lower():
                parts = line.split()
                if len(parts) > 1:
                    try:
                        pids.append(int(parts[1]))
                    except ValueError:
                        pass
    return list(set(pids))


def kill_pids(pids: list[int], dry_run: bool = False) -> None:
    for pid in pids:
        cmd = (
            ["taskkill", "/F", "/PID", str(pid)]
            if PLATFORM == "windows"
            else ["kill", "-9", str(pid)]
        )
        print(f"    Killing PID {pid} …  ({' '.join(cmd)})")
        if dry_run:
            print("    [dry-run] skipped.")
            continue
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"    PID {pid} terminated.")
        else:
            print(f"    Could not kill PID {pid}: {result.stderr.strip()}")


def cleanup_singleton_locks(target_dir: pathlib.Path, dry_run: bool = False) -> None:
    """Remove stale SingletonLock/Socket/Cookie files from *target_dir*."""
    found_any = False
    for name in ("SingletonLock", "SingletonSocket", "SingletonCookie"):
        lock_path = target_dir / name
        if lock_path.exists() or lock_path.is_symlink():
            found_any = True
            print(f"    Removing stale lock: {lock_path}")
            if not dry_run:
                try:
                    lock_path.unlink()
                except OSError as exc:
                    print(f"    Warning: could not remove {lock_path}: {exc}")
    if not found_any:
        print("    No singleton lock files found.")


def kill_stale_debug_instance(debug_dir: pathlib.Path, dry_run: bool = False) -> None:
    """
    Kill only a PREVIOUS debug-mode Chrome process tied to *this* debug
    directory (e.g. left over from a crashed run). Never touches your real
    Chrome profiles or other debug profiles -- they live elsewhere on disk.
    """
    pids = find_pids_by_cmdline(str(debug_dir))
    if pids:
        print(f"[*] Found a stale debug instance for this profile: PID(s) {pids}")
        kill_pids(pids, dry_run=dry_run)
        if not dry_run:
            time.sleep(1.5)
    else:
        print("[*] No previous debug instance running for this profile.")
    if not dry_run:
        cleanup_singleton_locks(debug_dir, dry_run=False)


def force_kill_all_chrome(dry_run: bool = False) -> None:
    """Legacy escape hatch: kill every chrome.exe on the system, real profiles included."""
    print("[!] --force-kill-all: killing every chrome.exe process system-wide.")
    print(
        "    (Your other open profiles/tabs will close too -- this is the old default.)"
    )
    if PLATFORM == "windows":
        cmd = ["taskkill", "/F", "/IM", "chrome.exe"]
        if dry_run:
            print(f"    [dry-run] would run: {' '.join(cmd)}")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(
                    f"    taskkill warning: {result.stderr.strip() or result.stdout.strip()}"
                )
    else:
        kill_pids(find_pids_by_cmdline("chrome"), dry_run=dry_run)
    if not dry_run:
        time.sleep(1.5)


# ── Auth bootstrap (opt-in, via --refresh-auth) ───────────────────────────────


def refresh_auth(profile: str, debug_dir: pathlib.Path, dry_run: bool = False) -> None:
    real_root = pathlib.Path(REAL_USER_DATA)
    real_profile_dir = real_root / profile

    if not real_profile_dir.is_dir():
        print(f"[x] Real profile not found: {real_profile_dir}")
        sys.exit(1)

    running = find_pids_by_cmdline(str(real_root))
    if running:
        print(
            f"[!] Chrome appears to be running against your real profile (PID(s) {running})."
        )
        print("    Close it first -- Cookies is a SQLite WAL file; copying it live")
        print("    risks an inconsistent snapshot.")
        sys.exit(1)

    debug_profile_dir = debug_dir / "Default"
    debug_profile_dir.mkdir(parents=True, exist_ok=True)

    print(f"[*] Refreshing auth state: {real_profile_dir}  ->  {debug_profile_dir}")
    if dry_run:
        print("    [dry-run] no files copied.")
        return

    shutil.copy2(real_root / "Local State", debug_dir / "Local State")
    print("    Copied Local State")

    copied = 0
    for rel in _resolve_auth_files(real_profile_dir):
        src = real_profile_dir / rel
        if not src.exists():
            continue
        dst = debug_profile_dir / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied += src.stat().st_size
        print(f"    Copied {rel}  ({src.stat().st_size:,} bytes)")

    print(f"[OK] Auth refreshed ({copied / 1024:.1f} KB copied).")


# ── Pre-flight ─────────────────────────────────────────────────────────────────


def validate_config(
    profile: str, debug_dir: pathlib.Path, needs_real_profile: bool
) -> None:
    errors: list[str] = []

    exe_path = pathlib.Path(CHROME_EXECUTABLE)
    if not exe_path.is_file():
        src = (
            "CHROME_EXECUTABLE env var"
            if os.environ.get("CHROME_EXECUTABLE")
            else "platform default"
        )
        errors.append(
            f"  [x] Chrome executable not found (from {src}):\n"
            f"        {CHROME_EXECUTABLE}\n"
            f'      Fix: $env:CHROME_EXECUTABLE = "C:\\...\\chrome.exe"'
        )

    if needs_real_profile:
        real_root = pathlib.Path(REAL_USER_DATA)
        real_profile_dir = real_root / profile
        if not real_profile_dir.is_dir():
            available = (
                sorted(
                    p.name
                    for p in real_root.iterdir()
                    if p.is_dir()
                    and (p.name.startswith("Profile") or p.name == "Default")
                )
                if real_root.is_dir()
                else []
            )
            hint = (
                f"Available profiles: {available}"
                if available
                else "Real user-data dir not found."
            )
            errors.append(
                f"  [x] Real profile not found (needed for --refresh-auth):\n"
                f"        {real_profile_dir}\n"
                f"      {hint}"
            )

    if not (1024 <= DEFAULT_PORT <= 65535):
        errors.append(
            f"  [x] CHROME_DEBUG_PORT={DEFAULT_PORT} invalid (must be 1024-65535)."
        )

    if errors:
        print("=" * 62)
        print("[!] Pre-flight check failed — fix the issues below and retry:")
        print("=" * 62)
        for err in errors:
            print(err)
        print("=" * 62)
        sys.exit(1)

    if not debug_dir.exists():
        print(f"[*] First run for this debug profile — it will start logged out.")
        print(
            f"    Run with --refresh-auth to seed it from your real '{profile}' profile."
        )

    print("[OK] Pre-flight checks passed.")


# ── Launch ─────────────────────────────────────────────────────────────────────


def launch_chrome(
    port: int, profile: str, dry_run: bool = False
) -> "pathlib.Path | None":
    debug_dir = get_debug_dir(profile)
    debug_dir.mkdir(parents=True, exist_ok=True)

    log_path = pathlib.Path(tempfile.gettempdir()) / f"chrome_debug_{port}.log"
    try:
        log_path.unlink(missing_ok=True)
    except OSError:
        pass

    cmd = [
        CHROME_EXECUTABLE,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={debug_dir}",
        "--profile-directory=Default",
        "--no-first-run",
        "--no-default-browser-check",
        "--remote-allow-origins=*",
        "--enable-logging",
        f"--log-file={log_path}",
    ]

    print(
        f"[*] Launching Chrome on port {port}  (debug profile mirrors real '{profile}') …"
    )
    print(f"    Debug user-data-dir: {debug_dir}")
    display_cmd = [
        c
        for c in cmd
        if not c.startswith("--enable-logging") and not c.startswith("--log-file")
    ]
    print(f"    {' '.join(repr(c) for c in display_cmd)}")
    print(f"    (Chrome log → {log_path})")

    if dry_run:
        print("    [dry-run] skipped.")
        return None

    if PLATFORM == "windows":
        subprocess.Popen(
            cmd,
            creationflags=subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
    else:
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    return log_path


def wait_for_port(port: int, timeout: float = POLL_TIMEOUT) -> tuple[bool, str]:
    candidates = [
        f"http://127.0.0.1:{port}/json/version",
        f"http://localhost:{port}/json/version",
    ]
    deadline = time.time() + timeout

    print(f"[*] Waiting for Chrome debug port {port} …", end="", flush=True)
    while time.time() < deadline:
        for url in candidates:
            try:
                with urllib.request.urlopen(url, timeout=1) as resp:
                    if resp.status == 200:
                        print(f" ready ✓  ({url})")
                        return True, url
            except (urllib.error.URLError, OSError):
                pass
        print(".", end="", flush=True)
        time.sleep(POLL_INTERVAL)

    print(" timed out ✗")
    return False, ""


def run_port_diagnostics(
    port: int, debug_dir: pathlib.Path, log_path: "pathlib.Path | None" = None
) -> None:
    print("\n[*] Diagnostics ─────────────────────────────────────────")

    print(f"\n  Checking what is bound to port {port}:")
    if PLATFORM == "windows":
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        lines = [ln.strip() for ln in result.stdout.splitlines() if f":{port}" in ln]
    else:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"], capture_output=True, text=True
        )
        lines = result.stdout.strip().splitlines()
    if lines:
        for ln in lines:
            print(f"    {ln}")
    else:
        print(
            f"    ✗  Nothing is bound to port {port}. Chrome did NOT open a debug server."
        )

    active_port_file = debug_dir / "DevToolsActivePort"
    print(f"\n  DevToolsActivePort file ({active_port_file}):")
    if active_port_file.exists():
        content = active_port_file.read_text(encoding="utf-8", errors="replace").strip()
        actual_port = content.splitlines()[0] if content else "(empty)"
        if actual_port == str(port):
            print(
                f"    ✓  File exists — Chrome confirms debug server on port {actual_port}."
            )
        else:
            print(f"    ⚠  File exists but shows port {actual_port} (expected {port}).")
    else:
        print("    ✗  File does not exist — Chrome did NOT start the DevTools server.")
        print("       Check chrome://policy for DevToolsAvailability = Disallowed.")

    print("\n  Chrome processes with --remote-debugging in their command line:")
    pids = find_pids_by_cmdline("remote-debugging")
    if pids:
        print(f"    ✓  PID(s): {pids}")
    else:
        print("    ✗  No chrome.exe has --remote-debugging-port in its command line.")

    if log_path and log_path.exists():
        print(f"\n  Chrome log ({log_path}):")
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            keywords = (
                "devtools",
                "remote_debug",
                "remote-debug",
                "error",
                "warning",
                str(port),
                "listen",
                "bind",
            )
            relevant = [ln for ln in lines if any(k in ln.lower() for k in keywords)]
            for ln in relevant[:30]:
                print(f"    {ln.rstrip()}")
            if not relevant:
                print(
                    f"    (no DevTools-related lines found; {len(lines)} total log lines)"
                )
        except OSError as exc:
            print(f"    Could not read log: {exc}")

    print("\n─────────────────────────────────────────────────────────")


def print_config(port: int, profile: str) -> None:
    debug_dir = get_debug_dir(profile)
    print("Resolved configuration:")
    print(f"  CHROME_EXECUTABLE   = {CHROME_EXECUTABLE}")
    print(
        f"  REAL_USER_DATA      = {REAL_USER_DATA}   (source for --refresh-auth only; never written to)"
    )
    print(f"  DEBUG_ROOT          = {DEBUG_ROOT}")
    print(f"  debug dir (profile) = {debug_dir}")
    print(f"  port                = {port}")
    print(f"  profile             = {profile}")
    print(f"  platform            = {PLATFORM}")


# ── CLI ───────────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Launch a dedicated, isolated debug-mode Chrome profile with --remote-debugging-port.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--port",
        "-p",
        type=int,
        default=DEFAULT_PORT,
        help=f"DevTools port (default: {DEFAULT_PORT})",
    )
    p.add_argument(
        "--profile",
        default=DEFAULT_PROFILE,
        help=f"Which REAL profile this debug profile mirrors / is named after (default: '{DEFAULT_PROFILE}')",
    )
    p.add_argument(
        "--refresh-auth",
        action="store_true",
        help="(Re)seed the debug profile's login state from the real profile (small files only)",
    )
    p.add_argument(
        "--force-kill-all",
        action="store_true",
        help="Legacy escape hatch: kill every chrome.exe system-wide, not just this debug profile's",
    )
    p.add_argument(
        "--no-wait",
        action="store_true",
        help="Skip waiting for the debug port to become ready",
    )
    p.add_argument(
        "--dry-run", action="store_true", help="Print commands without executing them"
    )
    p.add_argument(
        "--config", action="store_true", help="Print resolved config and exit"
    )
    return p.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    args = parse_args()

    if args.config:
        print_config(args.port, args.profile)
        return

    debug_dir = get_debug_dir(args.profile)

    print(
        f"[chrome_debug] platform={PLATFORM}  port={args.port}  profile='{args.profile}'"
    )
    print(f"               debug dir: {debug_dir}")
    print()

    validate_config(args.profile, debug_dir, needs_real_profile=args.refresh_auth)
    print()

    if args.refresh_auth:
        refresh_auth(args.profile, debug_dir, dry_run=args.dry_run)
        print()

    if args.force_kill_all:
        force_kill_all_chrome(dry_run=args.dry_run)
    else:
        print("[*] Checking for a stale debug instance from a previous run")
        print("    (your other Chrome profiles are left alone either way).")
        kill_stale_debug_instance(debug_dir, dry_run=args.dry_run)

    log_path = launch_chrome(port=args.port, profile=args.profile, dry_run=args.dry_run)

    if not args.no_wait and not args.dry_run:
        ready, _ = wait_for_port(args.port)
        if not ready:
            run_port_diagnostics(args.port, debug_dir, log_path)
            print(
                f"\n[~] Port {args.port} not responding after {POLL_TIMEOUT}s.\n    See diagnostics above."
            )
            return

    print("\n[✓] Done. You can now connect your automation / DevTools client.")
    print("    Your other Chrome profiles/windows were never touched.")


if __name__ == "__main__":
    main()
