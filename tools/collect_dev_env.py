#!/usr/bin/env python3
"""Collect a read-only developer environment report using the standard library.

This reports executable locations, not installed tool versions or build readiness.
It never invokes Bazel, Rust tools, compilers, installers, or network commands.
"""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys


def read_pins(root):
    bazel = (root / ".bazelversion").read_text(encoding="utf-8").strip()
    rust = None
    in_toolchain = False
    for line in (root / "rust-toolchain.toml").read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("["):
            in_toolchain = stripped == "[toolchain]"
        elif in_toolchain:
            match = re.match(r"channel\s*=\s*[\"']([^\"']+)[\"']", stripped)
            if match:
                rust = match.group(1)
                break
    if not bazel or not rust:
        raise ValueError("cannot read Bazel version and Rust toolchain channel")
    return {"bazel": bazel, "rust_channel": rust}


def git_revision(root, git):
    if not git:
        return {"commit": None, "status": "git is not on PATH"}
    environment = os.environ.copy()
    # Respect the selected directory even when called from a Git hook or worktree.
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE"):
        environment.pop(name, None)
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        common = {"capture_output": True, "text": True, "timeout": 5,
                  "env": environment, "check": False}
        top = subprocess.run([git, "-C", str(root), "rev-parse", "--show-toplevel"],
                             **common)
        if top.returncode or Path(top.stdout.strip()).resolve() != root:
            return {"commit": None, "status": "source directory is not a Git checkout root"}
        result = subprocess.run([git, "-C", str(root), "rev-parse", "--verify", "HEAD^{commit}"],
                                **common)
        revision = result.stdout.strip()
        if result.returncode or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
            return {"commit": None, "status": "HEAD commit is unavailable"}
        return {"commit": revision, "status": "read from selected checkout"}
    except (OSError, subprocess.TimeoutExpired):
        return {"commit": None, "status": "Git inspection failed or exceeded 5 seconds"}


def disk_report(requested):
    probe = requested
    while not probe.exists() and probe != probe.parent:
        probe = probe.parent
    if probe.is_file():
        probe = probe.parent
    result = {"requested_path": str(requested), "measured_path": str(probe),
              "used_parent_directory": probe != requested}
    try:
        usage = shutil.disk_usage(probe)
        result.update(total_bytes=usage.total, free_bytes=usage.free)
    except OSError:
        result.update(total_bytes=None, free_bytes=None, error="disk usage is unavailable")
    return result


def collect(root, build_dir):
    tools = {name: shutil.which(name) for name in
             ("git", "bazel", "bazelisk", "rustup", "rustc", "cargo", "clang", "clang++", "gcc", "g++")}
    return {
        "schema_version": 1,
        "repository": {"path": str(root), "git": git_revision(root, tools["git"])},
        "system": {"os": platform.system(), "release": platform.release(),
                   "architecture": platform.machine(), "logical_cpus": os.cpu_count()},
        "python": {"version": platform.python_version(), "executable": sys.executable},
        "repository_toolchain": read_pins(root),
        "executable_paths": tools,
        "storage": {"repository": disk_report(root), "build": disk_report(build_dir)},
        "notes": [
            "Executable paths do not establish installed versions or compatibility.",
            "Bazel may be managed by build.py and absent from PATH.",
            "Disk usage is informational; no build-space requirement is inferred.",
            "No build, database startup, SQL test, or performance test was run.",
            "Review local paths before sharing this report. No environment variables, credentials, or Git remotes are included.",
        ],
    }


def print_text(report):
    print("Developer environment (read-only)")
    print("Repository: " + report["repository"]["path"])
    git = report["repository"]["git"]
    print("Git commit: " + (git["commit"] or "unavailable") + " (" + git["status"] + ")")
    system = report["system"]
    print("System: {os} {release} / {architecture}; logical CPUs: {logical_cpus}".format(**system))
    print("Python: {version} ({executable})".format(**report["python"]))
    print("Repository toolchain: Bazel {bazel}; Rust {rust_channel}".format(**report["repository_toolchain"]))
    print("Executable locations (not version checks):")
    for name, path in report["executable_paths"].items():
        print("  {}: {}".format(name, path or "not on PATH"))
    print("Storage:")
    for name, disk in report["storage"].items():
        free = "unavailable" if disk["free_bytes"] is None else "{:.2f} GiB free".format(disk["free_bytes"] / (1024 ** 3))
        print("  {}: {} ({})".format(name, disk["requested_path"], free))
        if disk["used_parent_directory"]:
            print("    Measured existing parent: " + disk["measured_path"])
    print("Scope:")
    for note in report["notes"]:
        print("  " + note)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1],
                        help="seekdb checkout or source directory (default: this script's repository)")
    parser.add_argument("--build-dir", type=Path,
                        help="directory to inspect for build storage (default: REPO/build); no directory is created")
    args = parser.parse_args()
    try:
        root = args.repo.expanduser().resolve()
        required = ("build.py", ".bazelversion", "rust-toolchain.toml")
        missing = [name for name in required if not (root / name).is_file()]
        if missing:
            parser.error("not a seekdb source directory; missing: " + ", ".join(missing))
        build_dir = (args.build_dir.expanduser().resolve() if args.build_dir else root / "build")
        report = collect(root, build_dir)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
