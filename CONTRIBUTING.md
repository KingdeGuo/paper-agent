# 🤝 贡献指南 / Contributing Guide

**中文** · [English](#contributing-guide)

---

## 中文

欢迎贡献 Paper Agent！本项目致力于打造智能文献管理工具，感谢你的参与。

### 开发流程

1. **Fork** 本仓库
2. 创建特性分支：`git checkout -b feat/my-feature`
3. 提交更改：`git commit -m "feat: add my feature"`
4. 推送到分支：`git push origin feat/my-feature`
5. 发起 Pull Request

### 代码规范

- **Python**：遵循 PEP 8，使用 `ruff` 检查：`ruff check --fix paper_agent/`
- **JavaScript / React**：遵循项目内的格式化约定
- **提交信息**：遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范
  - `feat:` 新功能
  - `fix:` 修复 Bug
  - `docs:` 文档更新
  - `refactor:` 重构
  - `i18n:` 国际化相关
  - `style:` 代码风格（不影响功能）
  - `chore:` 构建、CI 等杂项

### 测试

```bash
python -m pytest paper_agent/tests -v
```

### 国际化

- 翻译文件位于 `paper_agent/frontend/src/i18n/locales/`
- 添加新语言：在 `locales/` 下新建目录，内容参考 `en/common.json`
- 组件中使用：`const { t } = useTranslation(); t('namespace.key')`

---

## English

Welcome to Paper Agent! We appreciate your contributions.

### Workflow

1. **Fork** the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Commit changes: `git commit -m "feat: add my feature"`
4. Push: `git push origin feat/my-feature`
5. Open a Pull Request

### Code Style

- **Python**: PEP 8, lint with `ruff`: `ruff check --fix paper_agent/`
- **JavaScript / React**: Follow project conventions
- **Commits**: [Conventional Commits](https://www.conventionalcommits.org/)
  - `feat:` New feature
  - `fix:` Bug fix
  - `docs:` Documentation
  - `refactor:` Code refactoring
  - `i18n:` Internationalization
  - `style:` Formatting (no logic change)
  - `chore:` Build, CI, etc.

### Tests

```bash
python -m pytest paper_agent/tests -v
```

### i18n

- Locale files: `paper_agent/frontend/src/i18n/locales/`
- Add a new language: create directory in `locales/`, reference `en/common.json`
- Usage: `const { t } = useTranslation(); t('namespace.key')`