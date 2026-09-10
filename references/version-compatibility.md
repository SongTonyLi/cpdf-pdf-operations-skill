# Runtime version and dependency compatibility

The source manual is version 2.9 (cover February 2026; changelog March 2026). The machine on which this skill was authored had cpdf 2.6 patch 1 (September 2023). **Never assume the author's installation is the user's installation. Always run `command -v cpdf`, `cpdf -version`, and consult the local full option catalog (`-summary` on 2.9+, otherwise `-help`).**

If `command -v cpdf` finds nothing, stop and prompt the user to download/install cpdf from <https://www.coherentpdf.com/>. Do not substitute another tool silently.

## Security boundary for versions before 2.9

The 2.9 changelog states that cpdf now “Sanitizes inputs to prevent command injection attacks.” Therefore, do not treat successful parsing or smoke tests on 2.6–2.8.x as evidence that those releases are safe with attacker-controlled data. Recommend cpdf 2.9+ for untrusted PDFs, filenames, attachment names, metadata, JSON, or other externally supplied values, especially for operations invoking Ghostscript, ImageMagick, JBIG2 tools, or other helpers. On an older release, stop before processing untrusted input and ask the user to upgrade from <https://www.coherentpdf.com/>.

## Feature gates after 2.6

This table is based on the manual change log and is a minimum-version guide, not a replacement for the local option catalog.

### Added in 2.7

- `-split-max`, `-spray`
- JSON forms for info, page info, labels, and font listing
- PDF subformat identification and AcroForm detection in `-info`
- `-extract-font`
- `-list-images`, `-list-images-used`, their JSON forms
- `-chop`, `-chop-h`, `-chop-v`
- create PDFs from JBIG2
- `-process-images` and associated recompression/resampling options
- `-extract-stream`, `-extract-stream-decompress`, `-obj`
- `-shift-boxes`
- `-no-process-struct-trees` (opt-out; polarity flipped in 2.7.1)

### Added in 2.7.1

- PDF from JPEG2000
- PDF/UA marking/removing markers and initial Matterhorn verification
- structure tree print/extract/replace
- **Polarity flip:** `-process-struct-trees` (manual spelling; changelog 2.7.1 wrote `-process-struct-tree`) replaces 2.7's `-no-process-struct-trees`. From 2.7.1 onward, structure-tree trim/merge is opt-in.
- `-set-language`

### Added in 2.7.2

- `-args-json`
- `-replace-obj`
- `-create-pdf-ua-1`, `-create-pdf-ua-2`
- structure creation/tagging with `-draw`
- paragraphs via `-para`/`-paras`
- PDF/UA output from `-typeset` and image sources
- `-stretch`
- whole-page `-redact`
- long-deprecated `-control` removed

### Added in 2.8

- `-center-to-fit`
- `-jpeg-to-jpeg-scale`, `-jpeg-to-jpeg-dpi`
- Ghostscript `-rasterize` and `-output-image`
- `-replace-stream`
- `-collate-n`
- `-toc-dot-leaders`
- units for `-info`/`-page-info` boxes; OpenAction and more form info in `-info`
- JSON/PDF syntax in dict/object exploration

### Added in 2.8.1

- `-remove-struct-tree`
- `-mark-as-artifact`
- deeper object-chain exploration (`-obj` from an object number; through arrays/name trees)
- wider PDF/UA preservation across transform/stamp/imposition operations
- `-underneath` and `-scale-stamp-to-fit` for `-combine-pages`
- `%objnum` in `-extract-images` output names

### Added in 2.9

- man page; `-help` / `--help` shortened; full catalog moved to `-summary`
- `-contains-javascript`, `-remove-javascript`
- `-progress`
- PDF portfolios (`-portfolio`, `-pf`, `-pfd`, `-pfr`)
- `-remove-article-threads`, `-remove-page-piece`, `-remove-web-capture`, `-remove-procsets`, `-remove-output-intents`
- `-lossless-to-jpeg2000`, `-jpeg2000-to-jpeg2000`
- CCITT Group 3/4 encoders (`CCITTG3`, `CCITTG4`) for `-process-images`
- `-process-images-force`; lossless CMYK processing
- 8-bit alpha PNG support, including `-rasterize-alpha`
- negative `-thinlines` values to enforce a maximum thickness
- `-remove-all-metadata`, `-extract-all-metadata`
- `empty` and `annotated` ranges; tolerance of some nonexistent pages (still refuses an empty PDF)
- `-extract-single-image`
- JSON attachment listing/data (`-json`, `-include-data`) and `-afd`/`-afr`
- `-inline` listing/extraction; mask reporting/extraction/`-merge-masks`
- removal of alternate images (changelog only; the manual body never names the operation—inspect local `-summary`)
- `-just-content` decompression and JBIG2 decompression via `-jbig2dec`
- `-draw-jpeg2000`
- `-create-pdf` and friends may appear mid-`AND`
- `-squeeze` processes xobjects inside xobjects
- `-pad-before` / `-pad-after` no longer fail on unsorted ranges
- input sanitization against command injection

