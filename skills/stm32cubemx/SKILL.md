---
name: stm32cubemx
description: Use when Codex needs to operate STM32CubeMX from the command line to validate or load .ioc files, generate STM32CubeMX projects, create Keil/MDK-ARM project files, run Keil UV4 command-line builds, inspect CubeMX/Keil logs, or diagnose STM32CubeMX generation and STM32 HAL project build failures.
---

# STM32CubeMX

Use this skill to turn `.ioc` validation into an actual STM32CubeMX and Keil build check, not just text parsing.

## Workflow

1. Start with an existing `.ioc` file. If the user only has a desired STM32 configuration, first create or obtain the `.ioc` using the relevant STM32 configuration skill or local tooling.
2. Prefer the bundled script:

```powershell
python "$env:USERPROFILE\.codex\skills\stm32cubemx\scripts\cubemx_generate_build.py" --ioc "D:\path\project.ioc" --build-keil --clean-keil-output
```

3. If CubeMX or Keil is not found, rerun with explicit paths:

```powershell
python "$env:USERPROFILE\.codex\skills\stm32cubemx\scripts\cubemx_generate_build.py" --ioc "D:\path\project.ioc" --cubemx "D:\STM32CubeMX" --uv4 "C:\Keil_v5\UV4\UV4.exe" --build-keil
```

4. Report the generated project directory, CubeMX log, Keil log, and whether the build produced `0 Error(s), 0 Warning(s)`.

## CubeMX Command Mode

Use STM32CubeMX quiet script mode for real validation:

```text
config load "<absolute .ioc path>"
project name <project_name>
project toolchain "MDK-ARM"
project path "<output root>"
project generate
exit
```

Run it on Windows as:

```powershell
& "<CubeMX>\jre\bin\java.exe" -jar "<CubeMX>\STM32CubeMX.exe" -q "<script file>"
```

Treat `config load` followed by `OK`, `project generate` followed by `OK`, and generated `Core/Src/main.c` as the baseline CubeMX success criteria.

## Keil Build Mode

Use `UV4.exe -b <project.uvprojx> -j0 -o <log>` for build verification. In this environment ARMCC V5 builds the CubeMX project reliably with Keil's default parallel setting.

Set `TEMP` and `TMP` to a writable folder before running Keil. ARMCC can fail with `cannot open embedded assembler output file "C:\WINDOWS\TEMP\..."` when the process cannot write to the default temp directory. This is an environment problem, not an `.ioc` problem.

The bundled script handles this by creating a local `keil_temp` folder and overriding `TEMP/TMP` for the build subprocess.

## Diagnosis Rules

- If CubeMX cannot load the `.ioc`, inspect the CubeMX log around `config load` first.
- If CubeMX loads but cannot generate, inspect the log around `project generate`.
- If Keil fails before compiling user files and mentions `C:\WINDOWS\TEMP`, rerun with a writable temp directory.
- If Keil reports `I/O error writing file ... .o`, retry with `--jobs 0 --clean-keil-output` and a writable local `TEMP/TMP`.
- If Keil compiles but links fail because object files are missing, read earlier compile errors; the link error is usually downstream.
- Ignore CubeMX update, advertisement image, and SQLite temp cleanup warnings unless they occur before `config load` or block `project generate`.
- Do not claim the firmware is hardware-tested unless flashing and board-level runtime checks were actually performed.

## Outputs

Keep validation artifacts near the `.ioc` unless the user requests a different destination:

```text
<ioc folder>/cubemx_project/<project_name>/
<ioc folder>/cubemx_verify_script.txt
<ioc folder>/cubemx_generate.log
<ioc folder>/keil_build.log
```
