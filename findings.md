# Agent 工作流设计调研记录

## 关键参考

### Anthropic: Building Effective Agents

- 区分 workflow 与 agent：workflow 适合可预先组织的路径，agent 适合更开放、需要自主决策的任务。
- 常见模式包括 prompt chaining、routing、parallelization、orchestrator-workers、evaluator-optimizer。
- 对复杂编码任务，orchestrator-workers 适合由中心调度器动态拆分任务。
- 对有明确评价标准的任务，evaluator-optimizer 适合做迭代改进。

### OpenAI Agents SDK / Practical Guide

- Agent 应由指令、工具、guardrails、handoffs、session/state 组成。
- 多 agent 常见两种模式：manager 将专家 agent 当工具调用；handoff 让专家接管流程。
- 可靠系统应有 run loop、退出条件、结构化输出、guardrails 和人类介入条件。
- 复杂系统应从单 agent 开始，必要时再扩展为多 agent。

### LangGraph

- 重点是持久化、checkpoint、thread state、人类介入和失败恢复。
- 对长任务来说，checkpoint 的核心价值是中断恢复、调试、回放和避免重复执行已成功步骤。

### Google ADK

- 强调层级化多 agent、工具生态、Sequential/Parallel/Loop 工作流、memory/session、artifact 管理和本地调试。
- 对本项目启发：不要只有聊天记忆，还要把赛题包、任务计划、日志和代码产物当 artifact 管理。

### CrewAI / AWS Bedrock Agents

- CrewAI 区分 Flows 与 Crews：Flow 更适合可控、事件驱动流程；Crew 更适合协作式专家团队。
- AWS Bedrock 多 agent 强调 supervisor/collaborator 层级模型，并要求明确角色边界、减少重叠职责。

## 对 NUEDC 工作流的启发

- 顶层应该是“可控 workflow + 局部 agentic 决策”，不是完全自治。
- 第一轮长跑需要 run loop 与 checkpoint，而不是一次回答。
- 专家 skill 不应互相抢控制权；由 Orchestrator 决定何时调用。
- 每个阶段都要输出 artifact：赛题事实表、得分路径、主矛盾、MVP、代码契约、验证日志。
- 进入代码前必须有验收门槛；没有门槛时应停止补问。
