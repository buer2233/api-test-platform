# api-test-platform
一个正在从“Python 接口自动化测试框架”演进为“统一接口测试资产平台”的项目。

当前项目目标不是只保留为手写 pytest 用例仓库，而是逐步建设成：

> **统一接口测试资产平台 + AI 生成/编排能力 + 规则校验与执行验证闭环**

---

## 1. 当前项目定位

当前仓库已经明确进入产品设计、架构设计和 V1 首批落地阶段，未来将支持：

- **接口文档驱动**：从 OpenAPI / Swagger / Markdown 文档生成接口资产和基础测试骨架
- **功能测试用例驱动**：从功能测试步骤或业务场景生成接口自动化测试场景
- **抓包驱动**：从真实请求流量中提取接口、依赖与测试场景

平台最终需要支持：

- **Web 服务访问使用**
- **桌面应用使用（Windows 优先，后续支持 macOS）**

当前阶段采用：

- **本地单机模式优先设计核心能力**
- **V1 先做底座、文档驱动最小闭环与架构奠基**
- **公开接口测试与底座验证统一以 JSONPlaceholder 作为专用测试网站**

---

## 2. 当前仓库结构

```text
api-test-platform/
├─ api_test/                 # 当前已有的 Python 接口自动化测试框架主体
│  ├─ core/                  # 当前基础请求与业务接口封装
│  ├─ tests/                 # 当前历史 pytest 测试用例
│  ├─ test_data/             # 测试数据
│  ├─ report/                # 测试报告输出
│  ├─ config.py              # 当前配置
│  ├─ conftest.py            # pytest fixture / hook
│  ├─ run_test.py            # 测试执行入口
│  └─ README.md              # 当前框架说明
├─ platform_core/            # V1 新增的平台核心最小实现（模型/解析/模板/规则/执行/闭环服务）
├─ tests/
│  └─ platform_core/         # V1 平台核心本地自动化测试
├─ product_document/         # 产品、架构、设计、阶段说明文档
├─ AGENTS.md                 # 当前仓库对 Codex / AI Worker 的全局指导
└─ README.md                 # 本文件
```

---

## 3. 已沉淀的核心文档

当前已经建立的设计文档位于 `product_document/`：

- `产品需求说明书(全局).md`
- `调研文档/AI自动化测试平台与AI驱动接口自动化测试平台调研报告.md`
- `架构设计/总体架构设计说明书.md`
- `架构设计/中间模型设计说明书.md`
- `架构设计/模板体系与代码生成规范说明书.md`
- `架构设计/现有接口自动化测试框架改造方案.md`
- `架构设计/UI设计说明文档.md`
- `阶段文档/全阶段工作规划文档.md`
- `阶段文档/V1阶段工作计划文档.md`
- `阶段文档/V1实施计划与开发任务拆解说明书.md`
- `阶段文档/V2阶段工作计划文档.md`
- `阶段文档/V3阶段工作计划文档.md`
- `阶段文档/后续阶段工作规划文档.md`
- `测试文档/详细测试用例说明书(V1).md`

---

## 4. 当前技术方向

### 核心技术栈

- **Python**
- **requests**
- **pytest**

### 当前架构建议方向

- 核心引擎：Python
- 模板体系：Jinja2（代码生成模板）
- Web 服务层：Django + DRF（当前确认）
- 数据存储：MySQL（当前确认）
- 前端：React + TypeScript（建议）
- Desktop：前端壳 + 本地服务内核（当前保持 Tauri 优先评估，Electron 备选）
- 开发流程：UI 设计先行 + TDD

---

## 5. 当前阶段的研发原则

当前阶段不是自由堆功能阶段，必须遵循：

1. **先产品说明书**
2. **再总体架构设计**
3. **再中间模型与框架改造设计**
4. **再详细测试用例设计**
5. **再按 TDD 开发**
6. **开发完成后执行测试验证**
7. **最后对照说明书验收**

### 当前主线

> 产品说明书优先 → 架构优先 → 中间模型优先 → 模板与规则优先 → TDD 开发 → 执行验证 → 资产沉淀

---

## 6. 当前对 AI / Codex 的要求

所有进入本仓库工作的 AI Worker（包括 Codex / Claude Code），都必须优先参考：

- `AGENTS.md`
- `product_document/` 下的说明文档

不允许：

- 绕过说明书直接大范围自由开发
- 把 AI 输出直接当作最终正确结果
- 直接拼接最终生产代码而不经过模板与规则
- 为了快速完成局部功能破坏平台化方向

---

## 7. V1 当前新增落地内容

截至 2026-03-31，已完成五轮 V1 首批落地：

