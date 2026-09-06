# agent-diansai-skill · 电赛中的人与 AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**基础不高，也能开始做真实项目。关键不是让 AI 一口气写完整题，而是学会与它配合。**

面向大一新生、第一次参加校赛/电赛，以及“AI 写了很多代码，但板子还是不对”的同学。

作者已确认获得 **2026 电赛省一等奖**。这次重开发从校赛循迹小车、人脸跟拍云台、H 题车载平衡滚球的项目资料与开发对话中提炼经验：人提供目标和现场反馈，AI 负责理解、查证、实现与分析，双方通过小实验推进。获奖是作者经历，不是新 skill 的效果实验，也不是使用后的获奖保证。

## 这次重新开发了什么

新主入口是 **[`diansai-collab`](skills/diansai-collab/SKILL.md)**，教的是如何协作，而不是再叠一层自动工程流程。

| 你现在的处境 | 它应该帮你做到 |
|---|---|
| 看不懂题，不知道从哪开始 | 用日常语言拆出一个可观察的小目标，不先布置整套课程 |
| 只会说“抖、不动、跑飞了” | 帮你把现象变成下一步能检查的问题 |
| AI 一直改 PID，效果越来越乱 | 区分代码、信号、机械、单位、时间与标定问题 |
| 编译过了，实物仍不对 | 分开软件检查、刷写、单模块动作和整机指标 |
| 新聊天又把旧错误走一遍 | 留下当前版本、已验证事实、失败尝试和下一步 |
| 比赛临近，功能还没合起来 | 一起决定先保住什么、验证什么、暂缓什么 |

**不是让新手当一个复制粘贴工具。** AI 要主动读工程、分析和实现；人要知道自己操作什么、看什么，以及何时停下来。陌生概念在用到时解释，不以术语量衡量水平。

## 一个真实问题怎样变成有效协作

“车碰到线还冲出去”并不自动等于 PID 太小。开发中，现场后来补充了线宽、触发路数和损坏通道，排查才聚焦到进线判据和捕线过程。

```text
人：我希望碰线后转进去，实际碰到边缘后还直走。线很窄，还有一路坏了。
AI：我先读进线判据与坏路屏蔽。这轮先确认是否识别到碰线，不同时改多组增益。
人：按明确步骤反馈触发状态、动作先后和测试结果。
AI：根据反馈修正判断，做最小改动并检查，再给下一轮实验。
```

这是协作过程概括，不是原始聊天逐字公开。更多见 [三个项目复盘](docs/ai-collaboration-retrospective.md) 和 [现场案例](skills/diansai-collab/references/field-cases.md)。

## 开始使用：先试一轮，再谈全流程

把这段发给能读取工程文件的 AI，并提供题面和项目路径：

> 请阅读本仓库的 `skills/diansai-collab/SKILL.md`，按其中的协作方式帮我做项目。我基础不高，请先读现有工程，解释当前目标。你负责能独立完成的代码检查与分析，我负责现场操作和反馈。这一轮只确定一个最小目标、成功现象和下一步；涉及烧录、接线或发布时先明确具体动作。

不支持 skill 的助手也可直接阅读这些 Markdown；具体加载方式以所用工具为准。只有聊天能力的助手需要你提供必要的代码或报错；没有本机文件证据时应明确说明。

### Windows / Codex 目录安装

```powershell
git clone https://github.com/54xkeee/agent-diansai-skill.git
cd agent-diansai-skill
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

- 默认仅安装新的 `diansai-collab`，降低新手入口负担。
- 目标为 `CODEX_HOME/skills`；未设置时使用 `~/.codex/skills`。
- 已存在的同名技能会先完整备份到 `CODEX_HOME/skill-backups`，再更新；旧安装中其他技能原样保留。
- 安装器只复制技能文件，不安装编译器、不连接板卡、不烧录。
- 成功退出和文件校验代表安装目录写入；另开会话显式调用 `$diansai-collab`，让助手说明是否读到该入口，再确认会话加载。
- 维护源是本仓库 `skills/`。直接改安装副本后再次安装会被更新覆盖；从备份恢复或把长期改进提交回维护源。

已有项目需要旧的专业工具时，按需安装：

```powershell
.\install.ps1 -SkillName stm32-keil
# 需要原来的整套技能时才使用：
.\install.ps1 -All
```

新入口独立工作，不要求先安装整套流程。旧安装留下的其他入口不会被自动禁用；若旧流程抢先执行，显式指定 `$diansai-collab` 并检查实际加载。

## 人与 AI 各自负责什么

| 人 | AI | 一起 |
|---|---|---|
| 选择目标、反馈限制、确认实物 | 读工程、解释、查证、实现和本地测试 | 决定下一次最小实验 |
| 接线、测量、拍摄、观察、紧急停机 | 把模糊现象转成可检查的问题 | 比较预期与实际，修正假设 |
| 决定比赛取舍、确认外部动作 | 保留可恢复改动和验证边界 | 留下让下一轮接得上的记录 |

AI 可以降低入门门槛，但实物接线核对、机械标定和现场测试仍要由人完成。基础弱不等于只能旁观，也不等于免去实物验证。

## 保留的专业能力

| Skill | 使用场景 |
|---|---|
| [diansai-collab](skills/diansai-collab/SKILL.md) | 默认入口：人与 AI 的沟通、分工、实验和交接 |
| [nuedc-full-runner](skills/nuedc-full-runner/SKILL.md) | 明确需要完整工程流程与多份文档时的可选入口 |
| [analyze-nuedc-task](skills/analyze-nuedc-task/SKILL.md) | 详细审题和工程任务包 |
| [nuedc-code-planner](skills/nuedc-code-planner/SKILL.md) | 明确请求多任务代码架构设计 |
| [stm32-keil](skills/stm32-keil/SKILL.md) | STM32/Keil 项目工具，先读脚本与项目约束再执行 |
| [stm32cubemx](skills/stm32cubemx/SKILL.md) | CubeMX 生成与 Keil 构建 |
| [planning-with-files-zh](skills/planning-with-files-zh/SKILL.md) | 需要较完整持久规划时按需使用 |

底层工具和生成示例保留，本次没有重新验证其全部固件行为。别把历史生成目录当作活动工程，也不要直接把示例固件刷到板上。

## 复盘、帖子与验证

- [AI 帮了什么、阻碍在哪里、我们如何配合](docs/ai-collaboration-retrospective.md)
- [可直接使用的反馈和交接方式](skills/diansai-collab/references/collaboration-cards.md)
- [2026 电赛省一经验分享 · 小红书文案](docs/xiaohongshu-post.md)
- [本次发布验证与剩余边界](docs/release-validation.md)

欢迎分享具体协作失败案例：目标是什么、AI 怎样理解、实际发生了什么、最后什么证据改变了判断。先去掉密码和个人信息，再提 [Issue](https://github.com/54xkeee/agent-diansai-skill/issues)。比起堆更多提示词，仓库更希望沉淀能让下一位同学少走弯路的办法。

[MIT](LICENSE) · [贡献方式](CONTRIBUTING.md)
