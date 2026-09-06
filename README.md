# 电赛人机协作 Skill

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**基础不高，也能和 AI 一起推进真实的电赛项目。**

面向大一新生、第一次参加电赛的同学，以及已经开始做项目，却总在“让 AI 改代码 → 上板不对 → 再改代码”之间打转的人。

你不必先学完所有知识才开始，也不必把 AI 的每句话都当成正确答案。这个仓库帮助你建立一种合作方式：**AI 负责读工程、分析和实现；你带回实物的真实表现；双方根据证据决定下一步。**

[开始使用](#开始使用) · [看看现场案例](skills/diansai-collab/references/field-cases.md) · [阅读协作规则](skills/diansai-collab/SKILL.md)

## 这是什么？

Skill 是一份给 AI 阅读的工作说明。这里的默认入口 **`diansai-collab`**，不是一套现成的小车程序，也不是“一句话自动完成电赛”的提示词，而是约定 AI 在项目中如何与你配合：

- **听懂目标，而不只是照着关键词写代码。** “参考之前的方法”不等于“把之前的目标也搬过来”。
- **把模糊现象变成可检查的问题。** 你可以从“车一开就跑偏”开始，AI 应当说清该看什么，而不是要求你先掌握整套控制理论。
- **让你的纠正真正影响后续工作。** 左右轮对应改了，就要追查编码器、输出和显示；不是只改一处名字，然后继续沿用旧判断。
- **保住已经有效的部分。** 有一个任务正常、另一个异常时，先比较差异；连续修改没有带来新证据时，先停下盲改。
- **分清做到哪一步。** 代码编译通过、固件写入板子、机构动作正常、整机达到指标，是不同的结果。

它希望降低的是入门和沟通的门槛，而不是省掉接线核对、测量与现场验证。

## 开始使用

### 先用一个真实问题试一轮

下载本仓库，让能读取本地文件的 AI 阅读 [协作规则](skills/diansai-collab/SKILL.md)，再把下面这段与你的题面、工程路径一起发给它：

```text
请按 skills/diansai-collab/SKILL.md 与我合作。

我的目标：
现有工程的位置：
目前实物的表现：
我已经试过什么：

我基础不高，请先读工程，再确定下一步。
代码检查、计算和实现由你主动完成。
需要我观察实物时，请说清怎么做、看哪里、什么情况要停下，
以及不同结果会怎样影响你的判断。
```

不知道某一项怎么填，直接说“不清楚”即可。只有聊天功能的助手，可以粘贴协作规则，并按需要补充代码、照片和报错；它能判断的范围取决于你提供的材料。

**第一轮不追求整题做完。** 先做到：你知道下一步做什么，AI 知道为什么做，结果回来后双方能继续往下走。

### 在 Windows 上安装到 Codex

已安装 Git 的情况下，在终端执行：

```powershell
git clone https://github.com/54xkeee/agent-diansai-skill.git
cd agent-diansai-skill
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

默认只安装 `diansai-collab`。安装后开启新会话，发送：

```text
$diansai-collab
请先确认你已读到这个 skill，再查看我的工程。
```

安装器只复制技能文件，不安装编译器，也不操作板卡。现有同名技能会先备份；其他技能保持原样。

<details>
<summary>安装位置、更新与按需安装</summary>

- 安装位置为 `CODEX_HOME/skills`；未设置时使用 `~/.codex/skills`。
- 同名技能备份位于 `CODEX_HOME/skill-backups`。
- 更新仓库后再次运行安装命令，即可更新安装副本。直接修改安装副本的内容会被覆盖，长期修改应保留在仓库源文件中。
- 文件安装完成与会话实际加载是两回事，请让助手确认读到入口。已有其他技能的用户，可显式指定 `$diansai-collab`，避免进入旧流程。

已有明确需要时，再安装其他技能：

```powershell
.\install.ps1 -SkillName stm32-keil
# 安装仓库内全部技能：
.\install.ps1 -All
```

</details>

## 它怎样改变一次调试？

假设小车在固定输出时能走直线，加入速度反馈后，却一边越来越快、另一边越来越慢。

直接说“帮我调一下 PID”，容易进入反复改参数的循环。更有用的合作是：

> **你：** 固定输出时正常，加入反馈后才出问题。
>
> **AI：** 先保住正常版本。我检查左右轮的输出与反馈是否对应，不急着改参数。
>
> **你：** 我可以观察轮子和屏幕，但不知道该看哪个数。
>
> **AI：** 我会说明具体动作、对应读数和停止条件，再根据结果判断。

这个例子概括自实际开发经历。关键不是某个参数，而是：**用已经正常的部分缩小问题，让每一次实物观察都能改变判断。**

基础不高时，你仍然能提供 AI 最缺的东西：哪个轮子动了、球从哪里滚过来、哪个版本曾经正常、刚才究竟改了什么。AI 则应承担技术分析，而不是把一句“检查硬件”当作全部帮助。

## 想深入了解，从这里读

| 你想解决的问题 | 阅读入口 |
|---|---|
| 不知道怎样反馈现象、纠正误解或交接进度 | [可直接使用的协作卡片](skills/diansai-collab/references/collaboration-cards.md) |
| 想看看真实项目里人和 AI 怎样走偏、怎样纠正 | [现场案例](skills/diansai-collab/references/field-cases.md) |
| 想了解这些规则如何从历史开发记录中提炼出来 | [电赛对话深度复盘](docs/diansai-dialogue-audit.md) |
| 想审查规则在不同情境下会引导什么行动 | [情境推演与局限](docs/collaboration-replay.md) |

## 经验从哪里来？

仓库整理自作者的校赛循迹小车、人脸跟拍云台和车载平衡滚球项目经历；作者获得了 **2026 年电赛省一等奖**。

比起只展示最后跑通的结果，这里更关注过程中的阻碍：双方对同一个词理解不同、成功方法迁移后失效、源码与板上版本脱节，以及反复调参却没有有效观察。

这些经验被整理成可复用的协作规则，供新手从自己的项目开始实践。它不是获奖保证，规则的实际效果仍需要更多使用反馈。[项目背景复盘](docs/ai-collaboration-retrospective.md) · [验证记录与适用边界](docs/release-validation.md)

<details>
<summary>已有工程经验？查看其他专业技能</summary>

默认协作入口独立工作，以下技能按需使用，不要求新手全部安装。

| Skill | 适合什么时候用 |
|---|---|
| [analyze-nuedc-task](skills/analyze-nuedc-task/SKILL.md) | 需要详细审题和工程任务包 |
| [nuedc-code-planner](skills/nuedc-code-planner/SKILL.md) | 需要多任务代码架构设计 |
| [stm32-keil](skills/stm32-keil/SKILL.md) | 处理 STM32 / Keil 工程 |
| [stm32cubemx](skills/stm32cubemx/SKILL.md) | 处理 CubeMX 生成与 Keil 构建 |
| [planning-with-files-zh](skills/planning-with-files-zh/SKILL.md) | 需要较完整的文件化进度管理 |
| [nuedc-full-runner](skills/nuedc-full-runner/SKILL.md) | 明确需要完整工程流程与多份文档 |

使用前阅读对应说明与项目约束。历史示例不是你的板卡固件，仍需核对芯片、接线和工具链。

</details>

## 一起把方法变得更有用

欢迎在 [Issues](https://github.com/54xkeee/agent-diansai-skill/issues) 分享你和 AI 卡住的具体时刻：**原本想做什么、AI 理解成了什么、实物发生了什么、什么证据最终改变了判断。**

无需写成完整教程，先去掉个人信息和密钥即可。一个具体的失败案例，往往比一条“万能提示词”更能帮助下一位同学。

[MIT](LICENSE) · [贡献方式](CONTRIBUTING.md)