- 新增 `platform_core/`，实现文档解析、中间模型、Jinja2 模板、基础规则、pytest 执行器、CLI 入口和文档驱动闭环服务。
- 解析输入已支持 `.json`、`.yaml`、`.yml`，兼容 OpenAPI 3.x 和 Swagger 2.0，并可从响应示例补齐 `json_field_equals` 断言候选。
- 新增 `PlatformApplicationService`，显式约束 V1 当前仅支持 `document` 路线，阻止 `functional_case` 和 `traffic_capture` 越界进入实现。
- 新增 `AssetWorkspace` 与 `asset_manifest.json`，为生成资产补齐 digest、来源、生成记录和执行记录关联，形成最小资产清单边界。
- 已补齐资产清单结构校验、工作区检查服务和 CLI `inspect`，使当前工作区不仅可落盘，还能被读取、检查并返回结构化资产摘要。
- 规则与模板已增强：`source_ids` 必填、`ai_assisted` 生成记录必须带 `prompt_reference`、可执行接口必须包含 `status_code` 断言，并已支持 `json_field_equals` 断言模板。
- 旧 `api_test` 底座已新增会话构建与私有环境依赖治理模块，`BaseAPI` 默认使用重试 Session，私有环境 RSA 公钥改为显式环境变量配置，不再依赖占位内容；`PublicAPI` 也已补齐最小旧接口操作目录，开始向统一接口资产边界收口。
- `platform_core` 已新增旧 `PublicAPI` 结构化适配层，可把历史接口目录转换为 `SourceDocument + ApiModule + ApiOperation` 快照，作为“既有接口资产”进入统一模型边界的最小桥接。
- `api_test/run_test.py` 已新增 `--public-baseline` 模式，可稳定排除 `private_env` 用例，形成不依赖 skip 的本地公开回归入口。
- 根目录 `pytest.ini` 与 `api_test/pytest.ini` 已显式配置 `asyncio_default_fixture_loop_scope=function`，收敛此前两套测试中的 `pytest-asyncio` 弃用告警；`api_test` 的 pytest-html hook 也已更新为当前推荐写法。
- 新增 `tests/platform_core/` 与 `api_test/tests/` 对应测试，当前本地基线为 `35 passed` 与 `30 passed, 4 skipped`。
- `api_test` 公开回归基线已切换到 JSONPlaceholder，并补齐过滤、嵌套路由、伪写入契约、REST 状态码兼容、公共 fixture、`users/todos` 资源封装、旧接口目录治理与公开基线执行入口；当前 `api_test` 全量基线为 `30 passed, 4 skipped`，公开基线为 `30 passed, 4 deselected`。

---

## 8. 当前如何使用

### 安装依赖

```bash
python -m pip install -r api_test/requirements.txt
```

### 运行 V1 平台核心测试

```bash
python -m pytest tests/platform_core -v
```

### 运行当前本地综合回归

```bash
cd api_test
python -m pytest -v
```

### 运行当前公开回归基线

```bash
cd api_test
python run_test.py --public-baseline
```

### 直接运行文档驱动闭环

```bash
python -m platform_core.cli run --source <spec-file> --output <workspace-dir>
```

### 检查已生成工作区资产清单

```bash
python -m platform_core.cli inspect --workspace <workspace-dir>
```

### 检查旧 PublicAPI 的结构化资产快照

```bash
python -m platform_core.cli inspect-legacy-public-api
```

### 当前公开接口测试站点

- 当前仓库公开接口测试、底座验证和接口能力示例统一使用 `https://jsonplaceholder.typicode.com/`
- 测试设计需遵循其公开 Guide：资源范围固定、支持 `GET/POST/PUT/PATCH/DELETE`、支持查询参数过滤和一层嵌套路由、写操作为伪写入不持久化
- `api_test` 默认公开基线地址已切换到该站点，并同步调整底座以支持 `201` 等标准 REST 状态码

### 说明

- 2026-03-31 的本地验证结果：
  - `python -m pytest tests/platform_core -v` -> `35 passed`
  - `cd api_test && python -m pytest -v` -> `30 passed, 4 skipped`
  - `cd api_test && python run_test.py --public-baseline` -> `30 passed, 4 deselected`
- 根目录 `pytest.ini` 已统一配置 `--basetemp=.pytest_tmp`，`platform_core` 执行器也会为生成工作区显式下发本地临时目录，因此当前无需再手工补 `--basetemp`。
- `api_test/tests/test_demo.py` 中带 `private_env` 标记的登录链路用例默认跳过；如需显式执行，请先设置 `ENABLE_PRIVATE_API_TESTS=1`，并提供有效 `API_TEST_RSA_PUBLIC_KEY`。
- 私有环境链路已移除 RSA 占位公钥依赖，并已通过 `python run_test.py --public-baseline` 提供稳定公开回归入口；但这类用例仍依赖真实账号和私有环境，因此不纳入 V1 当前公开回归验收基线。
- `python -m platform_core.cli run ...` 的输出摘要中已包含 `asset_manifest_path`，可直接定位本轮生成资产清单。
- `python -m platform_core.cli inspect ...` 可返回 `validation_status`、资产数量、生成记录数量、资产摘要、缺失资产和 digest 不一致信息，用于当前 V1 资产检查。
- `python -m platform_core.cli inspect-legacy-public-api` 可返回旧 `PublicAPI` 的模块数、接口数、私有链路接口数以及结构化操作清单，用于当前 V1 既有接口资产治理。

---

## 9. 项目当前最重要的事情

当前最重要的不是直接造更多功能，而是：

1. 继续补齐产品与架构文档
2. 稳定和扩展 V1 文档驱动最小闭环
3. 逐步把旧 `api_test` 底座与新平台核心能力收敛到统一方向
4. 在保持 TDD 的前提下继续推进规则、模板和输入能力增强

---

## 10. 维护说明

后续如有以下变化，应同步更新本 README：

- 产品定位变化
- 架构变化
- 目录结构变化
- V1 / V2 范围变化
- 使用方式变化
- 核心技术路线变化

---

## 11. 结论

本项目已经不再是一个普通的 pytest 测试仓库，而是在演进为一个：

> **面向测试与开发人员的接口测试资产平台**

后续所有开发都应围绕这一目标推进。
