#!/usr/bin/env python3
"""Detect connected debug probes without opening or modifying the target."""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass


KNOWN_USB_IDS = {
    "0483:3744": ("stlink", "ST-Link/V1"),
    "0483:3748": ("stlink", "ST-Link/V2"),
    "0483:374B": ("stlink", "ST-Link/V2-1"),
    "0483:374D": ("stlink", "ST-Link/V3E"),
    "0483:3752": ("stlink", "ST-Link/V2-1 (MSD)"),
    "0483:374F": ("stlink", "ST-Link/V3 MINIE"),
    "EF1A:74E5": ("cmsis-dap", "Horco CMSIS-DAP"),
    "0D28:0204": ("cmsis-dap", "DAPLink CMSIS-DAP"),
}
KNOWN_USB_VENDORS = {
    "1366": ("jlink", "SEGGER J-Link"),
}


@dataclass
class Probe:
    kind: str
    display_name: str
    manufacturer: str
    usb_id: str
    serial_ports: list[str]
    confidence: str
    recommended_backend: str
    recommended_config: str
    evidence: list[str]


def run_command(command: list[str]) -> str:
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=15,
        )
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"command timed out after {exc.timeout} seconds") from exc
    if completed.returncode != 0:
        message = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(message or f"command failed: {' '.join(command)}")
    return completed.stdout


def normalize_usb_id(instance_id: str) -> str:
    match = re.search(r"VID_([0-9A-F]{4}).*PID_([0-9A-F]{4})", instance_id, flags=re.IGNORECASE)
    if match:
        return f"{match.group(1).upper()}:{match.group(2).upper()}"
    return ""


def probe_defaults(kind: str) -> tuple[str, str, str]:
    if kind == "stlink":
        return ("high", "openocd", "interface/stlink.cfg")
    if kind == "jlink":
        return ("high", "openocd", "interface/jlink.cfg")
    if kind == "cmsis-dap":
        return ("high", "openocd", "interface/cmsis-dap.cfg")
    return ("low", "confirm_with_user", "")


def classify_probe(text: str, usb_id: str = "") -> tuple[str, str, str, str, str]:
    if usb_id in KNOWN_USB_IDS:
        kind, mapped_name = KNOWN_USB_IDS[usb_id]
        confidence, backend, config = probe_defaults(kind)
        return (kind, confidence, backend, config, mapped_name)
    vid = usb_id.split(":")[0] if ":" in usb_id else ""
    if vid in KNOWN_USB_VENDORS:
        kind, mapped_name = KNOWN_USB_VENDORS[vid]
        confidence, backend, config = probe_defaults(kind)
        return (kind, confidence, backend, config, mapped_name)
    lowered = text.lower()
    if re.search(r"\b(j-?link|segger)\b", lowered):
        confidence, backend, config = probe_defaults("jlink")
        return ("jlink", confidence, backend, config, "")
    if re.search(r"\b(st-?link|stmicroelectronics)\b", lowered):
        confidence, backend, config = probe_defaults("stlink")
        return ("stlink", confidence, backend, config, "")
    if re.search(r"\b(cmsis[- ]?dap|daplink)\b", lowered):
        confidence, backend, config = probe_defaults("cmsis-dap")
        return ("cmsis-dap", confidence, backend, config, "")
    return ("unknown", "low", "confirm_with_user", "", "")


