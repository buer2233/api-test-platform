# Vue3 前后端分离工作台重构设计说明

## 1. 文档说明
- **文档名称**：Vue3 前后端分离工作台重构设计说明
- **所属项目**：接口自动化测试平台
- **编写日期**：2026-04-20
- **文档目标**：基于项目根目录 `DESIGN.md`，将当前 Django 模板工作台重构为 Vue3 独立前端，并给出当前轮正式 UI 范围、后端契约和清理策略。
- **当前状态**：主人已明确确认，直接进入实现

---

## 2. 当前问题
当前正式入口 `/ui/v2/workbench/` 与 `/ui/v3/workbench/` 仍由 `scenario_service/templates/scenario_service/workbench.html` 承担页面渲染，存在以下问题：
1. 页面结构、样式和业务交互全部混在 Django 模板中，不符合前后端分离要求；
2. 历史页面承接了过多治理类区域，首页主轴不够聚焦；
3. 现有技术口径仍有 `React + TypeScript` 与 Jinja2 前端模板残留，与当前主人确认方向冲突；
4. 当前没有独立前端工程，也没有适合长期演进的组件、路由、状态与测试体系。

---

## 3. 当前轮设计目标
本轮正式目标如下：
1. 前端重构为 **Vue3 + TypeScript** 独立工程；
2. Web UI 采用**前后端分离设计**；
3. `DESIGN.md` 成为所有 UI 编写前的强制前置规则；
4. 正式页面只展示接口自动化主线内容：
   - 项目
   - 模块
   - 子模块
   - 测试用例
   - 测试接口
   - 执行结果
   - 报告与重试
5. 当前轮不再把数据清洗等后台处理界面纳入正式前端交付范围；
6. 旧 Jinja2 前端模板在新前端稳定后删除。

---

## 4. 核心设计结论

### 4.1 前端工程
新增独立前端目录 `frontend/`，采用：
1. `Vue3`
2. `TypeScript`
3. `Vite`
4. `Vue Router`
5. `Vitest`

前端职责：
1. 页面结构与视觉呈现；
2. 工作台导航树、列表区、详情区交互；
3. 调用 Django + DRF API；
4. 主题切换、状态展示、执行动作与报告入口。

后端职责：
1. 提供 API 契约；
2. 提供前端静态入口承接；
3. 不再承接工作台业务 UI 渲染；
4. 继续保留代码生成、执行、审核、调度、治理等核心业务逻辑。

### 4.2 Jinja2 边界
`Jinja2` 当前轮只保留在：
1. `platform_core/templates/`
2. 代码生成相关模板能力

`Jinja2` 不再承担：
1. Web 工作台页面模板
2. 页面内业务交互脚本
3. 页面视觉系统

### 4.3 前端入口策略
继续保留现有访问路径，避免外部使用方式断裂：
1. `/ui/v3/workbench/`
2. `/ui/v2/workbench/`

承接策略：
1. 两个路径统一返回 Vue 前端入口；
2. `/ui/v2/workbench/` 只作为兼容入口，不再维护第二套前端页面；
3. Windows Demo manifest 继续指向 `/ui/v3/workbench/`。

### 4.4 工作台信息架构
工作台保持三段式，但由 Vue 实现：
1. 左侧：项目 / 模块 / 子模块 / 测试用例 / 测试接口导航树
2. 中间：当前层级对象列表与主动作
3. 右侧：测试用例详情、执行结果、报告入口、失败重试、测试接口引用信息

### 4.5 当前轮展示边界
首页主轴只围绕接口自动化测试闭环：
1. 项目
2. 模块
3. 子模块
4. 测试用例
5. 测试接口
6. 执行
7. 报告

当前轮不展示：
1. 数据清洗工作台
2. 后台治理控制台式杂项面板
3. 与当前主线无关的后台处理入口

### 4.6 后端新读模型
为减少前端拼装复杂度，本轮后端新增面向工作台的读模型接口：
1. `GET /api/v2/workbench/bootstrap/`
   - 返回页面标题、主题配置、入口路径和核心 API 能力摘要
2. `GET /api/v2/workbench/navigation/`
   - 返回项目 / 模块 / 子模块 / 测试用例 / 测试接口导航树
