---
name: stm32-keil
description: Use when Codex needs to generate, review, validate, flash, debug, or diagnose STM32 Keil/CubeMX projects, especially .ioc files, HAL peripheral configuration, ST-Link/OpenOCD/CubeProgrammer flashing, and serial console workflows.
---

# STM32 Keil Skill

AI 工作规范文档。工具层（Python）保证格式正确，AI 负责意图理解和问答。

---

## 工作流程

```
1. 解析需求  → 识别外设列表、引脚意图
2. 问答补全  → 有缺失必填项时，一次性列出 + 默认值，等用户确认
3. 生成 .ioc → ioc_writer.py(mcu, config_dict) → project.ioc
4. 自动验证  → ioc_parser.py 回读 + check_project.py 冲突检查
5. 用户确认  → 提示用CubeMX打开验证无报错，确认后继续
```

---

## 引脚复用规则（冲突决策树）

STM32F103 常见复用冲突，遇到时**不问用户，直接报警告 + 推荐替代**：

| 引脚 | 复用1 | 复用2 | 推荐 |
|------|-------|-------|------|
| PA6 | TIM3_CH1（编码器） | SPI1_MISO | 编码器用PA6时，SPI1改用SPI2 |
| PA7 | TIM3_CH2（编码器） | SPI1_MOSI | 同上 |
| PA9 | TIM1_CH2（PWM） | USART1_TX | PWM用PA9时，调试串口改USART3(PB10) |
| PA10 | TIM1_CH3 | USART1_RX | 同上 |
| PB6 | I2C1_SCL | TIM4_CH1 | I2C用PB6时，TIM4 PWM改CH3(PB8)/CH4(PB9) |
| PB7 | I2C1_SDA | TIM4_CH2 | 同上 |

---

## 外设配置必填项

每类外设 AI 必须确认以下参数后才能生成 .ioc：

**TIM（PWM 输出）**
- `channel`：通道号（CH1/CH2/CH3/CH4）
- `pin`：对应引脚（从下表查，唯一）
- `freq_hz`：PWM 频率（默认 10000）
- `period` 和 `prescaler` 由工具根据 `sysclk=72MHz` 和 `freq_hz` 自动计算

**TIM（编码器）**
- `timer`：TIM2 或 TIM3（TIM1/TIM4 不支持编码器模式）
- `ch1_pin` / `ch2_pin`：固定映射，无需问用户（见下表）

**ADC**
- `channels`：通道号列表（IN0~IN15）
- `dma`：是否启用 DMA（默认 true，超过 2 路时强制 true）
- 采样时间默认 `ADC_SAMPLETIME_71CYCLES_5`，不问用户

**I2C**
- `bus`：I2C1 或 I2C2
- `speed_hz`：默认 100000，不问用户
- **不需要**填从机地址（地址是代码层的事，.ioc 不管）

**UART**
- `instance`：USART1/2/3
- `baudrate`：默认 115200，不问用户

**GPIO**
- `pin`：必须用户指定（自由GPIO没有固定映射）
- `direction`：output / input
- `pull`：输入时默认 PULLUP

---

## 固定引脚映射表（AI 自动确认，不问用户）

| 外设 | 信号 | 引脚 | 备注 |
|------|------|------|------|
| TIM1_CH1 | PWM | PA8 | 唯一映射 |
| TIM1_CH2 | PWM | PA9 | 唯一映射（注意与USART1_TX冲突） |
| TIM1_CH3 | PWM | PA10 | |
| TIM1_CH4 | PWM | PA11 | |
| TIM2_CH1 | 编码器A | PA0 | PA0 = PA0-WKUP，ioc写法特殊 |
| TIM2_CH2 | 编码器B | PA1 | |
| TIM3_CH1 | 编码器A | PA6 | |
| TIM3_CH2 | 编码器B | PA7 | |
| TIM4_CH1 | PWM | PB6 | 与I2C1_SCL冲突 |
| TIM4_CH2 | PWM | PB7 | 与I2C1_SDA冲突 |
| TIM4_CH3 | PWM | PB8 | |
| TIM4_CH4 | PWM | PB9 | |
| I2C1_SCL | I2C | PB6 | |
| I2C1_SDA | I2C | PB7 | |
| I2C2_SCL | I2C | PB10 | 与USART3_TX冲突 |
| I2C2_SDA | I2C | PB11 | 与USART3_RX冲突 |
| USART1_TX | UART | PA9 | 与TIM1_CH2冲突 |
| USART1_RX | UART | PA10 | |
| USART2_TX | UART | PA2 | |
| USART2_RX | UART | PA3 | |
| USART3_TX | UART | PB10 | |
| USART3_RX | UART | PB11 | |
| ADC1_IN8 | ADC | PB0 | |
| ADC1_IN9 | ADC | PB1 | |
| ADC1_IN10 | ADC | PC0 | |
| ADC1_IN11 | ADC | PC1 | |
| ADC1_IN12 | ADC | PC2 | |
| ADC1_IN13 | ADC | PC3 | |
| ADC1_IN14 | ADC | PC4 | |
| ADC1_IN15 | ADC | PC5 | |

