#!/usr/bin/env python3
"""Parse a STM32CubeMX .ioc file into a structured dict."""

from __future__ import annotations
import re
from pathlib import Path


def parse(path: Path) -> dict:
    """Return a dict with keys: mcu, peripherals, pins, rcc, nvic, dma, raw."""
    raw: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            raw[k.strip()] = v.strip()

    mcu = {
        "user_name": raw.get("Mcu.UserName", ""),
        "cpn": raw.get("Mcu.CPN", ""),
        "name": raw.get("Mcu.Name", ""),
        "package": raw.get("Mcu.Package", ""),
        "family": raw.get("Mcu.Family", ""),
    }

    ip_count = int(raw.get("Mcu.IPNb", "0"))
    peripherals = [raw.get(f"Mcu.IP{i}", "") for i in range(ip_count)]

    pin_count = int(raw.get("Mcu.PinsNb", "0"))
    pin_names = [raw.get(f"Mcu.Pin{i}", "") for i in range(pin_count)]

    pins: dict[str, dict] = {}
    for pname in pin_names:
        if pname.startswith("VP_"):
            continue
        signal = raw.get(f"{pname}.Signal", "")
        label = raw.get(f"{pname}.GPIO_Label", "")
        mode = raw.get(f"{pname}.Mode", "")
        pins[pname] = {"signal": signal, "label": label, "mode": mode}

    rcc = {k.split("RCC.", 1)[1]: v for k, v in raw.items() if k.startswith("RCC.")}
    nvic = {k.split("NVIC.", 1)[1]: v for k, v in raw.items() if k.startswith("NVIC.")}
    dma = {k.split("Dma.", 1)[1]: v for k, v in raw.items() if k.startswith("Dma.")}

    return {"mcu": mcu, "peripherals": peripherals, "pins": pins,
            "rcc": rcc, "nvic": nvic, "dma": dma, "raw": raw}


def find_conflicts(parsed: dict) -> list[str]:
    """Return list of conflict descriptions (duplicate pin assignments)."""
    seen: dict[str, str] = {}
    conflicts = []
    for pname, info in parsed["pins"].items():
        if not info["signal"]:
            continue
        label = info["label"] or info["signal"]
        base = re.sub(r"-.*", "", pname)  # PA0-WKUP -> PA0
        if base in seen:
            conflicts.append(f"Pin {base}: {seen[base]} vs {label}")
        else:
            seen[base] = label
    return conflicts


def validate(parsed: dict) -> list[str]:
    """Return list of issues found in the parsed .ioc."""
    issues = []
    issues.extend(find_conflicts(parsed))

    raw = parsed["raw"]
    # Each ADC channel needs a Rank entry
    adc_channels = int(raw.get("ADC1.NbrOfConversion", "0"))
    for i in range(adc_channels):
        if f"ADC1.Rank-{i}\\#ChannelRegularConversion" not in raw:
            issues.append(f"ADC1: missing Rank-{i} for channel {i}")

    # Each used TIM PWM channel needs SH.* entry
    for key in raw:
        if key.startswith("SH.S_TIM") and key.endswith(".ConfNb"):
            pass  # present
    for key in raw:
        if re.match(r"TIM\d\.Channel-PWM", key):
            ch = re.search(r"CH(\d)", key)
            tim = re.search(r"TIM(\d)", key)
            if ch and tim:
                sh_key = f"SH.S_TIM{tim.group(1)}_CH{ch.group(1)}.ConfNb"
                if sh_key not in raw:
                    issues.append(f"TIM{tim.group(1)} CH{ch.group(1)}: missing SH.* shared signal block")

    return issues


if __name__ == "__main__":
    import argparse, json, sys
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("ioc_file", type=Path)
    p.add_argument("--validate", action="store_true")
    args = p.parse_args()
    result = parse(args.ioc_file)
    if args.validate:
        issues = validate(result)
        if issues:
            print("Issues found:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        print("OK")
    else:
        result.pop("raw")
        print(json.dumps(result, ensure_ascii=False, indent=2))
