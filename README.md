# STM32 嵌入式开发 Skill

从 [mspm0-skill](https://github.com/mc3545dada/mspm0-skill) 移植，适配 STM32 HAL + Keil/CubeIDE 工具链。

## 功能

| 脚本 | 功能 | 原版对应 |
|------|------|---------|
| `detect_probe.py` | 识别 ST-Link/J-Link/CMSIS-DAP | `detect_probe.py` |
| `openocd_debug.py` | OpenOCD 烧录/调试/run-to-symbol | `openocd_debug.py` |
| `cubeprog_flash.py` | STM32CubeProgrammer CLI 烧录 | `ccs_dss_debug.py` 的 STM32 替代 |
| `check_project.py` | 检查 .ioc、编译产物、HAL 完整性 | `check_syscfg.py` |
| `serial_console.py` | 串口收发调试 | `serial_console.py` |
| `list_examples.py` | 列出内置例程 | `list_examples.py` |

## 内置例程

```
examples/
├── led_blink/          PC13 GPIO 翻转，500ms，验证时钟和 GPIO
├── pwm_breath_led/     TIM1_CH1 (PA8) PWM 呼吸灯，1kHz
├── uart_blocking_tx/   USART1 阻塞发送，115200
└── uart_dma_rx/        USART1 DMA 循环接收 + 回显
```

所有例程基于 STM32F103C8T6 (Blue Pill)，HSE 8MHz → PLL → 72MHz SYSCLK。

## 快速使用

```bash
# 检查项目结构
python skills/stm32-keil/scripts/check_project.py D:/my_project

# 识别调试探针
python skills/stm32-keil/scripts/detect_probe.py

# 烧录（ST-Link，自动查找编译产物）
python skills/stm32-keil/scripts/cubeprog_flash.py flash D:/my_project

# 烧录（OpenOCD，自动从 .ioc 检测目标型号）
python skills/stm32-keil/scripts/openocd_debug.py D:/my_project flash

# 串口监视
python skills/stm32-keil/scripts/serial_console.py --list
python skills/stm32-keil/scripts/serial_console.py --port COM3 --baud 115200

# 列出例程
python skills/stm32-keil/scripts/list_examples.py
```

## 与原版的差异

| 项目 | mspm0-skill | stm32-keil |
|------|-------------|------------|
| 配置文件 | `.syscfg` | `.ioc` |
| 编译产物 | `.out` | `.axf` / `.elf` / `.hex` |
| 烧录工具 | DSLite / OpenOCD | STM32CubeProgrammer / OpenOCD |
| 目标配置 | MSPM0 系列 | STM32 全系列（从 .ioc 自动检测） |
| IDE | CCS / Theia | Keil MDK / STM32CubeIDE |
| CCS DSS | ✅ | ❌（用 cubeprog_flash.py 替代） |

## 依赖

```bash
pip install pyserial   # serial_console.py 需要
```

其余脚本只依赖 Python 标准库。
