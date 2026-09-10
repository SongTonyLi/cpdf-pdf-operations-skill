#!/usr/bin/env python3
"""Create synthetic fixtures and smoke-test cpdf operation families safely."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import time
import zlib

from check_natural_language_cases import validate as validate_natural_language_cases

DOWNLOAD_URL = "https://www.coherentpdf.com/"


def make_png(path: Path, width: int = 64, height: int = 64) -> None:
    """Write a non-interlaced 8-bit RGB PNG without third-party modules."""
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            row.extend((x * 255 // max(1, width - 1), y * 255 // max(1, height - 1), 128))
        rows.append(bytes(row))

    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    data = b"\x89PNG\r\n\x1a\n"
    data += chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    data += chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
    data += chunk(b"IEND", b"")
    path.write_bytes(data)


def exact_options(help_text: str) -> set[str]:
    return set(re.findall(r"(?m)^\s{2}(-{1,2}[a-z0-9][a-z0-9-]*)\b", help_text))


class Suite:
    def __init__(self, cpdf: str, workdir: Path, options: set[str], verbose: bool = False):
        self.cpdf = cpdf
        self.workdir = workdir
        self.options = options
        self.verbose = verbose
        self.results: list[dict[str, object]] = []

    def path(self, name: str) -> Path:
        return self.workdir / name

    def run(self, case: str, args: list[str], *, outputs: list[Path] | None = None,
            check=None, minimum_version: str | None = None) -> bool:
        if args and args[0].startswith("-") and args[0] not in self.options:
            self.results.append({"case": case, "status": "unsupported", "option": args[0],
                                 "minimum_version": minimum_version})
            return False
        started = time.monotonic()
        proc = subprocess.run([self.cpdf, *map(str, args)], cwd=self.workdir, text=True,
                              capture_output=True)
        item: dict[str, object] = {
            "case": case,
            "command": ["cpdf", *self._redact(args)],
            "exit": proc.returncode,
            "seconds": round(time.monotonic() - started, 3),
        }
        errors: list[str] = []
        if proc.returncode != 0:
            errors.append((proc.stderr or proc.stdout).strip()[-1000:])
        for output in outputs or []:
            if output.suffix.lower() == ".pdf":
                ok, detail = self.validate_pdf(output)
                if not ok:
                    errors.append(f"{output.name}: {detail}")
            elif not output.exists() or output.stat().st_size == 0:
                errors.append(f"missing/empty output: {output}")
        if proc.returncode == 0 and check:
            try:
                check(proc)
            except Exception as exc:  # test assertion is recorded, not hidden
                errors.append(f"check failed: {exc}")
        item["status"] = "pass" if not errors else "fail"
        if errors:
            item["errors"] = errors
        if self.verbose or errors:
            item["stdout_tail"] = proc.stdout[-1000:]
            item["stderr_tail"] = proc.stderr[-1000:]
        self.results.append(item)
        return not errors

    @staticmethod
    def _redact(args: list[str]) -> list[str]:
        redacted = [str(x) for x in args]
        if "-encrypt" in redacted:
            i = redacted.index("-encrypt")
            if len(redacted) > i + 3:
                redacted[i + 2] = "<owner-password>"
                redacted[i + 3] = "<user-password>"
        redacted = ["owner=<redacted>" if x.startswith("owner=") else x for x in redacted]
        redacted = ["user=<redacted>" if x.startswith("user=") else x for x in redacted]
        return redacted

    def validate_pdf(self, path: Path) -> tuple[bool, str]:
        if not path.is_file() or path.stat().st_size < 8:
            return False, "not a nonempty file"
        if not path.read_bytes()[:8].startswith(b"%PDF-"):
            return False, "missing PDF header"
        proc = subprocess.run([self.cpdf, "-info", str(path)], text=True, capture_output=True)
        if proc.returncode:
            return False, (proc.stderr or proc.stdout).strip()[-500:]
        match = re.search(r"(?m)^Pages:\s*(\d+)", proc.stdout)
        return (match is not None, f"pages={match.group(1)}" if match else "missing page count")

    def output(self, *args: str) -> str:
        proc = subprocess.run([self.cpdf, *map(str, args)], cwd=self.workdir, text=True,
                              capture_output=True)
        if proc.returncode:
            raise RuntimeError((proc.stderr or proc.stdout).strip()[-1000:])
        return proc.stdout

    def record_assertion(self, case: str, condition: bool, detail: object) -> None:
        self.results.append({"case": case, "status": "pass" if condition else "fail", "detail": detail})

    def page_count(self, path: Path) -> int:
        value = self.output("-pages", str(path)).strip()
        return int(value)

    def page_info(self, path: Path) -> list[dict[str, str]]:
        text = self.output("-page-info", str(path))
        pages: list[dict[str, str]] = []
        current: dict[str, str] | None = None
        for line in text.splitlines():
            match = re.match(r"^Page (\d+):$", line)
            if match:
                current = {"Page": match.group(1)}
                pages.append(current)
            elif current is not None and ":" in line:
                key, value = line.split(":", 1)
                current[key.strip()] = value.strip()
        return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True,
                        help="new or empty directory dedicated to generated test artifacts")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    cpdf = shutil.which("cpdf")
    if not cpdf:
        print(f"cpdf was not found on PATH. Download/install it from {DOWNLOAD_URL}", file=sys.stderr)
        return 127

    workdir = args.workdir.expanduser().resolve()
    if workdir.exists() and any(workdir.iterdir()):
        print(f"Refusing nonempty work directory: {workdir}", file=sys.stderr)
        return 2
    workdir.mkdir(parents=True, exist_ok=True)

    version_proc = subprocess.run([cpdf, "-version"], text=True, capture_output=True)
    help_proc = subprocess.run([cpdf, "-help"], text=True, capture_output=True)
    help_text = help_proc.stdout + help_proc.stderr
    options = exact_options(help_text)
    if "-summary" in options:
        summary = subprocess.run([cpdf, "-summary"], text=True, capture_output=True)
        help_text += "\n" + summary.stdout + summary.stderr
        options |= exact_options(help_text)

    suite = Suite(cpdf, workdir, options, args.verbose)
    base = suite.path("base.pdf")
    second = suite.path("second.pdf")
    image_pdf = suite.path("image.pdf")
    textfile = suite.path("sample.txt")
    attachment = suite.path("notes.txt")
    png = suite.path("sample.png")
    textfile.write_text("Synthetic cpdf smoke test.\nSecond line with UTF-8: café.\n")
    attachment.write_text("Synthetic attachment only.\n")
    make_png(png)

    # 1, 17, 18: core creation and drawing
    suite.run("create-base", ["-create-pdf", "-create-pdf-pages", "4", "-create-pdf-papersize",
                              "a4portrait", "-o", str(base)], outputs=[base])
    numbered = suite.path("numbered.pdf")
    suite.run("stamp-page-numbers", ["-add-text", "Page %Page of %EndPage", "-bottom", "18",
                                     str(base), "-o", str(numbered)], outputs=[numbered])
    suite.run("create-drawing", ["-create-pdf", "AND", "-draw", "-circle", "200 200 100",
                                 "-strokecol", "red", "-thick", "4", "-stroke", "-o", str(second)],
              outputs=[second])
    suite.run("typeset", ["-typeset", str(textfile), "-font", "Courier", "-font-size", "11",
                          "-o", str(suite.path("typeset.pdf"))], outputs=[suite.path("typeset.pdf")])
    suite.run("png-to-pdf", ["-png", str(png), "-o", str(image_pdf)], outputs=[image_pdf])
    suite.record_assertion("semantic-create-page-count", suite.page_count(base) == 4,
                           {"expected": 4, "actual": suite.page_count(base)})
    image_info = suite.page_info(image_pdf)[0]
    suite.record_assertion("semantic-image-page-size", image_info.get("MediaBox", "").endswith("64.000000 64.000000"), image_info)

    # 2: merge, selection, split
    merged = suite.path("merged.pdf")
    suite.run("merge", ["-merge", str(numbered), str(second), str(image_pdf), "-merge-add-bookmarks",
                        "-o", str(merged)], outputs=[merged])
    selected = suite.path("selected.pdf")
    suite.run("page-selection", [str(merged), "1,3,~1", "-o", str(selected)], outputs=[selected])
    reversed_pdf = suite.path("reversed.pdf")
    suite.run("reverse", [str(merged), "reverse", "-o", str(reversed_pdf)], outputs=[reversed_pdf])
    splitdir = suite.path("split")
    splitdir.mkdir()
    suite.run("split-chunks", ["-split", str(merged), "-chunk", "2", "-o", str(splitdir / "part%%%.pdf")])
    split_files = sorted(splitdir.glob("*.pdf"))
    suite.record_assertion("semantic-merge-page-count", suite.page_count(merged) == 6,
                           {"expected": 6, "actual": suite.page_count(merged)})
    suite.record_assertion("semantic-selection-page-count", suite.page_count(selected) == 3,
                           {"expected": 3, "actual": suite.page_count(selected)})
    selected_info = suite.page_info(selected)
    reversed_info = suite.page_info(reversed_pdf)
    suite.record_assertion("semantic-selection-order", selected_info[-1].get("MediaBox", "").endswith("64.000000 64.000000"), selected_info)
    suite.record_assertion("semantic-reverse-order", reversed_info[0].get("MediaBox", "").endswith("64.000000 64.000000"), reversed_info[0])
    suite.record_assertion("semantic-split-chunks", len(split_files) == 3 and all(suite.page_count(p) == 2 for p in split_files),
                           {"files": len(split_files), "page_counts": [suite.page_count(p) for p in split_files]})

    # 3: geometry
    for case, op, value in [
        ("scale-to-fit", "-scale-to-fit", "usletterportrait"),
        ("scale-page", "-scale-page", "0.9 0.9"),
        ("shift", "-shift", "10 20"),
        ("rotate", "-rotateby", "90"),
        ("crop", "-cropbox", "0 0 400 500"),
    ]:
        out = suite.path(f"{case}.pdf")
        suite.run(case, [op, value, str(numbered), "-o", str(out)], outputs=[out])
    fit_info = suite.page_info(suite.path("scale-to-fit.pdf"))[0]
    rotate_info = suite.page_info(suite.path("rotate.pdf"))[0]
    crop_info = suite.page_info(suite.path("crop.pdf"))[0]
    suite.record_assertion("semantic-fit-dimensions", fit_info.get("MediaBox", "").endswith("612.000000 792.000000"), fit_info)
    suite.record_assertion("semantic-rotation", rotate_info.get("Rotation") == "90", rotate_info)
    suite.record_assertion("semantic-crop-box", crop_info.get("CropBox", "").endswith("400.000000 500.000000"), crop_info)
    upright = suite.path("upright.pdf")
    suite.run("upright", ["-upright", str(suite.path("rotate.pdf")), "-o", str(upright)], outputs=[upright])
    boxes = suite.path("boxes.pdf")
    suite.run("show-boxes", ["-show-boxes", str(numbered), "-o", str(boxes)], outputs=[boxes])

    # 4: encryption/decryption with synthetic passwords (redacted in report)
    encrypted = suite.path("encrypted.pdf")
    suite.run("encrypt", ["-encrypt", "AES256ISO", "smoke-owner", "smoke-user", "-no-copy",
                          str(numbered), "-o", str(encrypted)],
              check=lambda _p: (_ for _ in ()).throw(AssertionError("encrypted PDF missing"))
              if not encrypted.is_file() or not encrypted.read_bytes()[:8].startswith(b"%PDF-") else None)
    suite.run("inspect-encrypted", ["-info", str(encrypted), "owner=smoke-owner"],
              check=lambda p: (_ for _ in ()).throw(AssertionError("not reported encrypted"))
              if "Encryption: Not encrypted" in p.stdout or "Encryption:" not in p.stdout else None)
    decrypted = suite.path("decrypted.pdf")
    suite.run("decrypt", ["-decrypt", str(encrypted), "owner=smoke-owner", "-o", str(decrypted)],
              outputs=[decrypted])

    # 5: streams and squeeze
    compressed = suite.path("compressed.pdf")
    decompressed = suite.path("decompressed.pdf")
    squeezed = suite.path("squeezed.pdf")
    suite.run("compress", ["-compress", str(numbered), "-o", str(compressed)], outputs=[compressed])
    suite.run("decompress", ["-decompress", str(compressed), "-o", str(decompressed)], outputs=[decompressed])
    suite.run("squeeze", ["-squeeze", str(numbered), "-squeeze-log-to", str(suite.path("squeeze.log")),
                          "-o", str(squeezed)], outputs=[squeezed])

    # 6, 7: bookmarks, TOC, presentation
    bookmark_file = suite.path("bookmarks.txt")
    bookmark_file.write_text('0 "Start" 1 open\n0 "Middle" 3\n')
    bookmarked = suite.path("bookmarked.pdf")
    suite.run("add-bookmarks", ["-add-bookmarks", str(bookmark_file), str(numbered), "-o", str(bookmarked)],
              outputs=[bookmarked])
    suite.run("list-bookmarks", ["-list-bookmarks-json", str(bookmarked)],
              check=lambda p: (_ for _ in ()).throw(AssertionError("missing Start")) if "Start" not in p.stdout else None)
    toc = suite.path("toc.pdf")
    suite.run("table-of-contents", ["-table-of-contents", str(bookmarked), "-o", str(toc)], outputs=[toc])
    suite.record_assertion("semantic-toc-added-pages", suite.page_count(toc) > suite.page_count(bookmarked),
                           {"before": suite.page_count(bookmarked), "after": suite.page_count(toc)})
    no_bookmarks = suite.path("no-bookmarks.pdf")
    suite.run("remove-bookmarks", ["-remove-bookmarks", str(bookmarked), "-o", str(no_bookmarks)], outputs=[no_bookmarks])
    suite.record_assertion("semantic-bookmarks-removed", suite.output("-list-bookmarks-json", str(no_bookmarks)).strip() == "[]",
                           suite.output("-list-bookmarks-json", str(no_bookmarks)).strip())
    presentation = suite.path("presentation.pdf")
    suite.run("presentation", ["-presentation", str(numbered), "2-end", "-trans", "Split", "-duration", "2",
                               "-o", str(presentation)], outputs=[presentation])

    # 8: stamp/combine/rectangle/remove-text
    draft = suite.path("draft-watermark.pdf")
    suite.run("text-watermark", ["-add-text", "DRAFT", "-diagonal", "-opacity", "0.25", "-color", "red",
                                 "-underneath", str(numbered), "-o", str(draft)], outputs=[draft])
    rect = suite.path("rectangle.pdf")
    suite.run("add-rectangle", ["-add-rectangle", "50 30", "-topleft", "20", "-color", "yellow",
                                str(numbered), "-o", str(rect)], outputs=[rect])
    stamped = suite.path("stamped.pdf")
    suite.run("stamp-under", ["-stamp-under", str(second), "-scale-stamp-to-fit", str(numbered),
                              "-o", str(stamped)], outputs=[stamped])
    combined = suite.path("combined.pdf")
    suite.run("combine-pages", ["-combine-pages", str(second), str(numbered), "-o", str(combined)], outputs=[combined])
    removed_stamp = suite.path("remove-cpdf-text.pdf")
    suite.run("remove-cpdf-text", ["-remove-text", str(numbered), "-o", str(removed_stamp)], outputs=[removed_stamp])

    # 9: padding and imposition
    padded = suite.path("padded.pdf")
    suite.run("pad-every", ["-pad-every", "2", str(numbered), "-o", str(padded)], outputs=[padded])
    imposed = suite.path("imposed.pdf")
    suite.run("impose-xy", ["-impose-xy", "2 2", str(numbered), "-o", str(imposed)], outputs=[imposed])
    twoup = suite.path("twoup.pdf")
    suite.run("twoup", ["-twoup", str(numbered), "-o", str(twoup)], outputs=[twoup])
    suite.record_assertion("semantic-padding-page-count", suite.page_count(padded) == 5,
                           {"expected": 5, "actual": suite.page_count(padded)})
    suite.record_assertion("semantic-impose-page-count", suite.page_count(imposed) == 1,
                           {"expected": 1, "actual": suite.page_count(imposed)})
    suite.record_assertion("semantic-twoup-page-count", suite.page_count(twoup) == 2,
                           {"expected": 2, "actual": suite.page_count(twoup)})

    # 10: create, list, and remove a link annotation
    link_pdf = suite.path("link.pdf")
    suite.run("create-link-annotation", ["-add-text", "%URL[OpenAI|https://www.openai.com/]", "-top", "20",
                                         str(base), "1", "-o", str(link_pdf)], outputs=[link_pdf])
    suite.run("list-annotations", ["-list-annotations-json", str(link_pdf)],
              check=lambda p: (_ for _ in ()).throw(AssertionError("not JSON-like")) if "[" not in p.stdout else None)
    no_annotations = suite.path("no-annotations.pdf")
    suite.run("remove-annotations", ["-remove-annotations", str(link_pdf), "1", "-o", str(no_annotations)],
              outputs=[no_annotations])
    annotations_after = suite.output("-list-annotations-json", str(no_annotations)).strip()
    suite.record_assertion("semantic-annotations-removed", '"/Subtype"' not in annotations_after and "annotformatversion" in annotations_after,
                           annotations_after)

    # 11: metadata, opening, labels, composition
    metadata = suite.path("metadata.pdf")
    suite.run("set-title", ["-set-title", "Synthetic Test", str(numbered), "-o", str(metadata)], outputs=[metadata])
    metadata_xmp = suite.path("metadata-xmp.pdf")
    suite.run("create-metadata", ["-create-metadata", str(metadata), "-o", str(metadata_xmp)], outputs=[metadata_xmp])
    opened = suite.path("open-view.pdf")
    suite.run("viewer-settings", ["-set-page-layout", "OneColumn", str(metadata_xmp), "AND",
                                  "-display-doc-title", "true", "AND", "-open-at-page-fit", "end",
                                  "-o", str(opened)], outputs=[opened])
    labeled = suite.path("labels.pdf")
    suite.run("page-labels", ["-add-page-labels", str(numbered), "1-4", "-label-style", "LowercaseRoman",
                              "-o", str(labeled)], outputs=[labeled])
    suite.run("print-page-labels", ["-print-page-labels", str(labeled)],
              check=lambda p: (_ for _ in ()).throw(AssertionError("missing labelstyle")) if "labelstyle" not in p.stdout else None)
    metadata_info = suite.output("-info", "-utf8", str(metadata))
    opened_info = suite.output("-info", "-utf8", str(opened))
    suite.record_assertion("semantic-metadata-title", "Title: Synthetic Test" in metadata_info, metadata_info)
    suite.record_assertion("semantic-viewer-settings", "PageLayout: OneColumn" in opened_info and "displaydoctitle: true" in opened_info.lower(),
                           opened_info)
    no_labels = suite.path("no-labels.pdf")
    suite.run("remove-page-labels", ["-remove-page-labels", str(labeled), "-o", str(no_labels)], outputs=[no_labels])
    suite.record_assertion("semantic-labels-removed", suite.output("-print-page-labels", str(no_labels)).strip() == "",
                           suite.output("-print-page-labels", str(no_labels)).strip())
    suite.run("composition", ["-composition-json", str(merged)],
              check=lambda p: (_ for _ in ()).throw(AssertionError("missing Fonts")) if "Fonts" not in p.stdout else None)

    # 12: attachments
    attached = suite.path("attached.pdf")
    suite.run("attach-file", ["-attach-file", str(attachment), str(numbered), "-o", str(attached)], outputs=[attached])
    suite.run("list-attached", ["-list-attached-files", str(attached)],
              check=lambda p: (_ for _ in ()).throw(AssertionError("notes.txt not listed")) if "notes.txt" not in p.stdout else None)
    attachment_dir = suite.path("attachments")
    attachment_dir.mkdir()
    suite.run("dump-attachments", ["-dump-attachments", str(attached), "-o", str(attachment_dir)])
    if (attachment_dir / "notes.txt").read_text() != attachment.read_text():
        suite.results.append({"case": "attachment-content", "status": "fail"})
    else:
        suite.results.append({"case": "attachment-content", "status": "pass"})
    no_files = suite.path("no-files.pdf")
    suite.run("remove-files", ["-remove-files", str(attached), "-o", str(no_files)], outputs=[no_files])
    suite.record_assertion("semantic-attachments-removed", suite.output("-list-attached-files", str(no_files)).strip() == "",
                           suite.output("-list-attached-files", str(no_files)).strip())
    root_resolved = attachment_dir.resolve()
    escaped = [str(p) for p in attachment_dir.rglob("*") if p.is_file() and root_resolved not in p.resolve().parents]
    suite.record_assertion("semantic-attachment-containment", not escaped, escaped)

    # 13, 14: images and fonts available in 2.6
    suite.run("image-resolution", ["-image-resolution", "300", str(image_pdf)])
    image_dir = suite.path("images")
    image_dir.mkdir()
    image_args = ["-extract-images", str(image_pdf)]
    magick = shutil.which("magick")
    if magick:
        image_args += ["-im", magick]
    else:
        image_args += ["-raw"]
    image_args += ["-o", str(image_dir / "img%")]
    suite.run("extract-images", image_args)
    suite.results.append({"case": "extracted-image-files", "status": "pass" if list(image_dir.iterdir()) else "fail",
                          "count": len(list(image_dir.iterdir()))})
    suite.run("list-fonts", ["-list-fonts", str(numbered)],
              check=lambda p: (_ for _ in ()).throw(AssertionError("font not listed")) if "Times" not in p.stdout else None)
    suite.run("missing-fonts", ["-missing-fonts", str(numbered)])

    # 15, 16: CPDFJSON and OCG
    json_file = suite.path("document.json")
    suite.run("output-json", ["-output-json", "-utf8", str(numbered), "-o", str(json_file)], outputs=[json_file])
    roundtrip = suite.path("roundtrip.pdf")
    suite.run("json-roundtrip", ["-j", str(json_file), "-o", str(roundtrip)], outputs=[roundtrip])
    suite.record_assertion("semantic-json-roundtrip-page-count", suite.page_count(roundtrip) == suite.page_count(numbered),
                           {"before": suite.page_count(numbered), "after": suite.page_count(roundtrip)})
    suite.run("ocg-list", ["-ocg-list", str(numbered)])

    # 20: miscellaneous operations available in 2.6
    for case, op, extra in [
        ("blacktext", "-blacktext", []),
        ("blacklines", "-blacklines", []),
        ("blackfills", "-blackfills", []),
        ("thinlines", "-thinlines", ["0.2mm"]),
        ("remove-all-text", "-remove-all-text", []),
        ("draft", "-draft", ["-boxes"]),
        ("remove-clipping", "-remove-clipping", []),
        ("clean", "-clean", []),
        ("set-version", "-set-version", ["6"]),
    ]:
        out = suite.path(f"misc-{case}.pdf")
        suite.run(case, [op, *extra, str(merged), "-o", str(out)], outputs=[out])
    no_id = suite.path("no-id.pdf")
    suite.run("remove-id", ["-remove-id", str(numbered), "-o", str(no_id)], outputs=[no_id])
    suite.run("print-dict-entry", ["-print-dict-entry", "/URI", str(link_pdf)],
              check=lambda p: (_ for _ in ()).throw(AssertionError("URI missing")) if "openai.com" not in p.stdout else None)
    set_version_info = suite.output("-info", str(suite.path("misc-set-version.pdf")))
    no_id_info = suite.output("-info", str(no_id))
    draft_composition = suite.output("-composition-json", str(suite.path("misc-draft.pdf")))
    suite.record_assertion("semantic-version-marker", "Version: 1.6" in set_version_info, set_version_info)
    suite.record_assertion("semantic-id-removed", re.search(r"(?m)^ID:\s*(?:None)?\s*$", no_id_info) is not None, no_id_info)
    normalized_composition = draft_composition.replace(" ", "")
    suite.record_assertion("semantic-draft-images-removed", '("Images",0,0.0)' in normalized_composition or '["Images",0,0.0]' in normalized_composition,
                           draft_composition)

    # Newer-version gates: prove unsupported options are not executed on old cpdf.
    for case, option, minimum in [
        ("gate-page-labels-json", "-print-page-labels-json", "2.7"),
        ("gate-split-max", "-split-max", "2.7"),
        ("gate-pdfua", "-verify", "2.7.1"),
        ("gate-redact", "-redact", "2.7.2"),
        ("gate-rasterize", "-rasterize", "2.8"),
        ("gate-remove-struct-tree", "-remove-struct-tree", "2.8.1"),
        ("gate-javascript", "-contains-javascript", "2.9"),
    ]:
        if option in options:
            suite.results.append({"case": case, "status": "supported-not-run", "option": option,
                                  "minimum_version": minimum})
        else:
            suite.results.append({"case": case, "status": "unsupported", "option": option,
                                  "minimum_version": minimum})

    nl_report = validate_natural_language_cases(Path(__file__).resolve().parents[1])
    suite.results.append({"case": "natural-language-static-contract", "status": "pass" if nl_report["ok"] else "fail",
                          **nl_report})

    report = {
        "cpdf": cpdf,
        "version_output": (version_proc.stdout + version_proc.stderr).strip(),
        "workdir": str(workdir),
        "option_count": len(options),
        "results": suite.results,
    }
    failures = [item for item in suite.results if item["status"] == "fail"]
    counts: dict[str, int] = {}
    for item in suite.results:
        counts[str(item["status"])] = counts.get(str(item["status"]), 0) + 1
    report["summary"] = {"counts": counts, "failures": len(failures)}
    report_path = workdir / "smoke-report.json"
    report_path.write_text(json.dumps(report, indent=2))
    print(json.dumps({"report": str(report_path), **report["summary"]}, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
