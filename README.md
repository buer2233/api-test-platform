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

截至 2026-03-31，已完成两轮 V1 首批落地：

- 新增 `platform_core/`，实现文档解析、中间模型、Jinja2 模板、基础规则、pytest 执行器、CLI 入口和文档驱动闭环服务。
- 解析输入已支持 `.json`、`.yaml`、`.yml`，兼容 OpenAPI 3.x 和 Swagger 2.0。
- 闭环执行已支持多接口文档批量生成、整套 `generated/tests` 目录执行，以及 `python -m platform_core.cli run ...` 命令行入口。
- 新增 `tests/platform_core/`，覆盖模型、解析、模板、规则、执行、CLI 和集成闭环共 22 项本地自动化测试。
- 已整理旧 `api_test` 本地回归基线：私有环境登录链路用例默认跳过，公开示例与本地工具类测试可稳定执行。

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

### 直接运行文档驱动闭环

```bash
python -m platform_core.cli run --source <spec-file> --output <workspace-dir>
```

### 说明

- 2026-03-31 的本地验证结果：
  - `python -m pytest tests/platform_core -v` -> `22 passed`
  - `cd api_test && python -m pytest -v` -> `11 passed, 4 skipped`
- `api_test/tests/test_demo.py` 中带 `private_env` 标记的登录链路用例默认跳过；如需显式执行，请先设置 `ENABLE_PRIVATE_API_TESTS=1`。
- `api_test/core/base_api.py` 中 RSA 公钥仍为占位内容，因此这些私有环境用例不作为 V1 首批闭环验收基线。

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
