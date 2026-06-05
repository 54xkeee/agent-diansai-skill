#!/usr/bin/env python3
"""STM32 project structure checker — analog of mspm0-skill's check_syscfg.py."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def find_ioc(project_dir: Path) -> Path | None:
    matches = sorted(project_dir.glob("*.ioc"))
    return matches[0] if matches else None


def parse_ioc(ioc: Path) -> dict:
    info: dict = {"mcu": "", "toolchain": "", "ips": [], "pins": []}
    for line in ioc.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line.startswith("Mcu.UserName="):
            info["mcu"] = line.split("=", 1)[1]
        elif line.startswith("ProjectManager.TargetToolchain="):
            info["toolchain"] = line.split("=", 1)[1]
        elif re.match(r"Mcu\.IP\d+=", line):
            info["ips"].append(line.split("=", 1)[1])
        elif re.match(r"Mcu\.Pin\d+=", line) and "VP_" not in line:
            info["pins"].append(line.split("=", 1)[1])
    return info


def find_firmware(project_dir: Path) -> list[Path]:
    patterns = ["Debug/*.elf", "Debug/*.axf", "MDK-ARM/*/*.axf", "build/*.elf", "**/*.hex"]
    found: list[Path] = []
    for pat in patterns:
        for p in sorted(project_dir.glob(pat)):
            if p not in found:
                found.append(p)
    return found[:3]


def find_keil_project(project_dir: Path) -> Path | None:
    matches = sorted(project_dir.glob("**/*.uvprojx"))
    return matches[0] if matches else None


def find_cubeide_project(project_dir: Path) -> bool:
    return (project_dir / ".cproject").exists() or bool(list(project_dir.glob(".cproject")))


def detect_toolchain(project_dir: Path) -> str:
    if find_keil_project(project_dir):
        return "keil"
    if find_cubeide_project(project_dir):
        return "cubeide"
    if (project_dir / "CMakeLists.txt").exists():
        return "cmake"
    if (project_dir / "Makefile").exists():
        return "make"
    return "unknown"


def check_user_code_regions(project_dir: Path) -> list[str]:
    """Check that main.c has USER CODE regions (CubeMX generated properly)."""
    issues: list[str] = []
    main_c = project_dir / "Core/Src/main.c"
    if not main_c.exists():
        issues.append("Core/Src/main.c not found — run CubeMX Generate Code first")
        return issues
    text = main_c.read_text(encoding="utf-8", errors="replace")
    if "USER CODE BEGIN" not in text:
        issues.append("main.c has no USER CODE regions — may be manually written or corrupted")
    if "SystemClock_Config" not in text:
        issues.append("main.c missing SystemClock_Config — regenerate from .ioc")
    return issues


def run_checks(project_dir: Path) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    ioc = find_ioc(project_dir)
    if ioc:
        info.append(f"ioc: {ioc.name}")
        ioc_data = parse_ioc(ioc)
        if ioc_data["mcu"]:
            info.append(f"mcu: {ioc_data['mcu']}")
        if ioc_data["toolchain"]:
            info.append(f"toolchain_ioc: {ioc_data['toolchain']}")
        if ioc_data["ips"]:
            info.append(f"peripherals: {', '.join(ioc_data['ips'])}")
    else:
        warnings.append("No .ioc file found — cannot verify peripheral configuration")

    toolchain = detect_toolchain(project_dir)
    info.append(f"toolchain_detected: {toolchain}")
    if toolchain == "unknown":
        warnings.append("Cannot detect toolchain. Expected Keil .uvprojx, .cproject, CMakeLists.txt, or Makefile.")

    firmwares = find_firmware(project_dir)
    if firmwares:
        info.append(f"firmware: {', '.join(str(f.relative_to(project_dir)) for f in firmwares)}")
    else:
        warnings.append("No compiled firmware found — build the project first before flashing")

    errors.extend(check_user_code_regions(project_dir))

    # Check HAL drivers present
    hal_dir = project_dir / "Drivers/STM32F1xx_HAL_Driver"
    if not hal_dir.exists():
        # Try other families
        hal_dirs = list((project_dir / "Drivers").glob("STM32*HAL*")) if (project_dir / "Drivers").exists() else []
        if not hal_dirs:
            warnings.append("HAL driver directory not found under Drivers/ — run CubeMX Generate Code")

    return {"errors": errors, "warnings": warnings, "info": info}


def suggested_commands(project_dir: Path, toolchain: str, has_firmware: bool) -> list[str]:
    cmds: list[str] = []
    script_dir = Path(__file__).parent
    project_str = str(project_dir)
    cmds.append(f"python {script_dir}/detect_probe.py  # identify connected debug probe")
    if has_firmware:
        cmds.append(f"python {script_dir}/cubeprog_flash.py flash {project_str}  # flash via ST-Link")
        cmds.append(f"python {script_dir}/openocd_debug.py {project_str} flash  # flash via OpenOCD")
    cmds.append(f"python {script_dir}/serial_console.py --list  # list available serial ports")
    return cmds


def print_text(project_dir: Path, result: dict) -> None:
    print(f"Project: {project_dir}")
    print()
    for item in result["info"]:
        print(f"  {item}")
    print()
    if result["errors"]:
        print("Errors:")
        for e in result["errors"]:
            print(f"  ERROR: {e}")
    if result["warnings"]:
        print("Warnings:")
        for w in result["warnings"]:
            print(f"  WARN:  {w}")
    if not result["errors"] and not result["warnings"]:
        print("  No issues found.")
    toolchain = detect_toolchain(project_dir)
    has_firmware = bool(find_firmware(project_dir))
    print()
    print("Suggested commands:")
    for cmd in suggested_commands(project_dir, toolchain, has_firmware):
        print(f"  {cmd}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path, nargs="?", default=Path("."))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_checks(args.project_dir)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_text(args.project_dir, result)
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
