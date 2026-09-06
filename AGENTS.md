# Codex Local Workflow

## Communication

- 默认使用中文与用户沟通，除非用户明确要求其他语言。
- 动手前先说明假设；如果需求有多种解释，先把分歧点说清楚。
- 不确定且无法从本地上下文判断时，先问用户，不要静默猜测。

## Working Style

- 简单优先：只做用户明确要求的事，不添加 speculative 功能。
- 精准改动：只触碰完成任务必须修改的文件。
- 保留用户改动：发现未提交或非本轮修改的内容时，不要回滚；相关则兼容，无关则忽略。
- 匹配现有风格：代码、文档结构、命名和脚本调用方式尽量沿用仓库已有模式。

## 电赛人机协作入口

普通电赛/校赛项目、初学者求助和现场调试优先使用 `skills/diansai-collab/SKILL.md`。以用户当轮目标为边界，AI 主动读工程、解释和实现，人反馈实物现象；通过最小实验推进。不要因为出现赛题 PDF 就自动长跑或创建整套文档。

## NUEDC Full Runner（可选）

仅在用户明确选择完整工程流程、工程任务包和分阶段文档时使用 `nuedc-full-runner`。它是专业工作方式，不是新手协作入口的必经前置。

工作方式：

1. 先创建或恢复 `task_plan.md`、`findings.md`、`progress.md`。
2. 先生成 `nuedc_task_package.md`，拆出得分路径、主矛盾、MVP 和验证门槛。
3. 再生成 `code_architecture.md` 和 `cycle_contract.md`。
4. 只实现当前最小可验证周期，不一次性写完整赛题代码。
5. 当前周期未通过验证门槛时，修复当前周期或停止提问，不继续堆功能。

## STM32 Skill Workflow

当任务明确涉及 STM32、Keil、CubeMX、`.ioc`、HAL、烧录、调试或串口验证时，优先按以下顺序工作：

1. 明确目标：确认 MCU 型号、外设、引脚、时钟、调试口和期望现象。
2. 检查现状：阅读相关 `.ioc`、源码、脚本、README 和 skill 文档。
3. 列出假设：对有合理默认值的参数直接说明默认值；对影响正确性且无默认值的信息先问用户。
4. 最小实现：只修改必要的 `.ioc`、源码、脚本或文档。
5. 自动验证：优先运行本仓库已有脚本，例如 `check_project.py`、`ioc_parser.py`、`ioc_review.py`。
6. 硬件验证：需要真实板卡、探针或串口时，先说明依赖，再使用 `detect_probe.py`、`cubeprog_flash.py`、`openocd_debug.py`、`serial_console.py`。
7. 交付总结：说明改了什么、验证了什么、哪些步骤需要用户在硬件上确认。

详细清单见 `workflows/codex-stm32-local.md`。

## Stop Conditions

- 缺少关键硬件信息，且继续猜测可能导致接线、烧录或芯片配置错误。
- 本地缺少必须的软件工具，例如 Keil、STM32CubeProgrammer、OpenOCD 或串口驱动。
- 需要真实硬件反馈，但当前环境无法访问板卡或串口。
