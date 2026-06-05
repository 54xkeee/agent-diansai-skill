#!/usr/bin/env python3
"""Serial console utility for STM32 UART testing."""

from __future__ import annotations

import argparse
import sys
import time

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("ERROR: pyserial not installed. Run: pip install pyserial", file=sys.stderr)
    raise SystemExit(1)


def parse_hex_payload(value: str) -> bytes:
    value = value.replace(",", " ").replace("0x", "").replace("0X", "")
    return bytes(int(b, 16) for b in value.split() if b)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="List available serial ports and exit")
    parser.add_argument("--port", help="Serial port (e.g. COM3 or /dev/ttyUSB0)")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--parity", default="N", choices=["N", "E", "O", "M", "S"])
    parser.add_argument("--stopbits", type=float, default=1.0, choices=[1.0, 1.5, 2.0])
    parser.add_argument("--send", help="Text string to send after opening port")
    parser.add_argument("--send-hex", help="Hex bytes to send, e.g. '01 02 0A'")
    parser.add_argument("--send-line", action="store_true", help="Append \\n to --send")
    parser.add_argument("--send-crlf", action="store_true", help="Append \\r\\n to --send")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat send N times")
    parser.add_argument("--interval", type=float, default=1.0, help="Interval between repeats (s)")
    parser.add_argument("--duration", type=float, default=0, help="Exit after N seconds (0 = run until Ctrl+C)")
    parser.add_argument("--hex", action="store_true", help="Display received bytes as hex")
    parser.add_argument("--timestamp", action="store_true", help="Prefix output with timestamp")
    return parser


def run_console(args: argparse.Namespace) -> int:
    payload: bytes | None = None
    if args.send_hex:
        payload = parse_hex_payload(args.send_hex)
    elif args.send:
        text = args.send
        if args.send_crlf:
            text += "\r\n"
        elif args.send_line:
            text += "\n"
        payload = text.encode()

    with serial.Serial(
        port=args.port,
        baudrate=args.baud,
        parity=args.parity,
        stopbits=args.stopbits,
        timeout=0.1,
    ) as ser:
        send_count = 0
        start = time.monotonic()
        next_send = start
        try:
            while True:
                now = time.monotonic()
                if args.duration and (now - start) >= args.duration:
                    break
                if payload and send_count < args.repeat and now >= next_send:
                    ser.write(payload)
                    send_count += 1
                    next_send = now + args.interval
                data = ser.read(256)
                if data:
                    ts = f"[{time.strftime('%H:%M:%S')}.{int((now % 1) * 1000):03d}] " if args.timestamp else ""
                    if args.hex:
                        print(ts + " ".join(f"{b:02X}" for b in data))
                    else:
                        sys.stdout.write(ts + data.decode(errors="replace"))
                        sys.stdout.flush()
        except KeyboardInterrupt:
            pass
    return 0


def main() -> int:
    args = build_parser().parse_args()
    if args.list:
        ports = serial.tools.list_ports.comports()
        if not ports:
            print("No serial ports found.")
        for p in sorted(ports):
            print(f"{p.device:12s} {p.description}")
        return 0
    if not args.port:
        print("ERROR: --port required. Use --list to see available ports.", file=sys.stderr)
        return 2
    return run_console(args)


if __name__ == "__main__":
    raise SystemExit(main())