def first_string(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return ""


def as_list(value: object) -> list[dict[str, object]]:
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def windows_pnp_devices() -> list[dict[str, object]]:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        raise RuntimeError("PowerShell is unavailable")
    script = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$devices = Get-PnpDevice -PresentOnly -Class USB
$items = foreach ($device in $devices) {
    [PSCustomObject]@{
        FriendlyName = $device.FriendlyName
        Manufacturer = $device.Manufacturer
        InstanceId   = $device.InstanceId
    }
}
@($items) | ConvertTo-Json -Depth 3 -Compress
"""
    output = run_command([powershell, "-NoProfile", "-Command", script]).strip()
    return as_list(json.loads(output or "[]"))


def windows_serial_ports() -> list[dict[str, str]]:
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if not powershell:
        return []
    script = r"""
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
@(Get-CimInstance Win32_SerialPort | ForEach-Object {
    [PSCustomObject]@{ DeviceID = $_.DeviceID; PNPDeviceID = $_.PNPDeviceID }
}) | ConvertTo-Json -Depth 3 -Compress
"""
    try:
        output = run_command([powershell, "-NoProfile", "-Command", script]).strip()
        return [
            {k: str(v or "") for k, v in item.items()}
            for item in as_list(json.loads(output or "[]"))
        ]
    except (RuntimeError, json.JSONDecodeError):
        return []


def detect_windows() -> list[Probe]:
    devices = windows_pnp_devices()
    serial_ports = windows_serial_ports()
    probes: list[Probe] = []
    for device in devices:
        instance_id = first_string(device.get("InstanceId"))
        usb_id = normalize_usb_id(instance_id)
        texts = [
            t for t in (
                first_string(device.get("FriendlyName")).strip(),
                first_string(device.get("Manufacturer")).strip(),
            ) if t
        ]
        kind, confidence, backend, config, mapped_name = classify_probe(" | ".join(texts), usb_id)
        if kind == "unknown":
            continue
        ports: list[str] = []
        if usb_id:
            vid, pid = usb_id.split(":", 1)
            ports = sorted({
                p.get("DeviceID", "")
                for p in serial_ports
                if f"VID_{vid}&PID_{pid}" in p.get("PNPDeviceID", "").upper()
                and p.get("DeviceID")
            })
        probes.append(Probe(
            kind=kind,
            display_name=mapped_name or (texts[0] if texts else kind),
            manufacturer=first_string(device.get("Manufacturer")).strip(),
            usb_id=usb_id,
            serial_ports=ports,
            confidence=confidence,
            recommended_backend=backend,
            recommended_config=config,
            evidence=texts,
        ))
    return probes


def detect_linux() -> list[Probe]:
    root = "/sys/bus/usb/devices"
    if not os.path.isdir(root):
        return []
    probes: list[Probe] = []
    for name in os.listdir(root):
        device_dir = os.path.join(root, name)
        values: dict[str, str] = {}
        for field in ("product", "manufacturer", "idVendor", "idProduct"):
            try:
                with open(os.path.join(device_dir, field), encoding="utf-8", errors="replace") as f:
                    values[field] = f.read().strip()
            except OSError:
                values[field] = ""
        usb_id = (
            f"{values['idVendor'].upper()}:{values['idProduct'].upper()}"
            if values["idVendor"] and values["idProduct"] else ""
        )
        combined = " | ".join(v for v in (values["product"], values["manufacturer"]) if v)
        kind, confidence, backend, config, mapped_name = classify_probe(combined, usb_id)
        if kind == "unknown":
            continue
        probes.append(Probe(
            kind=kind,
            display_name=mapped_name or values["product"] or kind,
            manufacturer=values["manufacturer"],
            usb_id=usb_id,
            serial_ports=[],
            confidence=confidence,
            recommended_backend=backend,
            recommended_config=config,
            evidence=[v for v in (values["product"], values["manufacturer"]) if v],
        ))
    return probes


def detect_probes() -> list[Probe]:
    system = platform.system()
    if system == "Windows":
        return detect_windows()
    if system == "Linux":
        return detect_linux()
    raise RuntimeError(f"probe detection is not implemented on {system or 'this OS'}")


def print_text(probes: list[Probe]) -> None:
    if not probes:
        print("No supported debug probe detected.")
        print("Check USB connection or specify the flash backend manually.")
        return
    if len(probes) > 1:
        print(f"Detected {len(probes)} probes. Ask the user which one to use.")
        print()
    for i, probe in enumerate(probes, 1):
        print(f"Probe {i}: {probe.kind}")
        print(f"  Device: {probe.display_name}")
        if probe.manufacturer:
            print(f"  Manufacturer: {probe.manufacturer}")
        if probe.usb_id:
            print(f"  USB ID: {probe.usb_id}")
        if probe.serial_ports:
            print(f"  Serial ports: {', '.join(probe.serial_ports)}")
        print(f"  Confidence: {probe.confidence}")
        print(f"  Recommended backend: {probe.recommended_backend}")
        if probe.recommended_config:
            print(f"  Recommended config: {probe.recommended_config}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        probes = detect_probes()
    except (RuntimeError, json.JSONDecodeError) as exc:
        if args.json:
            print(json.dumps({"probes": [], "error": str(exc)}, ensure_ascii=False, indent=2))
        else:
            print(f"Probe detection failed: {exc}")
        return 2
    if args.json:
        print(json.dumps({"probes": [asdict(p) for p in probes]}, ensure_ascii=False, indent=2))
    else:
        print_text(probes)
    return 0 if probes else 1


if __name__ == "__main__":
    raise SystemExit(main())
