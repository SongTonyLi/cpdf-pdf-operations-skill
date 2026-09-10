# Natural-language recipes

Each recipe begins by re-running `command -v cpdf`, `cpdf -version`, and local help. Set `CPDF` to the resolved path. Replace sample paths only after quoting them. Never overwrite an input by default.

## Inspect and select

**“Tell me how many pages this has and whether it is encrypted.”**

```bash
"$CPDF" -info -utf8 "input.pdf"
"$CPDF" -pages "input.pdf"
```

**“Keep the cover, pages 4–8, and the last two pages.”**

```bash
"$CPDF" "input.pdf" '1,4-8,~2-~1' -o "selected.pdf"
```

**“Delete pages 3 to 5.”**

```bash
"$CPDF" "input.pdf" 'NOT3-5' -o "without-pages-3-5.pdf"
```

**“Reverse the PDF.”**

```bash
"$CPDF" "input.pdf" reverse -o "reversed.pdf"
```

## Merge and split

**“Merge these in this order but only take page 1 from the first.”**

```bash
"$CPDF" -merge "a.pdf" 1 "b.pdf" "c.pdf" -o "merged.pdf"
```

**“Interleave the odd and even scan files.”**

```bash
"$CPDF" -merge -collate "odd-pages.pdf" "even-pages.pdf" -o "interleaved.pdf"
```

**“Split into groups of ten pages.”**

```bash
mkdir -p "parts"
"$CPDF" -split "input.pdf" -chunk 10 -o "parts/part%%%.pdf"
```

**“Put odd pages in one PDF and even pages in another.”** (2.7+)

```bash
"$CPDF" -spray "input.pdf" -o "odd.pdf" -o "even.pdf"
```

For cpdf 2.6, use two safe selections instead:

```bash
"$CPDF" "input.pdf" odd -o "odd.pdf"
"$CPDF" "input.pdf" even -o "even.pdf"
```

## Geometry

**“Make everything A4 portrait without distorting it.”**

```bash
"$CPDF" -scale-to-fit a4portrait "input.pdf" -o "a4.pdf"
```

**“Normalize rotated pages before adding a footer.”**

```bash
"$CPDF" -upright "input.pdf" AND -add-text 'Page %Page' -bottom 18 -o "upright-numbered.pdf"
```

**“Crop to a 200 mm square from the lower-left.”**

```bash
"$CPDF" -cropbox '0 0 200mm 200mm' "input.pdf" -o "cropped.pdf"
```

**“Copy each trim box to the crop box.”**

```bash
"$CPDF" -frombox /TrimBox -tobox /CropBox -mediabox-if-missing "input.pdf" -o "trim-as-crop.pdf"
```

## Watermarks, numbering, and overlays

**“Add a translucent diagonal DRAFT watermark.”**

```bash
"$CPDF" -add-text DRAFT -diagonal -font Helvetica-Bold -font-size 72 -color red -opacity 0.25 "input.pdf" -o "draft.pdf"
```

**“Number pages in the bottom-right starting with the PDF page count.”**

```bash
"$CPDF" -add-text 'Page %Page of %EndPage' -bottomright 18 -utf8 "input.pdf" -o "numbered.pdf"
```

**“Apply six-digit Bates numbers starting at 125.”**

```bash
"$CPDF" -add-text '%Bates' -bates 125 -bates-pad-to 6 -bottomright 18 "input.pdf" -o "bates.pdf"
```

**“Put this letterhead behind each page.”**

```bash
"$CPDF" -stamp-under "letterhead.pdf" "input.pdf" -o "on-letterhead.pdf"
```

## Encryption

**“Password-protect this with modern encryption and prevent copying.”**

Warn that passwords may appear in process listings. Obtain owner/user values without printing them, then:

```bash
"$CPDF" -encrypt AES256ISO "$OWNER_PASSWORD" "$USER_PASSWORD" -no-copy "input.pdf" -o "protected.pdf"
```

**“Remove encryption.”**

```bash
"$CPDF" -decrypt "protected.pdf" "owner=$OWNER_PASSWORD" -o "decrypted.pdf"
```

Never show password values in the response.

## Compression and images

**“Losslessly optimize this PDF.”**

```bash
"$CPDF" -squeeze "input.pdf" -squeeze-log-to "squeeze.log" -o "optimized.pdf"
```

Check page count and output size. Do not promise a reduction.

**“Find images used below 300 dpi.”**

```bash
"$CPDF" -image-resolution 300 "input.pdf"
```

**“Extract all images.”**

```bash
mkdir -p "extracted-images"
"$CPDF" -extract-images "input.pdf" -im "$(command -v magick)" -dedup -o "extracted-images/%%%"
```

If `magick` is absent, check `pnmtopng`; otherwise explain the dependency. Do not extract into a nonempty unrelated directory.

**“Turn every page into a 200-dpi PNG.”** (2.8+ and Ghostscript)

