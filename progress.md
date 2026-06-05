# 赛题长跑型 Agent 工作流设计进度

## 2026-06-06

- 用户说明目标：不是硬编码 agent 工作流，而是希望第一轮输入完整赛题时，Codex 能长跑并按给定工作流逐步消化、规划、实现，避免直接生成不可运行代码。
- 读取了 `planning-with-files-zh`、`nuedc-code-planner`、`analyze-nuedc-task` 的 skill 设计。
- 调研了主流 agent 设计理念：Anthropic、OpenAI Agents SDK、LangGraph、Google ADK、CrewAI、AWS Bedrock Agents、MCP。
- 创建本地规划文件，用于记录本次设计依据和决策。
- 完成顶层设计方向：中心 Orchestrator 调度专家 skill，第一轮长跑但按阶段 checkpoint，不在主矛盾和 MVP 门槛前直接生成完整代码。
- 实现 `skills/nuedc-full-runner/`，包含上层 `SKILL.md`、`agents/openai.yaml` 和 4 个 artifact 模板。
- 将 `planning-with-files-zh` 与 `analyze-nuedc-task` 复制进仓库的 `skills/`，使当前仓库成为更完整的本地 skill bundle。
- 新增 `install.ps1`，可把 `skills/*` 安装到 `~/.codex/skills`。
- 更新 `AGENTS.md`，增加完整赛题优先使用 `nuedc-full-runner` 的本地入口规则。
- 已将新建的 `nuedc-full-runner` 安装到 `C:\Users\虚空之神\.codex\skills\nuedc-full-runner`；未覆盖已有 skill。
