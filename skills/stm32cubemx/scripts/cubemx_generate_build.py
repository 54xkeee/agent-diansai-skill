#!/usr/bin/env python3
"""Load a .ioc with STM32CubeMX, generate a project, and optionally build with Keil UV4."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def existing_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(os.path.expandvars(value)).expanduser()
    return path if path.exists() else None


def registry_cubemx_locations() -> list[Path]:
    if os.name != "nt":
        return []
    try:
        import winreg
    except ImportError:
        return []

    roots = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    found: list[Path] = []
    for hive, root_name in roots:
        try:
            root = winreg.OpenKey(hive, root_name)
        except OSError:
            continue
        with root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                try:
                    subkey_name = winreg.EnumKey(root, i)
                    subkey = winreg.OpenKey(root, subkey_name)
                except OSError:
                    continue
                with subkey:
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                    except OSError:
                        continue
                    if "STM32CubeMX" not in str(display_name):
                        continue
                    for value_name in ("InstallLocation", "DisplayIcon", "UninstallString"):
                        try:
                            raw = str(winreg.QueryValueEx(subkey, value_name)[0]).strip('"')
                        except OSError:
                            continue
                        if raw:
                            found.append(Path(raw.split(".exe", 1)[0] + ".exe") if ".exe" in raw else Path(raw))
    return found


def resolve_cubemx(explicit: str | None) -> tuple[Path, Path]:
    candidates: list[Path] = []
    for item in [explicit, os.environ.get("STM32CUBEMX")]:
        path = existing_path(item)
        if path:
            candidates.append(path)

    which = shutil.which("STM32CubeMX") or shutil.which("STM32CubeMX.exe")
    if which:
        candidates.append(Path(which))

    candidates.extend(registry_cubemx_locations())
    candidates.extend(
        [
            Path(r"D:\STM32CubeMX"),
            Path(r"C:\STM32CubeMX"),
            Path(r"C:\Program Files\STM32CubeMX"),
            Path(r"C:\Program Files\STMicroelectronics\STM32Cube\STM32CubeMX"),
            Path(r"C:\Program Files (x86)\STMicroelectronics\STM32Cube\STM32CubeMX"),
        ]
    )

    for candidate in candidates:
        if candidate.is_dir():
            exe = candidate / "STM32CubeMX.exe"
            java = candidate / "jre" / "bin" / "java.exe"
        else:
            exe = candidate
            java = candidate.parent / "jre" / "bin" / "java.exe"
        if exe.exists() and java.exists():
            return exe, java

    raise FileNotFoundError("STM32CubeMX not found. Pass --cubemx <install-dir-or-exe>.")


def resolve_uv4(explicit: str | None) -> Path:
    candidates: list[Path] = []
    for item in [explicit, os.environ.get("KEIL_UV4")]:
        path = existing_path(item)
        if path:
            candidates.append(path)

    which = shutil.which("UV4") or shutil.which("UV4.exe")
    if which:
        candidates.append(Path(which))

    candidates.extend([Path(r"C:\Keil_v5\UV4\UV4.exe"), Path(r"D:\Keil_v5\UV4\UV4.exe")])
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Keil UV4.exe not found. Pass --uv4 <path> or omit --build-keil.")


def run_command(args: list[str], log_path: Path, cwd: Path | None = None, env: dict[str, str] | None = None) -> int:
    proc = subprocess.run(args, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text((proc.stdout or "") + (proc.stderr or ""), encoding="utf-8")
    return proc.returncode


def write_cubemx_script(script_path: Path, ioc: Path, project_name: str, toolchain: str, project_root: Path) -> None:
    script = "\n".join(
        [
            f'config load "{ioc}"',
            f"project name {project_name}",
            f'project toolchain "{toolchain}"',
            f'project path "{project_root}"',
            "project generate",
            "exit",
            "",
        ]
    )
    script_path.write_text(script, encoding="utf-8")


def cubemx_ok(log_text: str, generated_project: Path) -> bool:
    return (
        'config load "' in log_text
        and "project generate" in log_text
        and "\nOK\n" in log_text
        and (generated_project / "Core" / "Src" / "main.c").exists()
    )


def find_uvprojx(project_dir: Path) -> Path:
    matches = sorted(project_dir.glob("**/*.uvprojx"))
    if not matches:
        raise FileNotFoundError(f"No .uvprojx found under {project_dir}")
    return matches[0]


def keil_build_ok(log_text: str) -> bool:
    return " - 0 Error(s), 0 Warning(s)." in log_text or "0 Error(s), 0 Warning(s)" in log_text


def run_keil_build(build_cmd: list[str], env: dict[str, str], timeout_s: int) -> bool:
    proc = subprocess.Popen(build_cmd, env=env)
    try:
        proc.wait(timeout=timeout_s)
        return False
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)
        return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ioc", required=True, type=Path, help="Absolute or relative path to the .ioc file.")
    parser.add_argument("--project-name", help="Generated project name. Defaults to <ioc-stem>_CubeMXVerify.")
    parser.add_argument("--project-root", type=Path, help="Output root. Defaults to <ioc-dir>/cubemx_project.")
    parser.add_argument("--toolchain", default="MDK-ARM", help='CubeMX toolchain, usually "MDK-ARM".')
    parser.add_argument("--cubemx", help="STM32CubeMX install directory or STM32CubeMX.exe path.")
    parser.add_argument("--build-keil", action="store_true", help="Build generated .uvprojx with Keil UV4.")
    parser.add_argument("--uv4", help="Path to Keil UV4.exe.")
    parser.add_argument("--jobs", type=int, default=0, help="Keil parallel build jobs. Defaults to 0, matching UV4's automatic setting.")
    parser.add_argument("--keil-timeout", type=int, default=120, help="Seconds to wait for UV4 before killing it.")
    parser.add_argument("--clean-keil-output", action="store_true", help="Remove the Keil target output directory before building.")
    args = parser.parse_args()

    ioc = args.ioc.resolve()
    if not ioc.exists():
        print(f"ERROR: .ioc not found: {ioc}", file=sys.stderr)
        return 2

    project_name = args.project_name or f"{ioc.stem}_CubeMXVerify"
    project_root = (args.project_root or (ioc.parent / "cubemx_project")).resolve()
    generated_project = project_root / project_name
    script_path = ioc.parent / "cubemx_verify_script.txt"
    cubemx_log = ioc.parent / "cubemx_generate.log"
    keil_log = ioc.parent / "keil_build.log"

    try:
        cubemx_exe, java_exe = resolve_cubemx(args.cubemx)
        write_cubemx_script(script_path, ioc, project_name, args.toolchain, project_root)

        cmd = [str(java_exe), "-jar", str(cubemx_exe), "-q", str(script_path)]
        rc = run_command(cmd, cubemx_log, cwd=cubemx_exe.parent)
        cube_log_text = cubemx_log.read_text(encoding="utf-8", errors="replace")
        cube_ok = rc == 0 and cubemx_ok(cube_log_text, generated_project)

        print(f"CubeMX: {cubemx_exe}")
        print(f"CubeMX script: {script_path}")
        print(f"CubeMX log: {cubemx_log}")
        print(f"Generated project: {generated_project}")
        print(f"CubeMX status: {'OK' if cube_ok else 'FAILED'}")
        if not cube_ok:
            return 1

        if args.build_keil:
            uv4 = resolve_uv4(args.uv4)
            uvprojx = find_uvprojx(generated_project)
            if args.clean_keil_output:
                output_dir = uvprojx.parent / project_name
                if output_dir.exists():
                    shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            temp_dir = ioc.parent / "keil_temp"
            temp_dir.mkdir(parents=True, exist_ok=True)
            env = os.environ.copy()
            env["TEMP"] = str(temp_dir)
            env["TMP"] = str(temp_dir)
            build_cmd = [str(uv4), "-b", str(uvprojx), f"-j{args.jobs}", "-o", str(keil_log)]
            timed_out = run_keil_build(build_cmd, env, args.keil_timeout)
            build_text = keil_log.read_text(encoding="utf-8", errors="replace") if keil_log.exists() else ""
            build_ok = keil_build_ok(build_text)
            print(f"Keil UV4: {uv4}")
            print(f"Keil project: {uvprojx}")
            print(f"Keil log: {keil_log}")
            if timed_out:
                print(f"Keil timeout: killed UV4 after {args.keil_timeout}s")
            print(f"Keil status: {'OK' if build_ok else 'FAILED'}")
            return 0 if build_ok else 1

        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