3. `GET /api/v2/workbench/test-interfaces/`
   - 返回 `api_test` 目录扫描出的测试接口目录与引用关系
4. `GET /api/v2/workbench/test-interfaces/<interface_id>/`
   - 返回单个测试接口详情

已有接口继续复用：
1. 场景列表、详情、结果、执行
2. 抓包会话、抓包候选
3. 生成确认
4. 主题偏好
5. Windows Demo manifest

### 4.7 模块 / 子模块映射策略
当前仓库已有治理模型不直接等于“模块 / 子模块”展示模型，因此当前轮采用视图层映射：
1. 项目：`project.project_code`
2. 模块：优先 `scenario.module_id`，缺失时回退 `environment.environment_code`
3. 子模块：`scenario_set.scenario_set_code`

这是一层前端读模型映射，不改变底层治理事实表。

### 4.8 测试接口目录策略
当前 `ApiTestMethodRegistry` 仅是内存注册表，不足以支撑前端目录展示。当前轮补齐：
1. 扫描 `api_test/core/` 下的接口文件；
2. 输出接口方法唯一标识、HTTP 方法、完整路径、文件路径、方法名；
3. 聚合被哪些测试用例引用；
4. 为前端提供稳定只读目录视图。

---

## 5. 技术实现策略

### 5.1 前端目录
建议新增：
1. `frontend/package.json`
2. `frontend/tsconfig.json`
3. `frontend/vite.config.ts`
4. `frontend/index.html`
5. `frontend/src/main.ts`
6. `frontend/src/App.vue`
7. `frontend/src/router/`
8. `frontend/src/components/`
9. `frontend/src/views/`
10. `frontend/src/services/`
11. `frontend/src/styles/`

### 5.2 后端入口承接
后端不再用 `TemplateView` 渲染模板页，改为：
1. 使用文件响应返回前端构建后的 `index.html`；
2. 或以统一前端入口响应承接 `/ui/v2/workbench/` 与 `/ui/v3/workbench/`；
3. 入口本身不承载业务模板变量。

### 5.3 DESIGN.md 落地方式
前端视觉系统必须直接对齐 `DESIGN.md`：
1. 暖白底色与橙色主强调；
2. 结构优先使用边框而不是阴影；
3. 标题、正文、标签、按钮遵循 `DESIGN.md` 的字阶与配色；
4. 三段式布局和交互密度做桌面工具感收口；
5. 所有新组件先定义 CSS 变量，避免样式散落。

---

## 6. 测试设计

### 6.1 后端测试
1. 新增工作台前端入口测试，确认 `/ui/v2/workbench/` 与 `/ui/v3/workbench/` 都返回 Vue 入口而非旧模板结构；
2. 新增工作台读模型 API 契约测试；
3. 新增 `api_test` 接口目录扫描测试；
4. 保留现有场景执行、调度、抓包、治理等后端测试。

### 6.2 前端测试
1. 使用 `Vitest` 对导航树、列表区、详情区、测试接口详情、执行动作和主题切换做组件 / 页面测试；
2. 对 API 适配层做单元测试；
3. 对关键页面状态做渲染测试。

### 6.3 集成与验收
1. 执行 Django / DRF 服务测试；
2. 执行前端 `npm run test`；
3. 执行前端 `npm run build`；
4. 启动应用后做浏览器级烟雾验证，确认页面加载、导航切换、执行动作与报告入口正常。

---

## 7. 旧模板清理策略
新前端稳定后，删除以下旧前端模板式承载代码：
1. `scenario_service/templates/scenario_service/workbench.html`
2. 与模板强耦合的 `TemplateView` 页面上下文构造逻辑
3. 仅验证 HTML `data-testid` 字符串的旧模板测试

保留：
1. 后端业务 API
2. Windows Demo manifest
3. 代码生成模板

---

## 8. 成功标准
本轮完成后，应满足：
1. 正式前端已切换为 Vue3 独立工程；
2. Django 不再渲染工作台业务模板页；
3. 页面主轴只展示项目、模块、子模块、测试用例、测试接口与执行相关内容；
4. `DESIGN.md` 的视觉系统已实际落地；
5. 旧 Jinja2 前端模板代码已删除；
6. 后端测试、前端测试、构建验证和浏览器验收均通过；
7. 文档、README、阶段记录和测试说明均已同步。
