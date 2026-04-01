# api-test-platform

一个正在从“手写接口自动化测试框架”演进为“统一接口测试资产平台”的仓库。

当前主线目标：

> 统一接口测试资产平台 + AI 生成/编排能力 + 规则校验与执行验证闭环

## 当前状态

截至 2026-04-01，仓库处于“通用测试框架大重构”执行中，已完成：

- 重构设计说明与实施计划；
- 重构前备份提交并推送：
  - `c102cb4`
  - `备份：测试框架大重构前的备份提交`
- `api_test/` 配置收口的首个 TDD 循环：
  - 新增 `api_test/api_config.json`
  - 新增 `api_test/core/config_loader.py`
  - 新增 `api_test/tests/test_config_loader.py`

当前分支最新已验证结果：

- `python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader`
  - `5 passed`

说明：

- 当前 `api_test` 仍在从旧私有站点链路向通用框架迁移；
- `BaseAPI`、`conftest.py`、`run_test.py` 和 `platform_core` 的去特化改造仍在继续；
- 2026-03-31 的全量回归结果仅作为重构前备份基线参考，不代表当前工作分支状态。

## 当前仓库结构

```text
api-test-platform/
├─ api_test/
│  ├─ api_config.json       # 新配置唯一来源（已建立，迁移中）
│  ├─ config.py             # 旧配置入口（待删除）
│  ├─ core/                 # 通用运行时与历史底座代码
│  ├─ tests/                # api_test 自动化测试
│  ├─ conftest.py           # pytest fixture / hook（待去特化）
│  ├─ pytest.ini            # api_test pytest 配置
│  ├─ run_test.py           # 测试执行入口（待改为正向公开基线）
│  ├─ README.md
│  └─ QUICKSTART.md
├─ platform_core/           # V1 平台核心最小闭环
├─ tests/platform_core/     # platform_core 自动化测试
├─ product_document/        # 产品、架构、阶段、测试文档
├─ docs/superpowers/        # 当前轮设计说明与实施计划
├─ AGENTS.md
└─ README.md
```

## 当前已确认方向

- 公开接口测试基线统一使用 `https://jsonplaceholder.typicode.com/`
- V1 当前只开放文档驱动最小闭环
- `api_test/` 的目标是“通用 HTTP 测试底座 + 公开示例适配”，不再是某个私有站点的专用框架
- 所有全局配置最终统一收口到 `api_test/api_config.json`

## 当前建议查看顺序

开始任何需求、设计或开发前，优先查看：

- [AGENTS.md](/D:/AI/api-test-platform/AGENTS.md)
- [产品需求说明书(全局).md](/D:/AI/api-test-platform/product_document/产品需求说明书(全局).md)
- [总体架构设计说明书.md](/D:/AI/api-test-platform/product_document/架构设计/总体架构设计说明书.md)
- [中间模型设计说明书.md](/D:/AI/api-test-platform/product_document/架构设计/中间模型设计说明书.md)
- [现有接口自动化测试框架改造方案.md](/D:/AI/api-test-platform/product_document/架构设计/现有接口自动化测试框架改造方案.md)
- [详细测试用例说明书(V1).md](/D:/AI/api-test-platform/product_document/测试文档/详细测试用例说明书(V1).md)
- [generic-test-framework-refactor-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-01-generic-test-framework-refactor-design.md)
- [generic-test-framework-refactor.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-01-generic-test-framework-refactor.md)

## 当前验证入口

平台核心历史基线：

```bash
python -m pytest tests/platform_core -v
```

当前轮配置收口验证：

```bash
python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader
```

## 备注

- 当前 README 已切换为“重构进行中”视角，只记录本分支已验证事实。
- `api_test` 和 `platform_core` 的更大范围回归，将在运行时去特化完成后再次统一复验并回填文档。