### Useful environment variables

These appear in the changelog / image chapter. Do not set them unless needed:

| Variable | Effect |
|---|---|
| `CPDF_SHOW_EXT=true` | Print ImageMagick/JBIG2 invocations during `-process-images` (manual text is spaced; confirm locally) |
| `CPDF_DEBUG` | Extra debug output (`-debug`) |
| `CPDF_REPRODUCIBLE_DATES=true` | Stable dates for tests |

## Detect support directly

Avoid a naive substring search such as searching for `-obj`, which can match `-create-objstm`. Parse exact option tokens:

```python
import re, subprocess
help_text = subprocess.run([cpdf, "-help"], text=True, capture_output=True).stdout
catalog = help_text
if re.search(r"(?m)^\s{2}-summary\b", help_text):
    catalog += "\n" + subprocess.run([cpdf, "-summary"], text=True, capture_output=True).stdout
options = set(re.findall(r"(?m)^\s{2}(-{1,2}[a-z0-9][a-z0-9-]*)\b", catalog))
if "-split-max" not in options:
    # Explain that the local cpdf is too old.
    ...
```

On 2.9+, `-help` is abbreviated: if `-summary` is listed, parse that instead (or the man page). On 2.6–2.8.x, parse `-help`. If neither catalog contains the option, probe a non-destructive operation on a generated temporary PDF rather than inventing a flag.

## Optional executable dependencies

Always locate helpers at runtime with `command -v` and pass the resolved path.

| Feature | Helper | cpdf option | Notes |
|---|---|---|---|
| malformed repair, rasterize, embed missing fonts | Ghostscript (`gs`) | `-gs` | May alter/drop metadata |
| image extraction/recompression | ImageMagick (`magick`) | `-im` | Treat extracted files as untrusted |
| alternate PNG conversion | `pnmtopng` | `-p2p` | Used when ImageMagick unavailable |
| linearization | qpdf or cpdflin | `-cpdflin` if not on expected path | cpdf delegates linearization |
| JBIG2 encoding | `jbig2enc` | `-jbig2enc` | Required for JBIG2 image processing |
| JBIG2 decoding | `jbig2dec` | `-jbig2dec` | Needed for decoding/re-encoding certain streams |

## Known semantic constraints

- cpdf does not provide general visible-text extraction or OCR. `-list-annotations` extracts annotation text; `-output-json` exposes PDF internals. Use another tool only after telling the user and getting permission if they explicitly asked to use cpdf.
- `-redact` empties whole pages, not rectangles or matching text.
- `-remove-text` removes text added by cpdf, while `-remove-all-text` removes page text operators broadly.
- Without `-process-struct-trees` (2.7.1+), merge keeps the first file's structure tree and split copies the whole tree into every part.
- Chapter 19's `-output-annotations-json` is a documentation slip; the operation is `-list-annotations-json`.
- Default text encoding is `-stripped`, not UTF-8.
- `-set-version` changes only the declared version marker; it does not down-convert PDF features.
- `-mark-as PDF/UA-*` changes a marker; it does not create accessibility.
- PDF/UA verification is partial/machine-checkable only and requires human review.
- `-contains-javascript`/`-remove-javascript` are not malware detection or complete content disarm and reconstruction.
- Viewer preferences, presentations, layers, and portfolios depend on reader support.

## Licensing

The cpdf program and manual are separately copyrighted and licensed by Coherent Graphics. This skill does not bundle cpdf or the manual. Confirm the user's permitted use, especially for commercial workflows. The skill's MIT license applies only to the original skill documentation and helper/test code.
