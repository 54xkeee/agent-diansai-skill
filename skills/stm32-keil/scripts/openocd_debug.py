#!/usr/bin/env python3
"""OpenOCD flash and debug helper for STM32 targets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path


DEFAULT_SPEEDS_KHZ = "4000,1000,500"
DEFAULT_PROCESS_TIMEOUT = 30
DEFAULT_RETRY_DELAY = 1.0

# STM32 target config map keyed by MCU prefix
STM32_TARGET_MAP = {
    "STM32F0": "target/stm32f0x.cfg",
    "STM32F1": "target/stm32f1x.cfg",
    "STM32F2": "target/stm32f2x.cfg",
    "STM32F3": "target/stm32f3x.cfg",
    "STM32F4": "target/stm32f4x.cfg",
    "STM32F7": "target/stm32f7x.cfg",
    "STM32H7": "target/stm32h7x.cfg",
    "STM32L0": "target/stm32l0.cfg",
    "STM32L1": "target/stm32l1.cfg",
    "STM32L4": "target/stm32l4x.cfg",
    "STM32L5": "target/stm32l5x.cfg",
    "STM32G0": "target/stm32g0x.cfg",
    "STM32G4": "target/stm32g4x.cfg",
    "STM32U5": "target/stm32u5x.cfg",
    "STM32WB": "target/stm32wbx.cfg",
}
DEFAULT_TARGET_CFG = "target/stm32f1x.cfg"


def emit(event: dict) -> None:
    print(json.dumps(event, ensure_ascii=False), flush=True)


def find_openocd() -> str:
    env = os.environ.get("OPENOCD")
    if env and Path(env).is_file():
        return env
    found = shutil.which("openocd")
    if found:
        return found
    raise RuntimeError(
        "openocd not found. Set OPENOCD env var or add to PATH.\n"
        "Download: https://github.com/openocd-org/openocd/releases"
    )


def find_gdb() -> str:
    env = os.environ.get("ARM_NONE_EABI_GDB")
    if env and Path(env).is_file():
        return env
    found = shutil.which("arm-none-eabi-gdb")
    if found:
        return found
    raise RuntimeError(
        "arm-none-eabi-gdb not found. Set ARM_NONE_EABI_GDB env var or add to PATH."
    )


def find_firmware(project_dir: Path, explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.is_absolute():
            p = project_dir / p
        if not p.exists():
            raise RuntimeError(f"Firmware file not found: {p}")
        return p
    # Search order: CubeIDE Debug, Keil MDK, CMake build
    patterns = [
        "Debug/*.elf",
        "Debug/*.axf",
        "MDK-ARM/*/*.axf",
        "build/*.elf",
        "**/*.elf",
        "**/*.axf",
        "**/*.hex",
    ]
    for pattern in patterns:
        matches = sorted(project_dir.glob(pattern))
        if matches:
            return matches[0]
    raise RuntimeError(
        f"No firmware found in {project_dir}. "
        "Build the project first, or pass --firmware explicitly."
    )


def detect_target_cfg(project_dir: Path) -> str:
    # Check .ioc for MCU family
    ioc_files = list(project_dir.glob("*.ioc"))
    if ioc_files:
        text = ioc_files[0].read_text(encoding="utf-8", errors="replace")
        m = re.search(r"Mcu\.UserName\s*=\s*(STM32[A-Z0-9]+)", text, re.IGNORECASE)
        if m:
            prefix = m.group(1)[:7].upper()
            for key, cfg in STM32_TARGET_MAP.items():
                if prefix.startswith(key):
                    return cfg
    return DEFAULT_TARGET_CFG


def classify_failure(output: str) -> str:
    lowered = output.lower()
    if re.search(r"(can't find interface|no such file|configuration file not found)", lowered):
        return "configuration_error"
    if re.search(r"(no device found|unable to open|cmsis-dap not found|hla_swd)", lowered):
        return "probe_not_found"
    if re.search(r"(target not examined|debug reason|swd_multidrop)", lowered):
        return "transport_or_target_access_failure"
    if re.search(r"(flash verify|verify fail)", lowered):
        return "verify_failed"
    if re.search(r"(timed out|timeout)", lowered):
        return "transport_or_target_timeout"
    if re.search(r"(target locked|security bit|rdp)", lowered):
        return "target_locked_or_protected"
    if "error" in lowered or "failed" in lowered:
        return "openocd_error"
    return "unknown"


def should_retry(failure: str) -> bool:
    return failure in {
        "probe_not_found",
        "transport_or_target_access_failure",
        "verify_failed",
        "transport_or_target_timeout",
        "openocd_error",
    }


def run_openocd(
    openocd: str,
    args: list[str],
    speed_khz: int,
    timeout: int,
) -> tuple[bool, str]:
    full_args = [openocd, *args]
    emit({"event": "attempt", "backend": "openocd", "speed_khz": speed_khz, "argv": full_args})
    try:
        result = subprocess.run(
            full_args, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "timeout"


def openocd_args(interface_cfg: str, target_cfg: str, speed_khz: int, commands: list[str]) -> list[str]:
    args = [
        "-f", interface_cfg,
        "-f", target_cfg,
        "-c", f"adapter speed {speed_khz}",
    ]
    for cmd in commands:
        args += ["-c", cmd]
    return args


def run_with_retry(
    openocd: str,
    interface_cfg: str,
    target_cfg: str,
    speeds: list[int],
    commands: list[str],
    attempts_per_speed: int,
    timeout: int,
    retry_delay: float,
) -> tuple[bool, str]:
    last_output = ""
    for speed in speeds:
        for attempt in range(attempts_per_speed):
            if attempt > 0:
                time.sleep(retry_delay)
            args = openocd_args(interface_cfg, target_cfg, speed, commands)
            ok, output = run_openocd(openocd, args, speed, timeout)
            last_output = output
            if ok:
                return True, output
            failure = classify_failure(output)
            emit({"event": "failure", "category": failure, "speed_khz": speed})
            if not should_retry(failure):
                return False, output
    return False, last_output


def cmd_probe(
    project_dir: Path, openocd: str, interface_cfg: str, target_cfg: str,
    speeds: list[int], attempts: int, timeout: int, delay: float,
) -> int:
    commands = ["init", "reset halt", "reg", "resume", "shutdown"]
    ok, output = run_with_retry(openocd, interface_cfg, target_cfg, speeds, commands, attempts, timeout, delay)
    if ok:
        emit({"event": "completed", "operation": "probe"})
        return 0
    emit({"event": "failed", "operation": "probe", "output": output[-2000:]})
    return 1


def cmd_flash(
    project_dir: Path, openocd: str, interface_cfg: str, target_cfg: str,
    speeds: list[int], attempts: int, timeout: int, delay: float,
    firmware: str | None, verify: bool,
) -> int:
    fw = find_firmware(project_dir, firmware)
    emit({"event": "firmware", "path": str(fw)})
    flash_cmd = f"program {fw.as_posix()} {'verify ' if verify else ''}reset exit"
    commands = ["init", flash_cmd]
    ok, output = run_with_retry(openocd, interface_cfg, target_cfg, speeds, commands, attempts, timeout, delay)
    if ok:
        emit({"event": "completed", "operation": "flash", "firmware": str(fw)})
        return 0
    emit({"event": "failed", "operation": "flash", "output": output[-2000:]})
    return 1


def cmd_registers(
    project_dir: Path, openocd: str, interface_cfg: str, target_cfg: str,
    speeds: list[int], attempts: int, timeout: int, delay: float,
) -> int:
    commands = ["init", "reset halt", "reg", "shutdown"]
    ok, output = run_with_retry(openocd, interface_cfg, target_cfg, speeds, commands, attempts, timeout, delay)
    if ok:
        emit({"event": "completed", "operation": "registers", "output": output})
        return 0
    emit({"event": "failed", "operation": "registers", "output": output[-2000:]})
    return 1


def cmd_reset(
    project_dir: Path, openocd: str, interface_cfg: str, target_cfg: str,
    speeds: list[int], attempts: int, timeout: int, delay: float,
) -> int:
    commands = ["init", "reset run", "shutdown"]
    ok, output = run_with_retry(openocd, interface_cfg, target_cfg, speeds, commands, attempts, timeout, delay)
    if ok:
        emit({"event": "completed", "operation": "reset"})
        return 0
    emit({"event": "failed", "operation": "reset", "output": output[-2000:]})
    return 1


def cmd_run_to_symbol(
    project_dir: Path, openocd: str, interface_cfg: str, target_cfg: str,
    speeds: list[int], attempts: int, timeout: int, delay: float,
    firmware: str | None, symbol: str, gdb_path: str | None, gdb_port: int, server_timeout: int,
) -> int:
    fw = find_firmware(project_dir, firmware)
    gdb = gdb_path or find_gdb()
    # Start OpenOCD GDB server
    server_args = [openocd, "-f", interface_cfg, "-f", target_cfg,
                   "-c", f"adapter speed {speeds[0]}", "-c", "init", "-c", "reset halt"]
    emit({"event": "starting_gdb_server", "argv": server_args})
    server = subprocess.Popen(server_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    try:
        time.sleep(min(server_timeout, 3))
        gdb_cmds = [
            f"target remote :{gdb_port}",
            f"file {fw.as_posix()}",
            f"break {symbol}",
            "continue",
            "info registers",
            "quit",
        ]
        gdb_args = [gdb, "--batch", *[item for cmd in gdb_cmds for item in ("-ex", cmd)]]
        emit({"event": "gdb_command", "argv": gdb_args})
        result = subprocess.run(
            gdb_args, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        ok = result.returncode == 0
        output = result.stdout + result.stderr
        if ok:
            emit({"event": "completed", "operation": "run-to-symbol", "symbol": symbol, "output": output})
            return 0
        emit({"event": "failed", "operation": "run-to-symbol", "output": output[-2000:]})
        return 1
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()


def parse_speeds(value: str) -> list[int]:
    return [int(s.strip()) for s in value.split(",") if s.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project_dir", type=Path, help="Project root directory")
    parser.add_argument("--openocd", help="Path to openocd executable")
    parser.add_argument("--interface", default="interface/stlink.cfg", dest="interface_cfg")
    parser.add_argument("--target", help="OpenOCD target config (auto-detected from .ioc if omitted)")
    parser.add_argument("--speeds", default=DEFAULT_SPEEDS_KHZ)
    parser.add_argument("--attempts-per-speed", type=int, default=1)
    parser.add_argument("--process-timeout", type=int, default=DEFAULT_PROCESS_TIMEOUT)
    parser.add_argument("--retry-delay", type=float, default=DEFAULT_RETRY_DELAY)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("probe")
    flash_p = sub.add_parser("flash")
    flash_p.add_argument("--firmware")
    flash_p.add_argument("--no-verify", action="store_true")
    sub.add_parser("registers")
    sub.add_parser("reset")
    rts = sub.add_parser("run-to-symbol")
    rts.add_argument("--firmware")
    rts.add_argument("--symbol", default="main")
    rts.add_argument("--gdb")
    rts.add_argument("--gdb-port", type=int, default=3333)
    rts.add_argument("--server-timeout", type=int, default=5)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        openocd = args.openocd or find_openocd()
    except RuntimeError as exc:
        emit({"event": "error", "message": str(exc)})
        return 2
    speeds = parse_speeds(args.speeds)
    target_cfg = args.target or detect_target_cfg(args.project_dir)
    emit({"event": "config", "interface": args.interface_cfg, "target": target_cfg, "speeds_khz": speeds})
    common = dict(
        project_dir=args.project_dir,
        openocd=openocd,
        interface_cfg=args.interface_cfg,
        target_cfg=target_cfg,
        speeds=speeds,
        attempts=args.attempts_per_speed,
        timeout=args.process_timeout,
        delay=args.retry_delay,
    )
    try:
        if args.command == "probe":
            return cmd_probe(**common)
        if args.command == "flash":
            return cmd_flash(**common, firmware=args.firmware, verify=not args.no_verify)
        if args.command == "registers":
            return cmd_registers(**common)
        if args.command == "reset":
            return cmd_reset(**common)
        if args.command == "run-to-symbol":
            return cmd_run_to_symbol(
                **common, firmware=args.firmware, symbol=args.symbol,
                gdb_path=args.gdb, gdb_port=args.gdb_port, server_timeout=args.server_timeout,
            )
    except RuntimeError as exc:
        emit({"event": "error", "message": str(exc)})
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
