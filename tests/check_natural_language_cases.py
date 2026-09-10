#!/usr/bin/env python3
"""Validate natural-language intent fixtures and their documentation coverage.

This is a static contract/schema check, not a model-behavior evaluation.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import sys

REQUIRED_FAMILIES = {
    "basic", "ranges", "merge-split", "pages", "encryption", "compression",
    "bookmarks", "presentations", "stamps", "multipage", "annotations",
    "metadata", "attachments", "images", "fonts", "json", "layers", "create",
    "draw", "accessibility", "misc", "limitation", "preflight",
}
ALLOWED_FIELDS = {
    "id", "prompt", "expected_options", "expected_range", "expected_behavior",
    "minimum_version", "family",
}


def validate(root: Path) -> dict[str, object]:
    cases_path = root / "tests" / "natural_language_cases.json"
    cases = json.loads(cases_path.read_text())
    docs = "\n".join((root / name).read_text() for name in (
        "SKILL.md",
        "references/command-reference.md",
        "references/natural-language-recipes.md",
        "references/version-compatibility.md",
    ))
    errors: list[str] = []
    ids: set[str] = set()
    prompts: set[str] = set()
    families: set[str] = set()

    if not isinstance(cases, list) or not cases:
        return {"ok": False, "errors": ["case file must be a nonempty JSON array"]}

    for index, case in enumerate(cases):
        label = case.get("id", f"index-{index}") if isinstance(case, dict) else f"index-{index}"
        if not isinstance(case, dict):
            errors.append(f"{label}: case must be an object")
            continue
        unknown = set(case) - ALLOWED_FIELDS
        if unknown:
            errors.append(f"{label}: unknown fields {sorted(unknown)}")
        for field in ("id", "prompt", "family"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                errors.append(f"{label}: missing nonempty {field}")
        if case.get("id") in ids:
            errors.append(f"{label}: duplicate id")
        ids.add(case.get("id"))
        if case.get("prompt") in prompts:
            errors.append(f"{label}: duplicate prompt")
        prompts.add(case.get("prompt"))
        families.add(case.get("family"))

        expected = case.get("expected_options", [])
        behavior = case.get("expected_behavior")
        if not expected and not behavior and "expected_range" not in case:
            errors.append(f"{label}: no expected command/range/behavior")
        if expected:
            if not isinstance(expected, list) or not all(isinstance(x, str) and x for x in expected):
                errors.append(f"{label}: expected_options must be nonempty strings")
            else:
                for token in expected:
                    if token not in docs:
                        errors.append(f"{label}: expected token not documented: {token}")
        if "expected_range" in case and str(case["expected_range"]) not in docs:
            errors.append(f"{label}: expected range not documented: {case['expected_range']}")
        if "minimum_version" in case and not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", str(case["minimum_version"])):
            errors.append(f"{label}: invalid minimum_version")

    missing_families = REQUIRED_FAMILIES - families
    if missing_families:
        errors.append(f"missing families: {sorted(missing_families)}")

    behavior_text = " ".join(str(case.get("expected_behavior", "")) for case in cases).lower()
    for phrase in ("no ocr", "secure redaction", "command -v cpdf", "https://www.coherentpdf.com/"):
        if phrase not in behavior_text:
            errors.append(f"safety/preflight behavior missing phrase: {phrase}")

    return {
        "ok": not errors,
        "kind": "static-schema-and-documentation-coverage",
        "not_model_behavior_test": True,
        "cases": len(cases),
        "families": sorted(families),
        "errors": errors,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    report = validate(root)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
