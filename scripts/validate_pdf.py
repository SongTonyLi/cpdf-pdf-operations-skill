#!/usr/bin/env python3
"""Validate one or more PDF outputs with the cpdf found on PATH."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

DOWNLOAD_URL = "https://www.coherentpdf.com/"


def validate(path: Path, cpdf: str) -> dict[str, object]:
    result: dict[str, object] = {"path": str(path), "ok": False}
    if not path.is_file():
        result["error"] = "not a file"
        return result
    result["bytes"] = path.stat().st_size
    if path.stat().st_size < 8:
        result["error"] = "file is empty or too short"
        return result
    try:
        header = path.read_bytes()[:8]
    except OSError as exc:
        result["error"] = str(exc)
        return result
    if not header.startswith(b"%PDF-"):
        result["error"] = "missing PDF header"
        return result

    proc = subprocess.run([cpdf, "-info", "-utf8", str(path)], text=True, capture_output=True)
    result["cpdf_exit"] = proc.returncode
    if proc.returncode:
        result["error"] = (proc.stderr or proc.stdout).strip()
        return result
    for line in proc.stdout.splitlines():
        if line.startswith("Pages:"):
            try:
                result["pages"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("Encryption:"):
            result["encryption"] = line.split(":", 1)[1].strip()
        elif line.startswith("Version:"):
            result["pdf_version"] = line.split(":", 1)[1].strip()
    result["ok"] = True
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="+", type=Path)
    args = parser.parse_args()
    cpdf = shutil.which("cpdf")
    if not cpdf:
        print(f"cpdf was not found on PATH. Download/install it from {DOWNLOAD_URL}", file=sys.stderr)
        return 127
    results = [validate(path.expanduser().resolve(), cpdf) for path in args.pdf]
    print(json.dumps(results, indent=2))
    return 0 if all(item["ok"] for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
