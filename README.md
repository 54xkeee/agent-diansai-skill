# agent-diansai-skill

STM32 嵌入式开发 + 电赛全流程 AI Skill 集合。

---

## 🚀 一键配置（复制给 AI）

> 把下面这段话直接发给支持 Claude Code / Kiro 的 AI，它会自动完成所有配置：

```
请帮我安装 agent-diansai-skill 工具集。

执行以下步骤：
1. 克隆仓库到本地临时目录：
   git clone https://github.com/54xkeee/agent-diansai-skill.git "$env:TEMP\agent-diansai-skill"

2. 运行安装脚本：
   powershell -ExecutionPolicy Bypass -File "$env:TEMP\agent-diansai-skill\install.ps1"

3. 安装完成后删除临时目录：
   Remove-Item -Recurse -Force "$env:TEMP\agent-diansai-skill"

4. 告诉我哪些 skill 已安装成功，以及可以用哪些命令。
```

---

## 包含的 Skill

| Skill 名称 | 触发场景 | 功能 |
|---|---|---|
| `stm32-keil` | STM32 Keil/CubeMX 项目开发 | 生成 .ioc、烧录、串口调试、检查项目结构 |
| `stm32cubemx` | 需要 CubeMX CLI 验证或 Keil 构建 | CubeMX headless 生成 + Keil UV4 构建验证 |
| `nuedc-full-runner` | 给出完整电赛/校赛赛题，要求全流程跑通 | 赛题分析 → 代码架构 → 实现周期 → 验证 |
| `analyze-nuedc-task` | 需要拆解赛题、提取评分路径 | 输出得分闭环、主矛盾、MVP |
| `nuedc-code-planner` | 已有工程包，需要生成代码实现计划 | 模块设计、状态机、实现周期划分 |
| `planning-with-files-zh` | 多步骤任务需要持久化规划文件 | 维护 task_plan.md / findings.md / progress.md |

---

## 手动安装

### 前置要求

```powershell
pip install pyserial
```

可选工具（按需）：
- [STM32CubeProgrammer](https://www.st.com/en/development-tools/stm32cubeprog.html)
- [OpenOCD](https://github.com/openocd-org/openocd/releases)
- STM32CubeMX 6.x（Keil 构建验证用）

### 安装步骤

```powershell
git clone https://github.com/54xkeee/agent-diansai-skill.git
cd agent-diansai-skill
powershell -ExecutionPolicy Bypass -File install.ps1
```

Skills 会被安装到 `~/.codex/skills/`，AI 自动加载。

---

## Skill 使用方法

安装后，直接在 AI 对话中描述需求，AI 会自动调用对应 Skill。也可以用斜杠命令显式触发：

```
/nuedc-full-runner   # 电赛全流程
/stm32-keil          # STM32 Keil 项目
```

---

## stm32-keil 工具命令

### 识别调试探针

```powershell
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\detect_probe.py"
```

### 检查项目结构

```powershell
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\check_project.py" D:\my_project
```

### 烧录固件

```powershell
# STM32CubeProgrammer（推荐）
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\cubeprog_flash.py" flash D:\my_project

# OpenOCD
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\openocd_debug.py" D:\my_project flash
```

### 串口调试

```powershell
# 列出串口
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\serial_console.py" --list

# 打开监视（Ctrl+C 退出）
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\serial_console.py" --port COM3
```

### 查看内置例程

```powershell
python "$env:USERPROFILE\.codex\skills\stm32-keil\scripts\list_examples.py"
```

---

## stm32cubemx 工具命令

```powershell
# CubeMX 生成 + Keil 构建验证
python "$env:USERPROFILE\.codex\skills\stm32cubemx\scripts\cubemx_generate_build.py" `
  --ioc "D:\my_project\project.ioc" --build-keil

# 指定工具路径
python "$env:USERPROFILE\.codex\skills\stm32cubemx\scripts\cubemx_generate_build.py" `
  --ioc "D:\my_project\project.ioc" `
  --cubemx "D:\STM32CubeMX" `
  --uv4 "C:\Keil_v5\UV4\UV4.exe" `
  --build-keil
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

**串口被占用**
关闭 Keil MDK 或 STM32CubeIDE 的串口监视器。
