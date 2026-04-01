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
- `api_test/` 运行时治理的第二个 TDD 循环：
  - 已将 `api_test/core/session.py` 改为读取 JSON 配置
  - 已将 `api_test/core/base_api.py` 收口为通用 HTTP 客户端
  - 已将 `api_test/core/__init__.py` 去除旧私有站点导出
- 已补充代理配置能力：
  - `api_test/api_config.json` 新增 `proxy.enabled` 和 `proxy.url`
  - `build_retry_session()` 在代理开关开启时自动为 `http/https` 请求挂载代理
  - 后续客户端应直接控制这两个配置项，而不是新增平行配置源
  - 本轮验证曾临时启用 `proxy.enabled=true` 并使用 `http://127.0.0.1:7890` 完成代理连通性验证，仓库默认值已恢复为关闭
- 已完成中文注释治理首轮落地：
  - 新增 `tests/test_comment_governance.py`，对仓库内 Python 模块/类/方法中文 docstring 与 `api_config.json` 中文说明字段做自动校验
  - 已为 `run_test.py`、`config_loader.py`、`base_api.py`、`platform_core` 核心层和现有测试文件补齐中文注释
  - `config_loader.py` 已兼容忽略 `_comment` / `*_comment` 配置说明字段，保证 `api_config.json` 可同时承载配置和中文说明
- 已移除 `api_test/tests` 中两个旧私有站点测试入口：
  - `test_demo.py`
  - `test_public_api_governance.py`

当前分支最新已验证结果：

- `python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader`
  - `5 passed`
- `python -m pytest api_test/tests/test_base_api_governance.py -v --noconftest --basetemp .pytest_tmp/base_api`
  - `10 passed`
- 代理有效性验证：
  - `Test-NetConnection 127.0.0.1 -Port 7890` -> `TcpTestSucceeded=True`
  - 基于 `build_retry_session()` 的代理会话请求 `https://jsonplaceholder.typicode.com/posts/1` -> `200 / body_id=1`
- 2026-04-01 代理开启专项复验：
  - `python -m pytest api_test/tests/test_base_api_governance.py -v --noconftest --basetemp .pytest_tmp/base_api_proxy_recheck`
    - `10 passed`
  - `python api_test/run_test.py --public-baseline`
    - `12 passed, 17 deselected`
  - `cd api_test && python run_test.py --public-baseline`
    - `12 passed, 17 deselected`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_full_after_cleanup`
  - `29 passed`
- 2026-04-01 默认关闭代理直连复验：
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_full_default_off_serial`
    - `1 failed, 28 passed`
    - 失败项：`test_patch_updates_partial_fields`
    - 根因：访问 `jsonplaceholder.typicode.com` 时出现 `SSL handshake/read timeout`，属于外网站点时延波动，不是框架断言逻辑错误
- `python api_test/run_test.py --public-baseline`
  - `12 passed, 17 deselected`
- 中文注释治理与兼容性回归：
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_full_comment_update`
    - `42 passed`
  - `python -m pytest api_test/tests/test_config_loader.py api_test/tests/test_base_api_governance.py api_test/tests/test_run_test.py -v --noconftest --basetemp .pytest_tmp/api_test_local_comment_update_fix`
    - `18 passed`
  - `python api_test/run_test.py --public-baseline`
    - `12 passed, 18 deselected`
- `cd api_test && python run_test.py --public-baseline`
  - `12 passed, 17 deselected`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_full`
  - `40 passed`

说明：

- 当前 `api_test` 的通用配置、通用运行时、公开基线入口和公开示例测试已经完成当前轮闭环验证；
- 代理开启时，当前公开基线与运行入口复验稳定通过；
- 仓库默认保持 `proxy.enabled=false`，但默认直连外网站点仍存在时延波动，当前公开站点回归建议优先开启代理；
- `platform_core` 全量仍然保持通过；
- 更深一层的 `platform_core` 去特化和旧资产桥接清理仍在后续改造范围内。

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
python -m pytest api_test/tests/test_base_api_governance.py -v --noconftest --basetemp .pytest_tmp/base_api
python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_full_after_cleanup
python api_test/run_test.py --public-baseline
cd api_test && python run_test.py --public-baseline
```

## 备注

- 当前 README 已切换为“重构进行中”视角，只记录本分支已验证事实。
- `api_test` 和 `platform_core` 的更大范围回归，将在运行时去特化完成后再次统一复验并回填文档。
