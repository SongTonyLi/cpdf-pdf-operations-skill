# cpdf command reference (manual 2.9)

This is an original condensed guide to the operation families in the Coherent PDF Command Line Tools 2.9 manual (cover February 2026; changelog March 2026). It does not reproduce or replace the manual. **Check the local full option catalog before using any option:** `-summary` on 2.9+, otherwise `-help`. See `version-compatibility.md` for older binaries.

`in.pdf [range] -o out.pdf` is omitted from many fragments below. Quote paths and compound arguments.

## 1. Core syntax, input, output, ranges

- Typical: `cpdf [operation] input.pdf [range] [options] -o output.pdf`.
- Multiple inputs: repeat file/range pairs or use `-i <extensionless-name>` and `-idir <directory>`; use `-idir-only-pdfs` before `-idir` to ignore non-PDFs.
- Streams: `-stdin`, `-stdout`, `-stdin-owner`, `-stdin-user`.
- Encrypted input credentials follow each input: `user=<password>` or `owner=<password>`; `-recrypt` preserves input encryption.
- Ordered operations: `... AND -range <range> <next operation> ... -o out.pdf`.
- Long command lines: `-args file` (textual substitution); 2.7.2+ also supports a JSON string array with `-args-json file` (C-style comments allowed). `-control` was removed in 2.7.2.
- Text: default is `-stripped` (drop bytes > 127). Prefer `-utf8`; `-raw` performs no conversion. Written text files use Unix LF even on Windows.
- String arguments: cpdf unescapes `\` so shell-special characters can be passed (`Hello\!`; write `\\` for a literal backslash).
- General output controls: `-producer`, `-creator`, `-keep-version`, `-change-id`, `-l`, `-keep-l`, `-cpdflin`, `-no-preserve-objstm`, `-create-objstm`, `-error-on-malformed`, `-progress` (2.9+). `-help` / `--help` is a short pointer page in 2.9+; `-summary` lists operations.
- `-fast` is allowed only on: `-rotate-contents`, `-upright`, `-vflip`, `-hflip`, `-shift`, `-scale-page`, `-scale-to-fit`, `-scale-contents`, `-center-to-fit`, `-stretch`, `-show-boxes`, `-hard-box`, `-trim-marks`, `-add-text`, `-add-rectangle`, `-stamp-on`, `-stamp-under`, `-combine-pages`, `-impose`, `-impose-xy`, `-twoup`, `-twoup-stack`. Skip it unless inputs are known ISO-compliant.
- Repair with Ghostscript: `-gs <path> -gs-malformed` or the exact force form `cpdf in.pdf -gs <path> -gs-malformed-force -o out.pdf [-gs-quiet]`. This may lose metadata.
- Exit `1`: password problem. Exit `2`: other cpdf error.

### Ranges

- Single and lists: `3`, `1-5`, `1-3,8-end`; descending ranges are valid.
- `~1` is last page; `~3-~1` means last three in forward order.
- Selectors: `odd`, `even`, `portrait`, `landscape`, `reverse`, `all`, `annotated` (2.9+), `empty` (2.9+).
- Modifiers: `NOT1-3` excludes; `2DUP1-5` duplicates every selected page twice.
- Page labels may stand in for numbers, e.g. `[iii]`.
- Ranges contain no spaces. 2.9+ may tolerate some nonexistent page numbers, but still errors if the output would have no pages.
- Without `-process-struct-trees`, selection keeps the structure tree whole, merge keeps the first file's tree only, and split copies the whole tree into every part. Add `-process-struct-trees` (2.7.1+) to trim/merge. 2.7 briefly had the opposite opt-out `-no-process-struct-trees`; do not use that flag on 2.7.1+.

### Units and geometry

Default is points. Suffixes: `pt`, `in`, `cm`, `mm`. Page variables: `PW PH PMINX PMINY PMAXX PMAXY`; corresponding crop (`CW CH CMINX...`), art (`AW...`), trim (`TW...`), and bleed (`BW...`) variables are available. Arithmetic words: `add`, `sub`, `mul`, `div` (for example `PW div 2`).

Named sizes: A0–A10 portrait/landscape; `usletterportrait`, `usletterlandscape`, `uslegalportrait`, `uslegallandscape`.

## 2. Merge, portfolio, and split

- Merge/select/reorder: `-merge a.pdf [range] b.pdf [range] ... -o out.pdf`; `-merge` is the default.
- Merge modifiers: `-collate`, `-collate-n n` (2.8+), `-retain-numbering`, `-merge-add-bookmarks`, `-merge-add-bookmarks-use-titles`, `-remove-duplicate-fonts`, `-process-struct-trees`, `-subformat PDF/UA-2`.
- Portfolio (2.9+): `-portfolio` on a base PDF with repeated `-pf file [-pfd description] [-pfr relationship]`. A typical blank base is `-create-pdf AND -portfolio -pf ...`. Viewer support is limited (Adobe-centric).
- Split: `-split in.pdf [-chunk n] -o 'part%%%.pdf'`. The output directory must already exist. Encryption flags or `-recrypt` may be added so each part is encrypted.
- Split at bookmarks: `-split-bookmarks level in.pdf -o '@B.pdf'`.
- Split to size (2.7+): `-split-max 10MiB in.pdf -o 'part%%%.pdf'`; suffixes `kB KiB MB MiB GB GiB`.
- Spray/de-collate (2.7+): `-spray in.pdf -o a.pdf -o b.pdf ...`.
- Split naming: `%`, `%%`, etc. padded sequence; `@F` source stem; `@N` sequence; `@S`/`@E` chunk page bounds; `@B` bookmark; `@b10@` truncated bookmark.

## 3. Pages, boxes, and transforms

- Scale page and contents: `-scale-page 'sx sy' [position]`.
- Fit preserving aspect: `-scale-to-fit 'w h'`; modifiers `-scale-to-fit-scale n`, `-scale-to-fit-rotate-clockwise`, `-scale-to-fit-rotate-anticlockwise`, `-prerotate`, `-no-warn-rotate`, position.
- Stretch (2.7.2+): `-stretch 'w h'`.
- Change page size and center without scaling (2.8+): `-center-to-fit 'w h'`.
- Scale contents only: `-scale-contents factor [position]`.
- Shift contents: `-shift 'dx dy'`; shift boxes instead (2.7+): `-shift-boxes 'dx dy'`.
- Viewer rotation: `-rotate 0|90|180|270` absolute; `-rotateby ...` relative.
- Physical content rotation: `-rotate-contents angle`; normalize rotation/origin: `-upright`.
- Flip content: `-hflip`, `-vflip`.
- Set: `-mediabox`, `-cropbox`, `-artbox`, `-trimbox`, `-bleedbox 'minx miny width height'`. Prefix geometry with `?` for `minx miny maxx maxy`.
- Remove: `-remove-cropbox`, `-remove-artbox`, `-remove-trimbox`, `-remove-bleedbox`.
- Copy boxes: `-frombox /TrimBox -tobox /CropBox [-mediabox-if-missing]`.
- Hard clip: `-hard-box /TrimBox`; diagnose: `-show-boxes`; print marks: `-trim-marks` (requires trim box).

## 4. Encryption and decryption

- Encrypt: `-encrypt METHOD owner user [permissions] [-no-encrypt-metadata] in.pdf -o out.pdf`.
- Use `AES256ISO` for new PDFs. `40bit` and `128bit` are insecure; `AES256` is deprecated; `AES` is older 128-bit AES.
- Permissions: `-no-edit`, `-no-print`, `-no-copy`, `-no-annot`, `-no-forms`, `-no-extract`, `-no-assemble`, `-no-hq-print`.
- Prefix passwords with `-pw=` if they could be parsed as options.
- AES-256 Unicode passwords must already be SASLPrep-normalized UTF-8 truncated to 127 bytes; cpdf does not preprocess them.
- Decrypt: `-decrypt in.pdf owner=<owner-password> -o out.pdf`. User password cannot decrypt.
- `-decrypt-force` bypasses password/permission checks; require explicit approval.

## 5. Compression and removal of ancillary data

- Streams: `-decompress [-just-content] [-jbig2dec path]`, `-compress`.
- Lossless structural optimization: `-squeeze [-squeeze-log-to file] [-squeeze-no-pagedata]`. Adding `-squeeze` beside another operation squeezes on write. Deprecated `-squeeze-no-recompress` has no effect since 2.6. 2.9+ also squeezes xobjects nested inside xobjects.
- Remove ancillary data (2.9+): `-remove-article-threads`, `-remove-page-piece`, `-remove-web-capture`, `-remove-procsets`, `-remove-output-intents`. The 2.9 changelog also mentions removing alternate images, but the manual body never names that operation—confirm with local `-summary`.
- Image recompression is under `-process-images`; removal commands for annotations, metadata, files, fonts, text, and images are in their sections.

## 6. Bookmarks and generated TOC

- List: `-list-bookmarks [-utf8]`; JSON: `-list-bookmarks-json [-preserve-actions]`.
- Replace bookmarks from matching list format: `-add-bookmarks file` or `-add-bookmarks-json file`.
- Remove all: `-remove-bookmarks`.
- Expansion state: `-bookmarks-open-to-level n` (`0` closes all).
- Generate/prepend TOC: `-table-of-contents`; options `-toc-title text`, `-toc-no-bookmark`, `-toc-dot-leaders` (2.8+), `-font`, `-font-size`, `-embed-std14 dir`, `-process-struct-trees`, `-subformat`.
- Bookmark destinations include `/XYZ`, `/Fit`, `/FitH`, `/FitV`, `/FitR`, `/FitB`, `/FitBH`, `/FitBV` forms.

## 7. Presentations

`-presentation in.pdf [range] [-trans Split|Blinds|Box|Wipe|Dissolve|Glitter] [-duration seconds] [-effect-duration seconds] [-vertical] [-outward] [-direction degrees]`.

Omit `-trans` to remove transitions on selected pages. Direction values depend on transition (typically `0`, `90`, `180`, `270`, and Glitter `315`).

## 8. Stamps, watermarks, text, rectangles

- Stamp first page of another PDF: `-stamp-on stamp.pdf` or `-stamp-under stamp.pdf`; options include position, `-scale-stamp-to-fit`, `-relative-to-cropbox`, `-process-struct-trees` (stamp marked as artifact).
- Pagewise overlay: `-combine-pages over.pdf under.pdf` (output length follows the under file). Options: `-prerotate`, `-underneath` (2.8.1+), `-scale-stamp-to-fit` (2.8.1+), `-process-struct-trees`. The 2.9 synopsis inconsistently writes `-stamp-scale-to-fit`; prose and changelog use `-scale-stamp-to-fit`. Require an exact local `-summary`/`-help` match.
- Text: `-add-text 'text'` (default: 12pt black Times Roman, top-left, over the page). Put it behind content with `-underneath`. Remove text previously added by cpdf: `-remove-text`. `-shift` may be combined with `-add-text` for extra offset.
- Rectangle: `-add-rectangle 'w h'`; useful for visual hiding/highlighting, **not secure redaction**.
- Font: standard 14 via `-font` and `-font-size`; embed with `-embed-std14 dir`; custom TTF with `-load-ttf Name=file -font Name`.
- Styling: `-color` (named, gray, RGB, CMYK), `-opacity`, `-outline`, `-linewidth`, `-line-spacing`, `-justify-left`, `-justify-right`, `-justify-center`.
- Absolute positions: `-pos-left`, `-pos-center`, `-pos-right 'x y'`.
- Relative: `-top`, `-topleft`, `-topright`, `-left`, `-center`, `-right`, `-bottomleft`, `-bottom`, `-bottomright`, `-diagonal`, `-reverse-diagonal`; modifiers `-midline`, `-topline`, `-relative-to-cropbox`, `-prerotate`.
- Specials: `%Page`, `%PageDiv2`, `%roman`, `%Roman`, `%EndPage`, `%Label`, `%EndLabel`, `%filename`, `%Bookmark<n>`, `%URL[text|URL]`, date/time codes, `%%`.
- Bates: `%Bates` with `-bates n` or `-bates-at-range n`, optionally `-bates-pad-to width`.
- Low-level page content: `-prepend-content`, `-postpend-content`, `-stamp-as-xobject`.

## 9. Multipage operations

- Insert: `-pad-before`, `-pad-after` with ranges; `-pad-every n`; use `-pad-with page.pdf` instead of blank.
- Pad total: `-pad-multiple n` or `-pad-multiple-before n`.
- Whole-page emptying (2.7.2+): `-redact [range]`; optionally preserve/trim tags with `-process-struct-trees`.
- Impose to paper: `-impose size`; to grid: `-impose-xy 'x y'`; modifiers `-impose-columns`, `-impose-rtl`, `-impose-btt`, `-impose-margin`, `-impose-spacing`, `-impose-linewidth`.
- Legacy two-up: `-twoup`, `-twoup-stack`.
- Chop/de-impose (2.7+): `-chop 'x y'`, `-chop-h y`, `-chop-v x`; order modifiers `-chop-columns`, `-chop-rtl`, `-chop-btt`.

## 10. Annotations

- List text: `-list-annotations [range]`; structured: `-list-annotations-json [range]`. Chapter 19 sometimes writes `-output-annotations-json`; that is a slip—use `-list-annotations-json`.
- Add from JSON: `-set-annotations file [-underneath]`.
- Copy: `-copy-annotations from.pdf to.pdf [range] -o out.pdf`.
- Remove: `-remove-annotations [range]`.
- To replace, remove first and then set. JSON may contain dependent objects and page links; edit cautiously.

## 11. Information, metadata, opening behavior, labels

- Inspect: `-info`, `-page-info [range]`, `-pages`; JSON variants (2.7+): `-info-json`, `-page-info-json`; units `-in`, `-cm`, `-mm` (expanded in 2.8). `-info` also reports OpenAction, AcroForm/XFA, mark-info, language, subformats (PDF/A, PDF/X, PDF/E, PDF/VT, PDF/UA), and a page-size summary when present.
- Set old-style info: `-set-title`, `-set-author`, `-set-subject`, `-set-keywords`, `-set-creator`, `-set-producer`, `-set-create`, `-set-modify`, `-set-trapped`, `-set-untrapped`; optionally `-also-set-xmp` or `-just-set-xmp`.
- Main XMP: `-set-metadata file`, `-print-metadata`, `-remove-metadata`, `-create-metadata`, `-set-metadata-date date`. All streams (2.9+): `-remove-all-metadata`, `-extract-all-metadata -o directory`.
- Initial layout: `-set-page-layout SinglePage|OneColumn|TwoColumnLeft|TwoColumnRight|TwoPageLeft|TwoPageRight`.
- Initial mode: `-set-page-mode UseNone|UseOutlines|UseThumbs|FullScreen|UseOC|UseAttachments`; `-set-non-full-screen-page-mode`.
- Viewer booleans: `-hide-toolbar`, `-hide-menubar`, `-hide-window-ui`, `-fit-window`, `-center-window`, `-display-doc-title` followed by `true|false`.
- Initial destination: `-open-at-page`, `-open-at-page-fit`, `-open-at-page-custom destination`.
- Language (2.7.1+): `-set-language BCP47-tag`.
- Labels: `-add-page-labels [range]` with `-label-style DecimalArabic|LowercaseRoman|UppercaseRoman|LowercaseLetters|UppercaseLetters|NoLabelPrefixOnly`, `-label-prefix`, `-label-startval`, `-labels-progress`; list as text with `cpdf -print-page-labels in.pdf`, or as JSON (2.7+) with the exact operation `cpdf -print-page-labels-json in.pdf`; remove with `-remove-page-labels`.
- Size accounting: `-composition` or `-composition-json`.

## 12. Attachments and portfolios

- Attach one or more: repeat `-attach-file filename`; optional `-to-page n`; descriptions/relationships via `-afd`, `-afr` (2.9+).
- List: `-list-attached-files`; 2.9+ supports `-json` and `-include-data`.
- Extract all to an existing directory: `-dump-attachments in.pdf -o directory`. List names first; for safer filename sanitization omit `-raw` and `-utf8` by default, use a dedicated empty directory, and verify resolved outputs remain inside it.
- Remove all document/page attachments: `-remove-files`.
- Treat extracted files as untrusted. Never overwrite unrelated files in a nonempty extraction directory.

## 13. Images and rasterization

- List image objects (2.7+): `-list-images` or `-list-images-json`, with a range. Fields include object, pages, name, width, height, bytes, bpc, colour space, filter, mask type (`ExplicitMask`, `ColourKeyMask`, `SMask`, `SMaskInData`, `NoMask`), and mask object. Adding `-inline` to include inline images (object 0, name `/InlineImage`) requires 2.9+. 2.9 also reports CCITT flavour and lossy vs lossless JBIG2.
- Effective DPI: `-image-resolution` or `-image-resolution-json` plus threshold/range; all uses (2.7+): `-list-images-used` or `-list-images-used-json`. Add `-inline` (2.9+) to include inline images.
- Extract: `-extract-images [range] [-im magick] [-p2p pnmtopng] [-raw] [-dedup|-dedup-perpage] -o 'dir/%%%'`. Output directory must exist. `%objnum` may be used in the output name (2.8.1+). Inline extraction (`-inline`, filenames get `-inline`) and soft-mask extraction/`-merge-masks` (writes `*-combined` PNGs) require 2.9+. Lossy JBIG2 globals are written as `<n>.jbig2global`.
- Extract one object (2.9+): `-extract-single-image object ... -o stem`. Does not work for lossy JBIG2 images that share JBIG2Globals.
- Reprocess (2.7+): `-process-images` with ImageMagick/JBIG2 tools. Methods: `-jpeg-to-jpeg quality`, `-jpeg-to-jpeg-scale percent` (2.8+), `-jpeg-to-jpeg-dpi dpi` (2.8+), `-lossless-to-jpeg quality`, `-lossless-to-jpeg2000 n` (2.9+), `-jpeg2000-to-jpeg2000 n` (2.9+), `-lossless-resample percent`, `-lossless-resample-dpi dpi`, and `-1bpp-method JBIG2|JBIG2Lossy|CCITTG4|CCITTG3` (`CCITT*` require 2.9+). Set `CPDF_SHOW_EXT=true` to print the external-tool invocations. 2.9 can process lossless CMYK images.
- Thresholds: `-pixel-threshold`, `-length-threshold`, `-percentage-threshold`, `-dpi-threshold`, `-process-images-info`, `-resample-interpolate`, `-jbig2-lossy-threshold`; `-process-images-force` requires 2.9+.
- Rasterize pages into a PDF (2.8+): `-gs path -rasterize`; export images: `-output-image ... -o 'page%%%.png'`.
- Raster options: `-rasterize-gray`, `-rasterize-1bpp`, `-rasterize-jpeg`, `-rasterize-jpeggray`, `-rasterize-jpeg-quality`, `-rasterize-res`, `-rasterize-annots`, `-rasterize-no-antialias`, `-rasterize-downsample`; `-tobox /Box` for export. `-rasterize-alpha` and 8-bit alpha PNGs (`-png`, `-output-image`, `-draw`) require 2.9+.

## 14. Fonts

- List: `-list-fonts`; JSON (2.7+): `-list-fonts-json`.
- Character map: `-print-font-table font -print-font-table-page n in.pdf`.
- Copy embedded font to target pages: `-copy-font source.pdf -copy-font-page n -copy-font-name /Fname target.pdf [range]`.
- Remove embedded fonts: `-remove-fonts` (lossy/risky).
- Find unembedded: `-missing-fonts`; embed via Ghostscript: `-embed-missing-fonts -gs path` (may alter PDF).
- Extract font (2.7+): `-extract-font page,/Fname in.pdf -o fontfile`.

## 15. CPDFJSON

- Export: `-output-json in.pdf -o out.json`; options `-output-json-parse-content-streams`, `-output-json-no-stream-data` (not round-trippable), `-output-json-decompress-streams`, `-utf8`; `-output-json-clean-strings` is deprecated.
- Import: `-j in.json -o out.pdf`; cpdf repairs stream `/Length` values.
- File is an array of `[object-number, object]`. Object `-1` is cpdf's wrapper (`/CPDFJSONformatversion` currently 3, plus parse/stream/version flags). Object `0` is the trailer. Objects `1..n` are PDF objects.
- CPDFJSON wraps integers as `{"I": n}`, floats as `{"F": n}`, names as `{"N": "/Name"}`, Unicode as `{"U": "text"}`, streams as `{"S": [dictionary, data]}`. 2.9 allows Float/Int wrappers anywhere in CPDFJSON and bookmark JSON.
- Back up first. Arbitrary edits can corrupt semantics or security properties.

## 16. Optional content groups (layers)

- List UTF-8 names: `-ocg-list`.
- Rename: `-ocg-rename -ocg-rename-from old -ocg-rename-to new`.
- Ensure all groups appear in order: `-ocg-order-all`.
- Merge distinct groups with the same name: `-ocg-coalesce-on-name`.

## 17. Create PDFs

- Blank: `-create-pdf [-create-pdf-pages n] [-create-pdf-papersize size]` (default one A4 portrait page). In 2.9+, `-create-pdf` and friends may appear in the middle of an `AND` chain.
- Typeset UTF-8 text: `-typeset file [-create-pdf-papersize size] [-font name] [-font-size n]`.
- Images: `-png image.png`, `-jpeg image.jpg`, `-jpeg2000 image.jp2` (2.7.1+); repeat inputs to form pages.
- JBIG2 (2.7+): repeat `-jbig2 page`; optional `-jbig2-global data`, reset with `-jbig2-global-clear`.
- Tagged subformats on supported versions: `-subformat PDF/UA-1|PDF/UA-2 -title title` before relevant source.

## 18. Draw

Start with `in.pdf [range] -draw ...` or `-create-pdf AND -draw ...`.

- Paths: `-rect 'x y w h'`, `-to`, `-line`, `-bez`, `-bez23`, `-bez13`, `-circle`, `-close`; paint with `-stroke`, `-fill`, `-filleo`, `-strokefill`, `-strokefilleo`.
- Clip: `-clip`, `-clipeo`.
- Style: `-strokecol`, `-fillcol`, `-thick`, `-cap butt|round|square`, `-join miter|round|bevel`, `-miter`, `-dash`.
- Graphics state/matrix: `-push`, `-pop`, `-matrix`, `-mtrans`, `-mrot` (radians), `-mscale`, `-mshearx`, `-msheary`.
- Reuse: `-xobj-bbox`, `-xobj name ... -end-xobj`, `-use name`.
- Images: `-draw-jpeg`, `-draw-png`, `-draw-jpeg2000` (2.9+), then `-image name`.
- Transparency: `-fill-opacity`, `-stroke-opacity`.
- Text: `-bt ... -et`, `-text`, `-stext`, `-font`, `-font-size`, `-leading`, `-charspace`, `-wordspace`, `-textscale`, `-rendermode 0..7`, `-rise`, `-nl`, `-text-width`. One synopsis writes `-fontsize` for `-text-width`; use `-font-size`.
- Paragraphs (2.7.2+): `-para 'L200pt=text'`; `-paras` plus `-indent`; no automatic multipage flow.
- Continue/create page: `-newpage`.
- Structure (2.7.2+): place `-draw-struct-tree` before `-draw`; use `-tag/-end-tag`, `-stag/-end-stag`, `-auto-tags/-no-auto-tags`, `-artifact/-end-artifact`, `-no-auto-artifacts`, `-namespace`, `-eltinfo/-end-eltinfo`, `-rolemap`.

## 19. Tagged PDF and PDF/UA (2.7.1+; drawing additions 2.7.2+)

- Structure: `-print-struct-tree`, `-extract-struct-tree -o tree.json`, `-replace-struct-tree tree.json`, `-remove-struct-tree` (2.8.1+), `-mark-as-artifact` (2.8.1+).
- Verify: `-verify 'PDF/UA-1(matterhorn)' [-json]`; one checkpoint: `-verify-single id`. Verification is incomplete and does not cover human-only criteria.
- Marker only: `-mark-as PDF/UA-1|PDF/UA-2`; remove: `-remove-mark ...`. A marker does not make content conformant.
- Create: `-create-pdf-ua-1 title` or `-create-pdf-ua-2 title`; valid output still requires proper embedded fonts, language, metadata, and structure. PDF/UA-2 needs a top-level `Document` tag in the PDF2 namespace.
- Use `-process-struct-trees` and sometimes `-subformat` during merge/split/stamp/TOC/imposition/redaction.
- Remediation may involve metadata/title/display-title/language fixes, font re-embedding, annotation removal, or careful structure/JSON edits; re-run verification and arrange human review.

## 20. Miscellaneous, sanitization, low-level inspection

- Remove images: `-draft [-boxes]`; one named image (must not be reused on other pages): `-draft-remove-only "/Im1" [range]`. `-blacktext`/`-blacklines`/`-blackfills` do not affect outlined text or form text.
- Remove text: `-remove-all-text [range]`.
- Normalize colors: `-blacktext`, `-blacklines`, `-blackfills`; despite names, `-color` can choose another color.
- Clamp line thickness: `-thinlines value`; negative values to enforce a maximum require 2.9+.
- Deprecated cleanup: `-clean`; normal writing already garbage-collects.
- Version marker only: `-set-version n` (`4` = PDF 1.4; `10` = PDF 2.0). It does not convert features.
- IDs: `-copy-id-from source.pdf`, `-remove-id`.
- Spot colors: `-list-spot-colors`.
- Dictionary search/edit: `-print-dict-entry key [-json]`, `-remove-dict-entry key [-dict-entry-search value]`, `-replace-dict-entry key -replace-dict-entry-value value [...]`.
- Remove page clipping paths: `-remove-clipping [range]`.
- Object exploration (2.7+): `-obj`/`-obj-json` with chains such as `/Root/Pages/Count`, `1256/PageLabels`, `P20/Resources`.
- Object edit (2.7.2+): `-replace-obj 'path=value'`; `-remove-obj number`.
- Stream extraction (2.7+): `-extract-stream` or `-extract-stream-decompress spec [-o file|-stdout]`; replacement (2.8+): `-replace-stream spec -replace-stream-with file`.
- JavaScript (2.9+): `-contains-javascript in.pdf` prints boolean; `-remove-javascript in.pdf -o out.pdf`. This is not malware analysis.

## Date formats

PDF info dates: `D:YYYYMMDDHHmmSSOHH'mm'`; a contiguous prefix is allowed. XMP metadata dates use ISO-like `YYYY-MM-DDThh:mm:ssZ` (or timezone offset). The literal `now` is supported for relevant setters but hurts reproducibility.
