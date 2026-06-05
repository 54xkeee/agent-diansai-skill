# 赛题长跑型 Agent 工作流设计计划

## 目标

设计一个面向 NUEDC/电赛赛题的 Codex 顶层工作流：用户第一轮直接丢完整赛题时，Agent 不直接生成一坨不可运行代码，而是长时间、有阶段地完成赛题消化、工程任务包、代码周期规划、STM32/Keil 落地与验证闭环设计。

## 阶段

| 阶段 | 状态 | 产物 |
| --- | --- | --- |
| 1. 理解用户目标 | complete | 明确“不硬编码 skill 调用”，而是设计可调度工作流 |
| 2. 调研 Agent 顶层设计理念 | complete | `findings.md` 中记录关键参考 |
| 3. 设计 NUEDC 工作流架构 | complete | 输出完整方案 |
| 4. 给出封装建议 | complete | 说明应放在 orchestrator skill、AGENTS.md 还是安装包 |
| 5. 实现 skill bundle | complete | 新增 `nuedc-full-runner`、模板、安装脚本，并纳入依赖 skill |

## 设计约束

- 不把 skill 调用写死成机械顺序。
- 第一轮允许长跑，但必须持续产出可恢复的中间文件。
- 未验证主矛盾前，不进入完整代码实现。
- 每个阶段必须有门槛、产物和停止条件。
- 赛题事实、推断、假设、待确认项必须分开。

## 当前决策

- 使用 `planning-with-files-zh` 作为持久工作记忆思想。
- 使用“单 Orchestrator + 专家 skill 作为能力模块”的架构。
- 避免多 agent 彼此交接失控，优先采用中心调度/manager pattern。
- 当前仓库作为完整 skill bundle：包含 `nuedc-full-runner`、`planning-with-files-zh`、`analyze-nuedc-task`、`nuedc-code-planner`、`stm32-keil`、`stm32cubemx`。