```bash
mkdir -p "pages-png"
"$CPDF" -gs "$(command -v gs)" -output-image -rasterize-res 200 "input.pdf" -o "pages-png/page%%%.png"
```

## Bookmarks, metadata, and labels

**“Export bookmarks so I can edit them.”**

```bash
"$CPDF" -list-bookmarks-json "input.pdf" > "bookmarks.json"
```

**“Apply this edited bookmark file.”**

```bash
"$CPDF" -add-bookmarks-json "bookmarks.json" "input.pdf" -o "bookmarked.pdf"
```

**“Set title and author, including XMP when those fields already exist.”**

```bash
"$CPDF" -set-title 'Report' -also-set-xmp "input.pdf" AND -set-author 'A. Author' -also-set-xmp -o "titled.pdf"
```

If XMP fields do not exist, first consider `-create-metadata` and validate metadata afterward.

**“Use Roman numerals for the first four pages and Arabic afterward.”**

```bash
"$CPDF" -add-page-labels "input.pdf" 1-4 -label-style LowercaseRoman -o "labels-1.pdf"
"$CPDF" -add-page-labels "labels-1.pdf" 5-end -label-style DecimalArabic -o "labeled.pdf"
```

## Attachments and annotations

**“Attach notes.txt to the document.”**

```bash
"$CPDF" -attach-file "notes.txt" "input.pdf" -o "with-notes.pdf"
"$CPDF" -list-attached-files "with-notes.pdf"
```

**“Extract all attachments.”**

First list and inspect attachment names. Use cpdf's default filename stripping by omitting both `-raw` and `-utf8`, and require a new empty directory:

```bash
"$CPDF" -list-attached-files "input.pdf"
mkdir "attachments"  # deliberately fails if the path already exists
"$CPDF" -dump-attachments "input.pdf" -o "attachments"
python3 - <<'PY'
from pathlib import Path
root = Path("attachments").resolve()
bad = [str(p) for p in root.rglob("*") if p.is_file() and root not in p.resolve().parents]
if bad:
    raise SystemExit(f"Attachment escaped extraction directory: {bad}")
print(f"Validated extraction containment under {root}")
PY
```

Treat extracted files as untrusted. On cpdf before 2.9, do not extract attacker-controlled attachments; upgrade first because 2.9 added command-injection input sanitization.

**“Remove comments from pages 1 through 3.”**

```bash
"$CPDF" -remove-annotations "input.pdf" 1-3 -o "without-comments.pdf"
```

## Create and draw

**“Create a five-page US Letter PDF.”**

```bash
"$CPDF" -create-pdf -create-pdf-pages 5 -create-pdf-papersize usletterportrait -o "blank-letter.pdf"
```

**“Make a PDF from this text file.”**

```bash
"$CPDF" -typeset "input.txt" -create-pdf-papersize a4portrait -font Courier -font-size 11 -o "text.pdf"
```

**“Draw a red outlined circle.”**

```bash
"$CPDF" -create-pdf AND -draw -circle '297.5 421 100' -strokecol red -thick 4 -stroke -o "circle.pdf"
```

## JSON and low-level work

**“Export a reversible editable JSON representation.”**

```bash
"$CPDF" -output-json -utf8 "input.pdf" -o "input.cpdf.json"
```

Do not add `-output-json-no-stream-data` if round-tripping is needed.

**“Convert the edited CPDFJSON back.”**

```bash
"$CPDF" -j "input.cpdf.json" -o "rebuilt.pdf"
```

Validate page count, encryption, metadata, bookmarks, and attachments; JSON edits can alter them.

**“List every link target.”**

```bash
"$CPDF" -print-dict-entry /URI "input.pdf"
```

## Accessibility and PDF/UA (2.7.1+)

**“Check PDF/UA-1 compliance.”**

```bash
"$CPDF" -verify 'PDF/UA-1(matterhorn)' -json "input.pdf" > "pdfua-report.json"
```

Explain that the verifier is partial and human checks remain. Do not mark the PDF as conforming merely because the user asks to “make it accessible.”

For tagged merge/split/stamp work, add `-process-struct-trees` when supported and validate the output structure.

## JavaScript sanitization (2.9+)

**“Check whether this PDF contains JavaScript.”**

```bash
"$CPDF" -contains-javascript "input.pdf"
```

**“Remove PDF JavaScript.”**

```bash
"$CPDF" -remove-javascript "input.pdf" -o "no-javascript.pdf"
"$CPDF" -contains-javascript "no-javascript.pdf"
```

State that this does not prove the PDF is harmless.

## Requests cpdf does not satisfy directly

- “OCR this scan” — no OCR operation.
- “Extract all visible text” — no general high-level text extraction operation.
- “Securely redact this sentence/rectangle” — cpdf's `-redact` is whole-page only; rectangles are visual covers, not secure redaction.
- “Convert to Word/Excel/HTML” — not a cpdf function.

Explain the limitation. Offer another tool only if the user permits it.
