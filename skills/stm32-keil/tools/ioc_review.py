#!/usr/bin/env python3
"""Validate a generated .ioc against a reference and report differences."""

from __future__ import annotations
import argparse
import sys
from pathlib import Path

# allow running without package install
sys.path.insert(0, str(Path(__file__).parent))
from ioc_parser import parse, validate


def diff_ioc(generated: Path, reference: Path) -> None:
    gen = parse(generated)
    ref = parse(reference)

    print(f"=== Validation: {generated.name} ===\n")

    # 1. structural validation
    issues = validate(gen)
    if issues:
        print("AUTO-VALIDATION ISSUES:")
        for i in issues:
            print(f"  FAIL {i}")
    else:
        print("  PASS Auto-validation passed")
    print()

    # 2. peripheral diff
    gen_ips = set(gen["peripherals"])
    ref_ips = set(ref["peripherals"])
    missing_ips = ref_ips - gen_ips
    extra_ips   = gen_ips - ref_ips
    if missing_ips:
        print(f"MISSING peripherals (in reference but not generated): {', '.join(sorted(missing_ips))}")
    if extra_ips:
        print(f"EXTRA peripherals (generated but not in reference):   {', '.join(sorted(extra_ips))}")
    if not missing_ips and not extra_ips:
        print("  PASS Peripheral list matches")
    print()

    # 3. pin diff
    gen_pins = {p: v["label"] for p, v in gen["pins"].items()}
    ref_pins = {p: v["label"] for p, v in ref["pins"].items()}
    missing_pins = set(ref_pins) - set(gen_pins)
    extra_pins   = set(gen_pins) - set(ref_pins)
    mismatch = [(p, gen_pins[p], ref_pins[p])
                for p in gen_pins if p in ref_pins and gen_pins[p] != ref_pins[p]]

    if missing_pins:
        print("MISSING pins:")
        for p in sorted(missing_pins):
            print(f"  MISS {p}: {ref_pins[p]}")
    if extra_pins:
        print("EXTRA pins (not in reference):")
        for p in sorted(extra_pins):
            print(f"  XTRA {p}: {gen_pins[p]}")
    if mismatch:
        print("LABEL MISMATCH:")
        for p, g, r in sorted(mismatch):
            print(f"  DIFF {p}: generated='{g}' reference='{r}'")
    if not missing_pins and not extra_pins and not mismatch:
        print("  PASS Pin assignments match")
    print()

    total_issues = len(issues) + len(missing_ips) + len(extra_ips) + len(missing_pins) + len(mismatch)
    print(f"Summary: {total_issues} issue(s) found")
    return total_issues


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("generated", type=Path)
    p.add_argument("reference", type=Path, nargs="?",
                   help="Reference .ioc to diff against (optional)")
    args = p.parse_args()

    if args.reference:
        n = diff_ioc(args.generated, args.reference)
        return 0 if n == 0 else 1
    else:
        issues = validate(parse(args.generated))
        if issues:
            for i in issues: print(f"FAIL {i}")
            return 1
        print("PASS OK")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
