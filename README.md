# stm32-skill 使用教程

STM32 嵌入式开发辅助工具集，从 [mspm0-skill](https://github.com/mc3545dada/mspm0-skill) 移植而来。

## 1. 环境准备

```bash
pip install pyserial
```

工具可选（按需安装）：
- **OpenOCD** — https://github.com/openocd-org/openocd/releases
- **STM32CubeProgrammer** — https://www.st.com/en/development-tools/stm32cubeprog.html
- **arm-none-eabi-gdb** — 随 Keil MDK 或 GNU Arm Toolchain 附带

## 2. 识别调试探针

```bash
python skills/stm32-keil/scripts/detect_probe.py
```

输出示例：
```
Probe 1: stlink
  Device: ST-Link/V2
  USB ID: 0483:3748
  Recommended backend: openocd
  Recommended config: interface/stlink.cfg
```

加 `--json` 获取机器可读输出。

## 3. 检查项目结构

```bash
python skills/stm32-keil/scripts/check_project.py D:/my_stm32_project
```

检查内容：
- `.ioc` 文件是否存在，读取 MCU 型号和外设列表
- 编译产物（`.elf` / `.axf` / `.hex`）是否存在
- `main.c` 的 `USER CODE` 区域是否完整
- HAL 驱动目录是否存在

## 4. 烧录固件

### 方式 A：STM32CubeProgrammer（推荐，支持 ST-Link）

```bash
# 自动查找编译产物烧录
python skills/stm32-keil/scripts/cubeprog_flash.py flash D:/my_stm32_project

# 指定固件文件
python skills/stm32-keil/scripts/cubeprog_flash.py flash D:/my_stm32_project --firmware Debug/my_project.elf

# 列出当前连接的探针
python skills/stm32-keil/scripts/cubeprog_flash.py list
```

### 方式 B：OpenOCD（支持 ST-Link / J-Link / CMSIS-DAP）

```bash
# 自动从 .ioc 检测目标型号
python skills/stm32-keil/scripts/openocd_debug.py D:/my_stm32_project flash

# 指定接口（默认 ST-Link）
python skills/stm32-keil/scripts/openocd_debug.py D:/my_stm32_project --interface interface/jlink.cfg flash

# 查看目标寄存器
python skills/stm32-keil/scripts/openocd_debug.py D:/my_stm32_project registers

# 复位运行
python skills/stm32-keil/scripts/openocd_debug.py D:/my_stm32_project reset

# 运行到 main 函数（需要 arm-none-eabi-gdb）
python skills/stm32-keil/scripts/openocd_debug.py D:/my_stm32_project run-to-symbol --symbol main
```

## 5. 串口调试

```bash
# 列出可用串口
python skills/stm32-keil/scripts/serial_console.py --list

# 打开串口监视（115200，Ctrl+C 退出）
python skills/stm32-keil/scripts/serial_console.py --port COM3

# 发送字符串
python skills/stm32-keil/scripts/serial_console.py --port COM3 --send "hello" --send-line

# 发送十六进制数据
python skills/stm32-keil/scripts/serial_console.py --port COM3 --send-hex "01 02 0A"

# 以十六进制显示接收内容
python skills/stm32-keil/scripts/serial_console.py --port COM3 --hex

# 运行 10 秒后自动退出
python skills/stm32-keil/scripts/serial_console.py --port COM3 --duration 10
```

## 6. 查看内置例程

```bash
python skills/stm32-keil/scripts/list_examples.py
```

输出：
```
Name               Complexity   Clock  Pins   Peripherals    Validated
led_blink          beginner     72MHz  PC13   GPIO           yes
pwm_breath_led     beginner     72MHz  PA8    TIM1, GPIO     yes
uart_blocking_tx   beginner     72MHz  PA9    USART1         yes
uart_dma_rx        intermediate 72MHz  PA9    USART1, DMA1   yes
```

例程源码在 `skills/stm32-keil/examples/<name>/main.c`，均基于 **STM32F103C8T6 (Blue Pill)**，HSE 8MHz → PLL × 9 → 72MHz。

## 7. 典型工作流

```
1. check_project.py    确认 .ioc 和编译产物
2. detect_probe.py     确认探针类型
3. cubeprog_flash.py   烧录
4. serial_console.py   串口验证输出
```

## 常见问题

**找不到 STM32_Programmer_CLI**
设置环境变量：`set STM32CUBEPROG=C:\path\to\STM32_Programmer_CLI.exe`

**找不到 openocd**
设置环境变量：`set OPENOCD=C:\path\to\openocd.exe`

**串口被占用**
关闭 Keil MDK 或 STM32CubeIDE 的串口监视器，再运行 serial_console.py。
