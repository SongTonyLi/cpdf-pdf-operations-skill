---
name: cpdf-pdf-operations
description: Operate on PDF files with the Coherent PDF (cpdf) CLI from natural-language requests. Use for inspecting, merging, splitting, selecting, reordering, rotating, scaling, cropping, encrypting, decrypting, compressing, stamping, numbering, attaching files, handling bookmarks/metadata/images/fonts/annotations/page labels, creating or drawing PDFs, JSON conversion, accessibility/PDF-UA work, low-level PDF inspection, and sanitizing JavaScript. Also use when the user says cpdf, Coherent PDF, watermark a PDF, combine PDFs, or manipulate PDF pages.
license: MIT (skill files only; cpdf has its own license)
compatibility: Requires a locally installed cpdf executable. Optional operations may require Ghostscript, ImageMagick, qpdf/cpdflin, jbig2enc, jbig2dec, or pnmtopng. Written from the cpdf 2.9 manual and runtime-gated for older versions.
metadata:
  author: SongTonyLi
  manual-version: "2.9"
---

# Natural-language PDF operations with cpdf

Translate the user's requested outcome into a safe, version-compatible `cpdf` invocation. Do not ask the user to know cpdf syntax.

## Mandatory start: locate and identify cpdf

**Always do this before every cpdf task, even if a path was previously known:**

```bash
CPDF="$(command -v cpdf 2>/dev/null || true)"
if [ -z "$CPDF" ]; then
  printf '%s\n' 'cpdf is not installed or is not on PATH.'
fi
```

If no executable is found, stop and prompt the user to download/install cpdf from <https://www.coherentpdf.com/>. Do not silently substitute another PDF program.

If found, run:

```bash
"$CPDF" -version
"$CPDF" -help
```

Use `-help` as the source of truth for locally supported options. The bundled reference describes manual 2.9, but older binaries lack newer operations. Read [version compatibility](references/version-compatibility.md) whenever an operation might be unavailable. Never invent an option. If unavailable, explain the minimum cpdf version and direct the user to <https://www.coherentpdf.com/>; offer an alternative only with permission.

**Security gate:** cpdf 2.9's changelog says it added input sanitization to prevent command-injection attacks. Treat pre-2.9 binaries as unsafe for untrusted PDFs, attachment names, filenames, metadata, or other attacker-controlled input—especially when an operation invokes an external helper. Recommend upgrading to 2.9+; do not process untrusted input on an older release merely because smoke tests pass.

For a quick environment report:

```bash
python3 scripts/preflight.py
```

Resolve all relative skill paths from this skill directory, not the user's current directory.

## Core workflow

1. **Clarify only ambiguity that changes the result.** Determine input(s), output, page range/order, units, overwrite policy, passwords/permissions, and whether appearance, metadata, annotations, bookmarks, forms, attachments, or accessibility tags must be preserved.
2. **Inspect before mutation.** Usually run `"$CPDF" -info -utf8 -- "$input"` only if the local CLI accepts `--`; cpdf 2.6 does not document `--`, so normally use `"$CPDF" -info -utf8 "$input"`. For page-sensitive work also use `-page-info`; for security work use `-contains-javascript` only when supported.
3. **Plan the exact command.** Prefer one cpdf call and `AND` for ordered operations. Use separate intermediate files only when required. Quote every path and text argument. Never use `eval` or concatenate untrusted text into a shell command.
4. **Protect originals.** Default to a new descriptive output path. Never overwrite an input unless the user explicitly asks and a recoverable backup is made. Ensure output differs from every input. Create requested output directories first.
5. **Preserve semantics deliberately.** Use `-process-struct-trees` for tagged/PDF-UA merge, split, stamp, TOC, imposition, or redaction when the installed version supports it. Warn when rasterizing, removing fonts/text/images/metadata/attachments/annotations, decrypting, forced repair, or low-level editing is lossy or destructive.
6. **Run and check exit status.** cpdf uses exit code `1` for a bad/inappropriate password and `2` for other errors. Do not report success on nonzero exit.
7. **Validate.** Confirm the output exists and is nonempty, then inspect with `-info` or run `python3 scripts/validate_pdf.py <output.pdf>`. Verify operation-specific facts such as page count, encryption, bookmarks, metadata, attachments, or extracted files.
8. **Report naturally.** State what changed, the output path, checks performed, and any caveat. Include the exact command when useful, but never echo passwords.

