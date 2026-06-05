#!/usr/bin/env python3
"""List built-in STM32 skill examples."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_manifests(examples_dir: Path) -> list[dict]:
    results = []
    for manifest in sorted(examples_dir.glob("*/manifest.json")):
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            data["_dir"] = manifest.parent.name
            results.append(data)
        except Exception as exc:
            results.append({"_dir": manifest.parent.name, "_error": str(exc)})
    return results


def fmt_clock(hz: int | None) -> str:
    if hz is None:
        return ""
    if hz >= 1_000_000:
        return f"{hz // 1_000_000}MHz"
    if hz >= 1_000:
        return f"{hz // 1_000}kHz"
    return str(hz)


def print_table(manifests: list[dict]) -> None:
    if not manifests:
        print("No examples found.")
        return
    rows = []
    for m in manifests:
        if "_error" in m:
            rows.append((m["_dir"], f"ERROR: {m['_error']}", "", "", "", ""))
            continue
        rows.append((
            m.get("name", m["_dir"]),
            m.get("complexity", ""),
            fmt_clock(m.get("cpuclk_hz")),
            ", ".join(m.get("pins", [])),
            ", ".join(m.get("peripherals", [])),
            "yes" if m.get("validated") else "",
        ))
    headers = ("Name", "Complexity", "Clock", "Pins", "Peripherals", "Validated")
    widths = [max(len(h), max(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    print(fmt.format(*headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt.format(*row))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--examples-dir", type=Path,
                        default=Path(__file__).parent.parent / "examples")
    args = parser.parse_args()
    manifests = load_manifests(args.examples_dir)
    if args.json:
        print(json.dumps(manifests, ensure_ascii=False, indent=2))
    else:
        print_table(manifests)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
