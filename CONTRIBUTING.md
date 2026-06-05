# Contributing

欢迎提交 PR 或 Issue！

## 添加新 Skill

1. 在 `skills/` 下新建目录，目录名即为 skill 名
2. 必须包含 `SKILL.md`，frontmatter 格式：

```markdown
---
name: your-skill-name
description: 一句话描述，AI 用这句话判断是否调用本 skill
---
```

3. 可选子目录：`scripts/`（工具脚本）、`examples/`（例程）、`templates/`（模板文件）、`agents/`（agent 配置）

## 提交规范

- commit message 使用英文，格式：`type: subject`
- 类型：`feat` / `fix` / `docs` / `refactor`
- 例：`feat: add stm32f4 encoder example`

## 测试

添加 Python 脚本后，确保：
- 有 `--help` 参数
- Windows PowerShell 下可正常运行