## Command construction rules

General form:

```bash
"$CPDF" [operation] "input.pdf" [range] [options] -o "output.pdf"
```

- cpdf treats arguments containing a period as file names. Prefix extensionless inputs with `-i`.
- Put each encrypted input's `user=...` or `owner=...` next to that input. Use `-recrypt` only when retaining existing encryption is intended.
- Prefer `-utf8` for textual input/output.
- Measurements default to points (`72pt = 1in`); `pt`, `in`, `cm`, and `mm` are accepted. Page/box variables and arithmetic are documented in the command reference.
- Use response files (`-args`; `-args-json` in 2.7.2+) for long or complex argument lists. A response file does **not** make embedded passwords secret.
- Multiple ordered operations use uppercase `AND`; subsequent page selections use `-range`.
- When outputting binary PDF to stdout, redirect or pipe it; never dump it to the terminal.
- A password may appear in process listings and logs. Avoid printing it, avoid persistent command history where possible, and remove temporary response files containing it.

## Page ranges

Common natural-language mappings:

| Request | Range |
|---|---|
| pages 1 through 5 | `1-5` |
| pages 1, 3, and 8 onward | `1,3,8-end` |
| last three pages | `~3-~1` |
| reverse all pages | `reverse` |
| odd/even pages | `odd` / `even` |
| all except pages 2–4 | `NOT2-4` |
| duplicate each selected page twice | `2DUP<range>` |
| portrait/landscape pages | `portrait` / `landscape` |
| pages with annotations | `annotated` (2.9+) |
| page by label | `[iii]` (manual syntax; verify locally) |

Ranges contain no spaces. Do not use the 2.9 `empty` range on older binaries.

## Choose the operation family

Read [the command reference](references/command-reference.md) for exact syntax and options. Read [natural-language recipes](references/natural-language-recipes.md) for intent-to-command examples.

| User intent | Primary operations |
|---|---|
| inspect/count/audit | `-info`, `-page-info`, `-pages`, `-composition`, `-list-*` |
| extract/reorder/delete/duplicate pages | default merge/selection with ranges |
| merge/collate/split/spray/portfolio | `-merge`, `-split`, `-split-bookmarks`, `-split-max`, `-spray`, `-portfolio` |
| resize/position/rotate/crop/boxes | `-scale-*`, `-stretch`, `-center-to-fit`, `-shift*`, `-rotate*`, `-upright`, `-*box` |
| protect/unlock | `-encrypt`, `-decrypt`, permissions, `-recrypt` |
| reduce size/debug streams | `-compress`, `-decompress`, `-squeeze`, `-process-images` |
| bookmarks/TOC/presentation | `-list/add/remove-bookmarks*`, `-table-of-contents`, `-presentation` |
| watermark/logo/page numbers/Bates | `-stamp-*`, `-combine-pages`, `-add-text`, `-add-rectangle` |
| blank pages/redact/impose/chop | `-pad-*`, `-redact`, `-impose*`, `-twoup*`, `-chop*` |
| annotations | `-list/set/copy/remove-annotations*` |
| metadata/open view/language/labels | `-set-*`, `-metadata`, viewer preferences, `-add-page-labels` |
| attachments | `-attach-file`, `-list-attached-files`, `-dump-attachments`, `-remove-files` |
| images/rasterization | `-list-images*`, `-extract-images`, `-process-images`, `-rasterize`, `-output-image` |
| fonts | `-list-fonts*`, `-copy-font`, `-extract-font`, `-missing-fonts`, `-embed-missing-fonts` |
| editable PDF representation | `-output-json`, `-j` |
| layers/optional content | `-ocg-*` |
| create/typeset/image-to-PDF/draw | `-create-pdf*`, `-typeset`, `-png/-jpeg/-jpeg2000/-jbig2`, `-draw` |
| tagged PDF/PDF-UA | structure-tree and `-verify/-mark-as/-create-pdf-ua-*` operations |
| sanitize/explore/low-level repair | `-remove-javascript`, `-obj*`, dictionary/object/stream operations |

