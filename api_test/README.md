# api_test

`api_test/` 正在从历史接口测试框架收口为“通用 HTTP 测试底座 + JSON 配置驱动 + 公开示例适配”。

## 当前状态

截至 2026-04-02，当前目录已完成配置层首个 TDD 循环：

- 新增唯一配置文件 [api_config.json](/D:/AI/api-test-platform/api_test/api_config.json)
- 新增配置加载器 [config_loader.py](/D:/AI/api-test-platform/api_test/core/config_loader.py)
- 新增配置测试 [test_config_loader.py](/D:/AI/api-test-platform/api_test/tests/test_config_loader.py)
- 已完成第二个 TDD 循环：
  - [session.py](/D:/AI/api-test-platform/api_test/core/session.py) 改为读取 JSON 配置
  - [base_api.py](/D:/AI/api-test-platform/api_test/core/base_api.py) 收口为通用 HTTP 客户端
  - [test_base_api_governance.py](/D:/AI/api-test-platform/api_test/tests/test_base_api_governance.py) 通过
- 已完成第三个 TDD 循环：
  - 新增 [common_tools.py](/D:/AI/api-test-platform/api_test/core/common_tools.py) 作为通用工具承接层
  - [base_api.py](/D:/AI/api-test-platform/api_test/core/base_api.py) 已移除所有非 HTTP 工具方法
  - 新增 [test_common_tools.py](/D:/AI/api-test-platform/api_test/tests/test_common_tools.py) 锁定工具迁移后的回归行为
- 已补充代理能力：
  - `api_config.json` 新增 `proxy.enabled` 与 `proxy.url`
  - `session.py` 会在代理开关开启时同时为 `http/https` 配置代理
  - 未来客户端应直接控制同一组配置字段
- 已完成历史残留文件清理：
  - 已删除 `config.py`
  - 已删除旧目录桥接清单文件
  - 已删除 `core/legacy_assets.py`
  - 已删除 `test_data/account.txt`
- 已完成中文注释治理首轮：
  - `api_config.json` 已为关键配置段补充中文说明字段
  - `run_test.py`、`config_loader.py`、`base_api.py`、`session.py`、`jsonplaceholder_api.py` 和现有测试文件已补齐中文注释
  - `config_loader.py` 会在加载配置时忽略 `_comment` / `*_comment` 字段

已验证结果：

```bash
python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader
python -m pytest api_test/tests/test_base_api_governance.py api_test/tests/test_common_tools.py -v --noconftest --basetemp .pytest_tmp/base_api_split_docs
python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_base_api_split_full
python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_after_base_api_split
python -m pytest tests -v --basetemp .pytest_tmp/root_after_base_api_split
python api_test/run_test.py --public-baseline
cd api_test && python run_test.py --public-baseline
```

结果：

- `5 passed`
- `19 passed`
- `39 passed`
- `48 passed`
- `53 passed`
- `12 passed, 27 deselected`
- `12 passed, 27 deselected`

补充说明：

- 2026-04-01 已完成代理端口探测和真实代理请求验证，代理开启时公开基线双入口均通过；
- 2026-04-01 默认关闭代理的 `api_test` 全量直连复验曾出现 `test_patch_updates_partial_fields` 超时失败，根因为访问公开站点时的 `SSL handshake/read timeout`，不是框架功能断言失败；
- 2026-04-02 当前轮已完成 `BaseAPI` 与 `common_tools` 的职责收口，`api_test/tests` 全量更新为 `39 passed`，公开基线双入口均为 `12 passed, 27 deselected`。

## 当前目录结构

```text
api_test/
├─ api_config.json         # 通用配置唯一来源
├─ core/
│  ├─ base_api.py          # 通用 HTTP 客户端
│  ├─ common_tools.py      # 通用工具函数
│  ├─ __init__.py          # 通用运行时导出
│  ├─ config_loader.py     # 新配置加载器
│  ├─ jsonplaceholder_api.py
│  └─ session.py
├─ tests/
│  ├─ test_config_loader.py
│  ├─ test_base_api_governance.py
│  ├─ test_common_tools.py
│  ├─ test_jsonplaceholder_api.py
│  ├─ test_jsonplaceholder_resources.py
│  └─ test_run_test.py
├─ conftest.py             # 公开基线 fixture / HTML 报告 hook
├─ pytest.ini
├─ run_test.py             # 正向 `public_baseline` 执行入口
├─ requirements.txt
├─ README.md
└─ QUICKSTART.md
```

## 当前目标

本轮重构完成后，`api_test/` 需要满足：

- `api_config.json` 作为唯一配置源
- `BaseAPI` 只保留通用 HTTP 能力
- 历史专用登录链路、旧桥接目录和账号文件已删除
- `JsonPlaceholderAPI` 只作为公开示例适配层
- `run_test.py --public-baseline` 正向执行公开基线用例
- 代理开关和代理地址统一收口到 `api_config.json`，供后续客户端直接控制
- `requirements.txt` 使用固定版本约束，并已移除未使用的 `rsa` 依赖

## 当前代理配置

默认配置如下：

```json
"proxy": {
  "enabled": false,
  "url": "http://127.0.0.1:7890"
}
```

说明：

- 仓库默认值为关闭；
- 开启后 `requests` 的 `http` 与 `https` 请求都会走同一代理地址；
- 后续 Web/Desktop 客户端完成后，应直接修改这两个字段来控制代理，而不是增加新的独立配置入口。

## 当前状态判断

当前工作分支已经完成以下验证：

- 历史同口径 `api_test` 全量回归已通过，当前最新代理开启专项复验下公开基线稳定通过
- `run_test.py --public-baseline` 在仓库根目录和 `api_test/` 目录执行结果一致
- 公开基线用例使用 `public_baseline` 正向标记
- 代理配置已落地，并通过端口探测、真实代理请求和公开基线双入口复验
- `BaseAPI` 只保留 HTTP 请求相关能力，通用工具已迁移到 `common_tools.py`
- 默认关闭代理时，公开站点直连仍存在外网时延波动，当前不宜把单次超时误判为框架逻辑失败
- `requirements.txt` 已改为固定版本清单，满足当前仓库的依赖安全治理要求

说明：

- `api_test/tests/test_demo.py` 与 `api_test/tests/test_public_api_governance.py` 已从当前测试集移除，不再属于通用框架回归范围。
- `api_test` 当前通用回归链路已满足 V1 目标；后续增强主要转入 `platform_core` / V2 阶段，而不是继续修改当前 `api_test` 基线链路。

## 当前公开测试站点

当前公开接口自动化测试与底座验证统一使用：

- `https://jsonplaceholder.typicode.com/`

设计测试时必须遵循：

- 资源范围以 `posts/comments/albums/photos/todos/users` 为主
- 支持 `GET/POST/PUT/PATCH/DELETE`
- 支持查询参数过滤和一层嵌套路由
- 写操作按伪写入契约断言，不假设真实持久化

## 参考文档

- [现有接口自动化测试框架改造方案.md](/D:/AI/api-test-platform/product_document/架构设计/现有接口自动化测试框架改造方案.md)
- [V1阶段工作计划文档.md](/D:/AI/api-test-platform/product_document/阶段文档/V1阶段工作计划文档.md)
- [详细测试用例说明书(V1).md](/D:/AI/api-test-platform/product_document/测试文档/详细测试用例说明书(V1).md)
- [generic-test-framework-refactor-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-01-generic-test-framework-refactor-design.md)
- [generic-test-framework-refactor.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-01-generic-test-framework-refactor.md)
