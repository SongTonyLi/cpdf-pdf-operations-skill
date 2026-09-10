# cpdf PDF Operations Agent Skill

A globally installable [Agent Skills](https://agentskills.io/) package that lets coding agents translate natural-language PDF requests into safe, version-compatible [Coherent PDF (cpdf)](https://www.coherentpdf.com/) CLI operations.

It covers inspection, page selection, merge/split, transforms, encryption, compression, bookmarks, stamps, metadata, attachments, images, fonts, annotations, CPDFJSON, drawing, optional content groups, PDF/UA workflows, and low-level inspection/sanitization.

## Install

Clone or copy this directory to a global Agent Skills location:

```bash
mkdir -p ~/.agents/skills
git clone <repository-url> ~/.agents/skills/cpdf-pdf-operations
```

Pi also discovers global skills under `~/.pi/agent/skills/`.

Install cpdf separately and ensure it is on `PATH`. If it is missing, the skill instructs the agent to stop and direct the user to <https://www.coherentpdf.com/>.

```bash
command -v cpdf
cpdf -version
python3 ~/.agents/skills/cpdf-pdf-operations/scripts/preflight.py
```

## Why runtime detection matters

The reference manual used to author this skill is cpdf 2.9, while users may have older releases. The skill always locates the user's cpdf, checks its version/help, and refuses to invent unavailable options. Version additions from 2.7 through 2.9 are documented in `references/version-compatibility.md`.

**Security:** cpdf 2.9's changelog records input sanitization against command injection. Do not process untrusted PDFs or attacker-controlled values with earlier releases; upgrade to 2.9+ first. Passing smoke tests on an older binary demonstrates compatibility, not security.

## Examples

Ask naturally:

- “Merge these three PDFs in order and add page numbers.”
- “Keep pages 1, 4 through 8, and the last two pages.”
- “Encrypt this with AES-256 and prevent copying.”
- “Add a translucent DRAFT watermark behind every page.”
- “Extract every attachment into a new folder.”
- “Check this PDF for JavaScript and remove it.” (cpdf 2.9+)
- “Verify PDF/UA-1 and explain the remaining human checks.” (cpdf 2.7.1+)

## Test

The smoke test creates isolated synthetic fixtures; it does not use personal PDFs.

```bash
python3 tests/smoke.py --workdir /tmp/cpdf-skill-smoke
```

It records a JSON report, performs operation-specific semantic assertions where cpdf exposes inspectable state, and marks newer-version scenarios as unsupported rather than issuing unknown commands. `tests/check_natural_language_cases.py` separately validates the static prompt-contract schema and documentation coverage; it is explicitly not a model-behavior test.

## Files

- `SKILL.md` — activation metadata and agent workflow
- `references/command-reference.md` — concise 2.9 operation-family reference
- `references/version-compatibility.md` — feature gates and external dependencies
- `references/natural-language-recipes.md` — outcome-to-command examples
- `scripts/preflight.py` — cpdf/helper discovery
- `scripts/validate_pdf.py` — output checks
- `tests/smoke.py` — reproducible functional and semantic smoke test
- `tests/check_natural_language_cases.py` — static intent-contract/schema validator
- `tests/natural_language_cases.json` — intent coverage cases (not executed model conversations)

## Licensing and source

The original skill files are MIT licensed. cpdf and its manual are separate products copyrighted and licensed by Coherent Graphics; neither is redistributed here. Review cpdf's terms, especially for commercial use.

Reference: *Coherent PDF Command Line Tools User Manual*, version 2.9 (2026), available from the vendor: <https://www.coherentpdf.com/>.