---

## 易错点清单

1. **PA0 的 .ioc 写法**：信号名必须用 `S_TIM2_CH1_ETR`，引脚名写 `PA0-WKUP`，不是 `PA0`
2. **TIM1 是高级定时器**：需要额外写 `RepetitionCounter=0`；PWM 生成对应的 SH 块是 `SH.S_TIM1_CH1.0=TIM1_CH1,PWM Generation1 CH1`
3. **TB6612 STBY 引脚**：必须初始化为高电平（`GPIO_PIN_SET`），否则电机不工作
4. **DMA 通道固定映射**（F103）：ADC1 → DMA1_Channel1，USART3_TX → DMA1_Channel2，USART3_RX → DMA1_Channel3
5. **TIM4 作调度中断**：不需要任何通道，只需 TIM4 基础计时器配置 + NVIC 中断使能；VP 虚拟引脚必须写 `VP_TIM4_VS_ClockSourceINT`
6. **ADC 的 `Rank` 字段**：每个通道必须有对应的 `Rank-N` 字段（从1开始），缺失会导致 CubeMX 打开报错
7. **SH.* 共享信号块**：所有 TIM 通道和 ADC 通道都需要对应的 `SH.*` 块，AI 经常遗漏这部分
8. **NVIC 格式**：必须用 `true\:priority\:subpriority\:false\:false\:true\:...` 格式，不是简单的布尔值

---

## 问答策略

### 何时问用户

| 情况 | 处理 |
|------|------|
| 自由 GPIO 引脚未指定（蜂鸣器/LED/方向控制） | **必须问**，无法推断 |
| 总线类型不确定（灰度传感器 ADC 还是 I2C） | **必须问** |
| 同一引脚被两个功能争用 | 不问，报警告 + 推荐替代 |
| 外设参数有合理默认值（PWM频率/I2C速度/波特率） | 自动使用默认值，写入 assumptions |
| 外设参数影响正确性且无默认值（ADC通道列表） | **必须问** |

### 问答格式

一次性列出所有缺失项，不要逐个问：

```
需要确认以下信息才能生成 .ioc：

1. 蜂鸣器接哪个引脚？（如 PB12）
2. LED 接哪个引脚？（如 PB13）
3. 电机方向控制：AIN1/AIN2/BIN1/BIN2 接哪四个引脚？
4. TB6612 STBY 接哪个引脚？

以下参数已使用默认值，如需修改请说明：
- PWM 频率：20kHz（TIM1，Period=3599）
- 编码器模式：TI12（四倍频）
- I2C 速度：100kHz
- 调试串口：115200
```

---

## 验证步骤

### 自动验证（ioc_parser.py + check_project.py）

- 引脚无重复分配
- 所有 TIM 通道有对应 SH.* 块
- ADC 通道有对应 Rank 字段
- DMA 通道映射合法

### 手动验证（必须用户执行）

1. 用 STM32CubeMX 6.x 打开生成的 .ioc
2. 确认无报错弹窗
3. 检查引脚视图，确认引脚分配符合预期
4. Generate Code，确认 main.c 中初始化函数齐全

### CubeMX CLI 说明

CubeMX 6.x 的 `-q` headless 模式**不可靠**：
- 在无显示器环境（CI/SSH）可能静默失败
- 不建议在 skill 流程中依赖它做自动代码生成
- 可以用它做 .ioc 格式验证（打开不报错即为合法）

---

## .ioc 文件格式速查

格式为 INI key=value，大小写敏感。关键规则：

```ini
# MCU 信息
Mcu.UserName=STM32F103RCTx
Mcu.CPN=STM32F103RCT6
Mcu.Name=STM32F103R(C-D-E)Tx     # CubeMX 内部名，不同于 UserName

# 引脚信号（注意 PA0 的特殊写法）
PA0-WKUP.Signal=S_TIM2_CH1_ETR
PA0-WKUP.GPIO_Label=ENC_L_A

# 共享信号块（TIM/ADC 必须有）
SH.S_TIM1_CH1.0=TIM1_CH1,PWM Generation1 CH1
SH.S_TIM1_CH1.ConfNb=1

# NVIC 格式
NVIC.TIM4_IRQn=true\:1\:0\:false\:false\:true\:true\:true\:true

# 虚拟引脚（每个用到 ClockSource 的 TIM 都需要）
VP_TIM4_VS_ClockSourceINT.Mode=Internal
VP_TIM4_VS_ClockSourceINT.Signal=TIM4_VS_ClockSourceINT
```
