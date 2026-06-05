# Codex STM32 Local Workflow

这份工作流用于本地 Codex 线程处理 STM32 Keil/CubeMX 项目。目标是让每次任务都能按固定节奏完成：先弄清楚，再最小修改，最后验证和交付。

## 1. Intake

接到任务后，先判断任务类型：

- 生成或修改 `.ioc`
- 修改 HAL/C 用户代码
- 检查工程结构
- 烧录、调试、串口观察
- 生成示例、文档或工具脚本

必须先确认的信息：

- MCU 型号或开发板型号
- 使用的外设和目标行为
- 已知引脚连接
- 工程路径
- 编译工具链：Keil、CubeIDE、CMake 或其他

可以使用默认值但要写进假设的信息：

- UART 波特率默认 `115200`
- I2C 速率默认 `100000`
- 常规 PWM 频率默认 `10000`
- STM32F103 常见系统时钟默认按项目已有 `.ioc` 或 README 为准

## 2. Inspect

优先读取这些文件：

- `*.ioc`
- `Core/Src/main.c`
- `Core/Inc/main.h`
- `MDK-ARM/*.uvprojx`
- `README.md`
- `skills/stm32-keil/SKILL.md`

搜索时优先用：

```powershell
rg --files
rg "USER CODE|MX_|HAL_|GPIO|TIM|UART|USART|ADC|I2C|SPI|DMA"
```

不要在未理解项目结构前批量改文件。

## 3. Decide

改动前输出简短判断：

- 我理解的目标
- 当前项目状态
- 将要修改的文件
- 验证方式
- 无法自动验证的硬件步骤

如果存在多种实现方式，优先选最少改动、最贴近现有项目的一种。

## 4. Implement

修改原则：

- 只改完成任务必须改的内容。
- 不重排无关代码。
- 不删除用户已有代码。
- 在 `USER CODE BEGIN` / `USER CODE END` 区域内放用户逻辑。
- CubeMX 生成区不要手写业务逻辑。
- 新脚本放在 `skills/stm32-keil/scripts/`，新 `.ioc` 工具放在 `skills/stm32-keil/tools/`。

## 5. Verify

按任务选择验证方式：

```powershell
python skills/stm32-keil/scripts/check_project.py <project>
python skills/stm32-keil/tools/ioc_parser.py <file.ioc>
python skills/stm32-keil/tools/ioc_review.py <file.ioc>
python skills/stm32-keil/scripts/detect_probe.py
python skills/stm32-keil/scripts/cubeprog_flash.py list
python skills/stm32-keil/scripts/serial_console.py --list
```

如果需要烧录：

```powershell
python skills/stm32-keil/scripts/cubeprog_flash.py flash <project>
```

如果需要 OpenOCD 调试：

```powershell
python skills/stm32-keil/scripts/openocd_debug.py <project> flash
python skills/stm32-keil/scripts/openocd_debug.py <project> reset
```

## 6. Report

最终回复包含：

- 改动文件
- 完成的行为
- 已运行的验证命令和结果
- 没有运行的验证及原因
- 用户接下来需要在硬件上确认的事项

如果发现无关问题，只报告，不顺手修改。

## Quick Command Map

| 目标 | 命令 |
| --- | --- |
| 检查工程 | `python skills/stm32-keil/scripts/check_project.py <project>` |
| 识别探针 | `python skills/stm32-keil/scripts/detect_probe.py` |
| 列出串口 | `python skills/stm32-keil/scripts/serial_console.py --list` |
| 列出烧录器 | `python skills/stm32-keil/scripts/cubeprog_flash.py list` |
| 烧录工程 | `python skills/stm32-keil/scripts/cubeprog_flash.py flash <project>` |
| 查看例程 | `python skills/stm32-keil/scripts/list_examples.py` |
