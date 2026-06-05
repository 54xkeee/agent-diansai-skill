# Code Architecture

## 目标

- 最终代码目标：
- 当前实现范围：
- 不实现：

## 已知输入

- 赛题任务包：
- 硬件：
- 传感器：
- 执行器：
- 当前代码：
- 约束：

## 模块设计

| 模块 | 职责 | 输入 | 输出 | 调用时机 | 失败信号 |
| --- | --- | --- | --- | --- | --- |
| app/task_state_machine |  |  |  |  |  |
| app/scheduler_or_main_loop |  |  |  |  |  |
| app/telemetry_or_log |  |  |  |  |  |
| drivers/sensor |  |  |  |  |  |
| drivers/actuator |  |  |  |  |  |
| modules/estimator |  |  |  |  |  |
| modules/controller |  |  |  |  |  |
| modules/task_logic |  |  |  |  |  |
| config |  |  |  |  |  |

## 共享状态

```text
raw input:
estimated state:
target:
control output:
task state:
health/fault:
```

## 最小状态机

```text
BOOT -> IDLE -> TEST_IO -> BASIC_TASK -> FINISHED
                      \-> FAILSAFE
```

## 主矛盾代码设计

### Hard Point 1

- Why it controls the score:
- Data needed:
- State variables:
- Algorithm skeleton:
- Logs:
- Verification gate:
- Fallback:
- Do not implement yet:

### Hard Point 2

- Why it controls the score:
- Data needed:
- State variables:
- Algorithm skeleton:
- Logs:
- Verification gate:
- Fallback:
- Do not implement yet:

## 实现周期

| Cycle | 目标 | 产物 | 验证门槛 |
| --- | --- | --- | --- |
| 1 | 框架 + 基础 IO 可观测 |  |  |
| 2 | 最小得分闭环 |  |  |
| 3 | 发挥项 + 集成 |  |  |
