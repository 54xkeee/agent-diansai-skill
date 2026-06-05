# STM32 嵌入式开发 Skill

## 概览

这个 skill 面向使用 Keil MDK / STM32CubeIDE / STM32CubeMX 开发 STM32 的场景，提供：

- 调试探针识别（ST-Link、J-Link、CMSIS-DAP）
- OpenOCD 烧录与调试（flash、probe、registers、run-to-symbol）
- STM32CubeProgrammer CLI 烧录
- 串口调试工具
- 项目结构检查（.ioc、Keil .uvprojx、编译产物）
- 内置例程库

## 目录结构

```
skills/stm32-keil/
├── SKILL.md            ← 本文件（AI 行为指令）
├── scripts/
│   ├── detect_probe.py       ← 探针识别
│   ├── serial_console.py     ← 串口收发测试
│   ├── openocd_debug.py      ← OpenOCD 烧录/调试
│   ├── cubeprog_flash.py     ← STM32CubeProgrammer CLI 烧录
│   ├── check_project.py      ← 项目结构检查
│   └── list_examples.py      ← 内置例程列表
└── examples/
    ├── empty_project/        ← 基础空工程
    ├── led_blink/            ← GPIO 翻转 LED
    ├── pwm_breath_led/       ← TIM PWM 呼吸灯
    ├── uart_blocking_tx/     ← USART 阻塞发送
    └── uart_dma_rx/          ← USART DMA 接收
```

## AI Agent 规则

### 修改原则

- **不要直接修改 CubeMX 生成的文件**（`stm32*_hal_*.c/h`、`main.c` 的 `USER CODE BEGIN/END` 以外区域）
- 用户代码只写在 `/* USER CODE BEGIN */` 和 `/* USER CODE END */` 块内
- 修改引脚/外设配置时先改 `.ioc`，再用 CubeMX 重新 Generate Code

### 烧录决策树

```
检测到探针？
├── ST-Link → cubeprog_flash.py 或 openocd_debug.py (interface/stlink.cfg)
├── J-Link  → openocd_debug.py (interface/jlink.cfg)
└── CMSIS-DAP → openocd_debug.py (interface/cmsis-dap.cfg)
```

### 编译产物

| 工具链 | 产物路径 | 格式 |
|--------|---------|------|
| Keil MDK | `MDK-ARM/<project>/<project>.axf` | ELF/AXF |
| STM32CubeIDE | `Debug/<project>.elf` | ELF |
| Make/CMake | `build/<project>.elf` | ELF |

### 串口调试

- 打开串口前关闭 Keil/CubeIDE 的串口监视器，避免端口占用
- 默认波特率 115200，8N1

### 项目检查流程

1. 运行 `check_project.py` 确认 .ioc、编译产物、探针状态
2. 再进行烧录或调试操作

## 安装

```bash
npx skills add mc3545dada/mspm0-skill@stm32-keil
```

或手动把 `skills/stm32-keil/` 复制到 `~/.claude/skills/stm32-keil/`。
