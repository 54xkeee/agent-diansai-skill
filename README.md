# agent-diansai-skill · 电赛中的人与 AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**基础不高，也能开始做真实项目。关键不是让 AI 一口气写完整题，而是学会与它配合。**

面向大一新生、第一次参加校赛/电赛，以及“AI 写了很多代码，但板子还是不对”的同学。

作者已确认获得 **2026 电赛省一等奖**。本仓库从校赛循迹小车、人脸跟拍云台、H题车载平衡滚球的开发经历中提炼协作方法。第二轮复盘覆盖电赛目录30个历史主任务，通读去重用户文本并重点回读助手决策链，另检查44个子任务的可读交付/状态；不是挑几段成功聊天包装成“万能提示词”。获奖是作者经历，不是新skill的效果实验或使用后的获奖保证。[阅读范围与完整复盘](docs/diansai-dialogue-audit.md)

## 这次重新开发了什么

新主入口是 **[`diansai-collab`](skills/diansai-collab/SKILL.md)**，教的是如何协作，而不是再叠一层自动工程流程。

**核心发现：人和AI都可能局部正确，双方对同一个项目的理解却逐渐错开。** 左右通道与物理轮错位、复用方法时连目标一起复制、精细控制范围被当成比赛评分范围、刚修改的源码被当成板上固件——这些误差靠“再认真一点”解决不了。

新版要求AI保存关系和已纠正的区别；纠正后追踪受影响依赖；有正常任务时拿它作对照；迁移成功经验前检查工况；没有新证据时停止同类盲改。人负责带回现实，AI负责让现实真正改变下一步。

| 你现在的处境 | 它应该帮你做到 |
|---|---|
| 看不懂题，不知道从哪开始 | 用日常语言拆出一个可观察的小目标，不先布置整套课程 |
| 只会说“抖、不动、跑飞了” | 帮你把现象变成下一步能检查的问题 |
| AI一直改PID，效果越来越乱 | 保住正常路径，检查完整反馈配对，停止没有新证据的同类补丁 |
| 编译过了，实物仍不对 | 分开软件检查、刷写、单模块动作和整机指标 |
| 已经说清了，后来又误解 | 保存“方法≠目标、控制窗口≠评分窗口”等区别，不只存最新参数 |
| 比赛临近，功能还没合起来 | 一起决定先保住什么、验证什么、暂缓什么 |

**不是让新手当一个复制粘贴工具。** AI 要主动读工程、分析和实现；人要知道自己操作什么、看什么，以及何时停下来。陌生概念在用到时解释，不以术语量衡量水平。

## 一个真实问题怎样变成有效协作

开发中曾出现：固定PWM的Task1能直走，Task2一启用反馈，两侧速度差距却不断扩大。手推计数正向，并未证明反馈调节的是同一个物理轮。这个正常/异常对照比笼统的“车跑偏了”更有定位价值。

```text
人：Task1能走直线，Task2一边越来越快，另一边越来越慢。
AI：先保住Task1。我查Task2新接入的反馈与输出配对，不先改全局P。
人：我能给屏幕读数；你说具体看什么，不要只让我“确认闭环”。
AI：我把物理轮、反馈、PWM和显示对应起来，再给能区分问题的动作。
```

这是协作过程概括，不是原始聊天逐字公开，也不是本次新做的实机测试。更多见 [9条纠偏链的深度复盘](docs/diansai-dialogue-audit.md)、[现场案例](skills/diansai-collab/references/field-cases.md) 和 [18个情境的决策推演](docs/collaboration-replay.md)。

## 开始使用：先试一轮，再谈全流程

把这段发给能读取工程文件的 AI，并提供题面和项目路径：

> 请阅读本仓库的 `skills/diansai-collab/SKILL.md`。我基础不高，你先读现有工程并判断当前最值得解决的问题。能自己查的代码与计算由你负责；需要我观察实物时，说清动作、观察位置、停止条件，以及结果会改变哪个判断。保存我已纠正的概念区别，不把旧解释带到下一轮。涉及烧录、接线或发布时先明确具体动作。

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

- [第二轮：全量历史索引、9条纠偏链和共性机制](docs/diansai-dialogue-audit.md)
- [18个情境：行动推演及过度约束反查](docs/collaboration-replay.md)
- [初版：三个项目中AI帮了什么](docs/ai-collaboration-retrospective.md)
- [可直接使用的反馈和交接方式](skills/diansai-collab/references/collaboration-cards.md)
- [2026 电赛省一经验分享 · 小红书文案](docs/xiaohongshu-post.md)
- [本次发布验证与剩余边界](docs/release-validation.md)

欢迎分享具体协作失败案例：目标是什么、AI 怎样理解、实际发生了什么、最后什么证据改变了判断。先去掉密码和个人信息，再提 [Issue](https://github.com/54xkeee/agent-diansai-skill/issues)。比起堆更多提示词，仓库更希望沉淀能让下一位同学少走弯路的办法。

[MIT](LICENSE) · [贡献方式](CONTRIBUTING.md)
