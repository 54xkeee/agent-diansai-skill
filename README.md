# agent-diansai-skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-blue)](install.ps1)

STM32 嵌入式开发 + 电赛全流程 AI Skill 集合，适用于 Claude Code / Kiro / Codex 等 AI 编程助手。

---

## 快速开始

### 方法一：一键配置（把下面这段复制给 AI）

```
请帮我安装 agent-diansai-skill：

1. git clone https://github.com/54xkeee/agent-diansai-skill.git "$env:TEMP\agent-diansai-skill"
2. powershell -ExecutionPolicy Bypass -File "$env:TEMP\agent-diansai-skill\install.ps1"
3. Remove-Item -Recurse -Force "$env:TEMP\agent-diansai-skill"

安装完成后告诉我已安装的 skill 列表。
```

### 方法二：手动安装

```powershell
git clone https://github.com/54xkeee/agent-diansai-skill.git
cd agent-diansai-skill
powershell -ExecutionPolicy Bypass -File install.ps1
```

Skills 安装到 `~/.codex/skills/`，AI 自动加载。

---

## 包含的 Skill

| Skill | 用途 |
|---|---|
| [`nuedc-full-runner`](skills/nuedc-full-runner/SKILL.md) | 电赛/校赛全流程：赛题分析 → 代码架构 → 实现 → 验证 |
| [`stm32-keil`](skills/stm32-keil/SKILL.md) | STM32 Keil/CubeMX 项目：生成 .ioc、烧录、串口调试 |
| [`stm32cubemx`](skills/stm32cubemx/SKILL.md) | CubeMX headless 生成 + Keil UV4 构建验证 |
| [`analyze-nuedc-task`](skills/analyze-nuedc-task/SKILL.md) | 拆解赛题，输出得分路径、主矛盾、MVP |
| [`nuedc-code-planner`](skills/nuedc-code-planner/SKILL.md) | 代码架构设计，输出实现周期和验证门槛 |
| [`planning-with-files-zh`](skills/planning-with-files-zh/SKILL.md) | 多步骤任务持久化规划（task_plan / findings / progress） |

---

## 前置要求

```powershell
pip install pyserial
```

可选（按需安装）：

| 工具 | 用途 | 下载 |
|---|---|---|
| STM32CubeProgrammer | 烧录固件 | [st.com](https://www.st.com/en/development-tools/stm32cubeprog.html) |
| OpenOCD | 开源调试/烧录 | [openocd-org/openocd](https://github.com/openocd-org/openocd/releases) |
| STM32CubeMX 6.x | .ioc 生成验证 | [st.com](https://www.st.com/en/development-tools/stm32cubemx.html) |
| Keil MDK | 编译构建 | [keil.com](https://www.keil.com/download/product/) |

---

## 工具命令速查

### 项目检查与探针识别

```powershell
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\check_project.py" D:\my_project
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\detect_probe.py"
```

### 烧录

```powershell
# STM32CubeProgrammer（推荐）
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\cubeprog_flash.py" flash D:\my_project

# OpenOCD
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\openocd_debug.py" D:\my_project flash
```

### 串口调试

```powershell
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\serial_console.py" --list
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\serial_console.py" --port COM3
```

### CubeMX + Keil 构建验证

```powershell
python "$env:USERPROFILE\.codex\skills\stm32cubemx\scripts\cubemx_generate_build.py" `
  --ioc "D:\my_project\project.ioc" --build-keil
```

---

## 常见问题

**找不到 STM32_Programmer_CLI**
```powershell
$env:STM32CUBEPROG = "C:\path\to\STM32_Programmer_CLI.exe"
```

**找不到 openocd**
```powershell
$env:OPENOCD = "C:\path\to\openocd.exe"
```

**串口被占用**：关闭 Keil MDK 或 STM32CubeIDE 的串口监视器。

---

## 贡献

欢迎提 Issue 或 PR，详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## License

[MIT](LICENSE)
