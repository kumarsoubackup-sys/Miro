# 前端多语言 (Vue I18n) 分支与 PR 计划

方案：Vue I18n 9，locale 存 localStorage，fallback `en`，切换时更新 `document.documentElement.lang` 与 `<title>`。

## 已完成（当前分支）

- **分支**：建议 `feat/i18n-setup-home` 或并入 `main` 的首个 PR
- 安装 `vue-i18n@9`（frontend）
- 新增 `frontend/src/locales/zh-CN.json`、`en.json`，按模块分 key：`home.*`、`process.*`、`history.*`、`step.*`、`report.*`、`interaction.*`、`common.*`
- `frontend/src/i18n.js`：`createI18n`，默认 locale 从 `localStorage` 读，fallback `en`；导出 `applyLocaleToDocument()` 用于更新 `document.documentElement.lang` 和 `<title>`
- `main.js`：`app.use(i18n)`，并在挂载前调用 `applyLocaleToDocument()`
- **首页 Home.vue**：所有文案改为 `{{ $t('home.xxx') }}` 或脚本内 `useI18n().t`；导航栏增加语言切换「中文 / English」，切换时写 `localStorage` 并调用 `applyLocaleToDocument()`

## 后续分支（多个 PR 逐步完成）

建议每个 PR 对应一个功能模块，便于 review 与回滚。

| 分支名建议 | 范围 | 说明 |
|-----------|------|------|
| `feat/i18n-process` | Process (MainView.vue) | 补全 `process.*` key，MainView 内所有文案改为 `$t('process.xxx')` 或 `t('process.xxx')` |
| `feat/i18n-history` | History (HistoryDatabase.vue) | 补全 `history.*` key，HistoryDatabase 内文案改为 `$t('history.xxx')` |
| `feat/i18n-steps` | Step1–Step5 组件 | Step1GraphBuild、Step2EnvSetup、Step3Simulation、Step4Report、Step5Interaction 使用 `step.*`（可按 step1.*、step2.* 等子模块划分） |
| `feat/i18n-report` | Report (ReportView.vue) | 补全 `report.*`，ReportView 文案改为 `$t('report.xxx')` |
| `feat/i18n-interaction` | Interaction (InteractionView.vue) | 补全 `interaction.*`，InteractionView 文案改为 `$t('interaction.xxx')` |

每个 PR 需：

1. 在 `zh-CN.json` / `en.json` 中补全对应模块的 key。
2. 将对应页面/组件中的硬编码文案改为 `{{ $t('module.key') }}` 或 `const { t } = useI18n(); ... t('module.key')`。
3. 若该页有独立导航/布局，可在其顶部或导航中复用或放置语言切换（与 Home 一致：切换时写 localStorage 并调用 `applyLocaleToDocument()`）。

## 使用约定

- **模板**：`{{ $t('home.xxx') }}` 或 `:placeholder="$t('home.xxx')"`
- **脚本**：`const { t } = useI18n();` 后使用 `t('home.xxx')`
- **带参数**：`$t('key', { name: value })`
- **locale 存储**：`localStorage` key 为 `locale`（见 `i18n.js` 的 `LOCALE_STORAGE_KEY`），取值 `zh-CN` 或 `en`。