## Safety boundaries

- **Redaction:** `-redact` removes whole-page content only; it is not area/text redaction. A filled rectangle merely hides content and is not secure redaction. Say this explicitly.
- **Passwords:** never include a real password in the final response or test logs. Ask for it only when required.
- **Encryption:** recommend `AES256ISO` for new files. Never recommend insecure `40bit` or `128bit`; `AES256` is deprecated.
- **Forced decryption/repair:** use `-decrypt-force` or Ghostscript repair only after warning and user approval; these can bypass permissions or lose metadata.
- **Lossy actions:** require explicit intent before rasterization, image recompression, `-draft`, `-remove-all-text`, font removal, or metadata/attachment/annotation removal.
- **Low-level edits:** inspect first, make a backup, and validate. `-replace-obj`, `-remove-obj`, dictionary edits, stream replacement, and JSON editing can corrupt a PDF.
- **JavaScript:** inspection/removal is available only in cpdf 2.9+. Treat removal as sanitization, not proof the PDF is harmless.
- **Attachments:** list names before extraction. By default do not add `-raw` or `-utf8` to `-dump-attachments`, because cpdf's default strips dubious filename characters. Extract only into a newly created empty directory, then verify every resolved output remains inside it.
- **External tools:** do not assume they exist. Locate them with `command -v` and pass the exact path using `-gs`, `-im`, `-p2p`, `-jbig2enc`, `-jbig2dec`, or `-cpdflin` as appropriate.
- **Licensing:** cpdf is separate software with its own license. This skill does not redistribute it or change its licensing terms.

## Fast recipes

```bash
# Merge
"$CPDF" -merge "a.pdf" "b.pdf" -o "merged.pdf"

# Extract pages 2–5
"$CPDF" "in.pdf" 2-5 -o "pages-2-5.pdf"

# Rotate selected pages clockwise
"$CPDF" -rotateby 90 "in.pdf" 2,4 -o "rotated.pdf"

# Add page numbers at bottom center
"$CPDF" -add-text "Page %Page of %EndPage" -bottom 18 -utf8 "in.pdf" -o "numbered.pdf"

# Watermark under every page
"$CPDF" -stamp-under "watermark.pdf" "in.pdf" -o "watermarked.pdf"

# Secure modern encryption (replace variables without logging them)
"$CPDF" -encrypt AES256ISO "$OWNER_PASSWORD" "$USER_PASSWORD" -no-copy "in.pdf" -o "protected.pdf"

# Inspect without modifying
"$CPDF" -info -utf8 "in.pdf"
"$CPDF" -pages "in.pdf"
```

For more recipes—including attachment, metadata, bookmark, JSON, image, drawing, PDF/UA, and sanitization examples—read [natural-language recipes](references/natural-language-recipes.md).

## Completion checklist

- [ ] Re-located cpdf with `command -v cpdf` for this task.
- [ ] Checked `-version` and local `-help`.
- [ ] Confirmed inputs and output do not collide.
- [ ] Explained destructive/lossy/security-sensitive effects.
- [ ] Used only locally supported options and available helper tools.
- [ ] Checked exit status and validated every produced PDF/file set.
- [ ] Reported output paths and evidence without exposing secrets.
