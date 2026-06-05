#!/usr/bin/env python3
"""STM32CubeProgrammer CLI flash helper for STM32 targets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path


def emit(event: dict) -> None:
    print(json.dumps(event, ensure_ascii=False), flush=True)


def find_cubeprog() -> str:
    env = os.environ.get("STM32CUBEPROG")
    if env and Path(env).is_file():
        return env
    found = shutil.which("STM32_Programmer_CLI") or shutil.which("STM32_Programmer_CLI.exe")
    if found:
        return found
    # 默认安装路径
    default_paths = [
        r"C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe",
        r"C:\Program Files (x86)\STMicroelectronics\STM32Cube\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe",
        "/usr/local/STMicroelectronics/STM32Cube/STM32CubeProgrammer/bin/STM32_Programmer_CLI",
    ]
    for path in default_paths:
        if Path(path).is_file():
            return path
    raise RuntimeError(
        "STM32_Programmer_CLI not found. Install STM32CubeProgrammer or set STM32CUBEPROG env var.\n"
        "Download: https://www.st.com/en/development-tools/stm32cubeprog.html"
    )


def find_firmware(project_dir: Path, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = project_dir / p
        if not p.exists():
            raise RuntimeError(f"Firmware file not found: {p}")
        return p
    patterns = ["Debug/*.elf", "Debug/*.hex", "MDK-ARM/*/*.axf", "build/*.elf", "**/*.hex", "**/*.elf"]
    for pattern in patterns:
        matches = sorted(project_dir.glob(pattern))
        if matches:
            return matches[0]
    raise RuntimeError(f"No firmware found in {project_dir}. Build first or pass --firmware.")


def run_cubeprog(cubeprog: str, args: list[str], timeout: int = 60) -> tuple[bool, str]:
    full_args = [cubeprog, *args]
    emit({"event": "attempt", "backend": "cubeprog", "argv": full_args})
    try:
        result = subprocess.run(
            full_args, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "timeout"


def detect_connect_args(interface: str, serial: str | None) -> list[str]:
    """返回 -c 参数列表，根据接口类型构建连接字符串。"""
    if interface == "swd":
        conn = "port=SWD"
    elif interface == "jtag":
        conn = "port=JTAG"
    else:
        conn = f"port={interface}"
    if serial:
        conn += f" sn={serial}"
    return ["-c", conn]


def cmd_list_probes(cubeprog: str) -> int:
    ok, output = run_cubeprog(cubeprog, ["--list"])
    if ok or output:
        emit({"event": "completed", "operation": "list", "output": output})
        return 0
    emit({"event": "failed", "operation": "list", "output": output})
    return 1


def cmd_flash(
    project_dir: Path, cubeprog: str, interface: str, serial: str | None,
    firmware: str | None, verify: bool, reset: bool, timeout: int,
) -> int:
    fw = find_firmware(project_dir, firmware)
    emit({"event": "firmware", "path": str(fw)})
    connect_args = detect_connect_args(interface, serial)
    flash_args = [*connect_args, "-w", str(fw)]
    if verify:
        flash_args += ["-v"]
    if reset:
        flash_args += ["-rst"]
    ok, output = run_cubeprog(cubeprog, flash_args, timeout)
    if ok:
        emit({"event": "completed", "operation": "flash", "firmware": str(fw)})
        return 0
    emit({"event": "failed", "operation": "flash", "output": output[-2000:]})
    return 1


def cmd_reset(cubeprog: str, interface: str, serial: str | None, timeout: int) -> int:
    connect_args = detect_connect_args(interface, serial)
    ok, output = run_cubeprog(cubeprog, [*connect_args, "-rst"], timeout)
    if ok:
        emit({"event": "completed", "operation": "reset"})
        return 0
    emit({"event": "failed", "operation": "reset", "output": output[-2000:]})
    return 1


def cmd_read_option_bytes(cubeprog: str, interface: str, serial: str | None, timeout: int) -> int:
    connect_args = detect_connect_args(interface, serial)
    ok, output = run_cubeprog(cubeprog, [*connect_args, "-ob", "displ"], timeout)
    if ok or output:
        emit({"event": "completed", "operation": "read-ob", "output": output})
        return 0
    emit({"event": "failed", "operation": "read-ob", "output": output[-2000:]})
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cubeprog", help="Path to STM32_Programmer_CLI")
    parser.add_argument("--interface", default="swd", choices=["swd", "jtag", "uart", "usb"])
    parser.add_argument("--serial", help="Probe serial number (for multi-probe setups)")
    parser.add_argument("--timeout", type=int, default=60)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    flash_p = sub.add_parser("flash")
    flash_p.add_argument("project_dir", type=Path)
    flash_p.add_argument("--firmware")
    flash_p.add_argument("--no-verify", action="store_true")
    flash_p.add_argument("--no-reset", action="store_true")
    sub.add_parser("reset")
    sub.add_parser("read-ob")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        cubeprog = args.cubeprog or find_cubeprog()
    except RuntimeError as exc:
        emit({"event": "error", "message": str(exc)})
        return 2
    try:
        if args.command == "list":
            return cmd_list_probes(cubeprog)
        if args.command == "flash":
            return cmd_flash(
                args.project_dir, cubeprog, args.interface, args.serial,
                args.firmware, not args.no_verify, not args.no_reset, args.timeout,
            )
        if args.command == "reset":
            return cmd_reset(cubeprog, args.interface, args.serial, args.timeout)
        if args.command == "read-ob":
            return cmd_read_option_bytes(cubeprog, args.interface, args.serial, args.timeout)
    except RuntimeError as exc:
        emit({"event": "error", "message": str(exc)})
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
