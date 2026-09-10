#!/usr/bin/env python3
"""Report cpdf and optional helper availability without changing files."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys

DOWNLOAD_URL = "https://www.coherentpdf.com/"
HELPERS = ("gs", "magick", "qpdf", "cpdflin", "jbig2enc", "jbig2dec", "pnmtopng")


def run(path: str, *args: str) -> tuple[int, str]:
    proc = subprocess.run([path, *args], text=True, capture_output=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> int:
    cpdf = shutil.which("cpdf")
    if not cpdf:
        print(f"cpdf was not found on PATH. Download/install it from {DOWNLOAD_URL}", file=sys.stderr)
        return 127

    rc, version_output = run(cpdf, "-version")
    _, help_output = run(cpdf, "-help")
    has_summary = bool(re.search(r"(?m)^\s{2}-summary\b", help_output))
    match = re.search(r"cpdf Version\s+([^\n]+)", version_output, re.IGNORECASE)
    report = {
        "cpdf": cpdf,
        "version": match.group(1).strip() if match else version_output.splitlines()[-1] if version_output else None,
        "version_exit": rc,
        "option_catalog": "-summary" if has_summary else "-help",
        "helpers": {name: shutil.which(name) for name in HELPERS},
    }
    print(json.dumps(report, indent=2))
    return 0 if rc == 0 else rc


if __name__ == "__main__":
    raise SystemExit(main())
