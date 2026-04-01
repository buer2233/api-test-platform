# api_test

`api_test/` 正在从“带私有站点历史包袱的接口测试框架”重构为“通用 HTTP 测试底座 + 公开示例适配”。

## 当前状态

截至 2026-04-01，当前目录已完成配置层首个 TDD 循环：

- 新增唯一配置文件 [api_config.json](/D:/AI/api-test-platform/api_test/api_config.json)
- 新增配置加载器 [config_loader.py](/D:/AI/api-test-platform/api_test/core/config_loader.py)
- 新增配置测试 [test_config_loader.py](/D:/AI/api-test-platform/api_test/tests/test_config_loader.py)

已验证结果：

```bash
python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader
```

结果：

- `5 passed`

## 当前目录结构

```text
api_test/
├─ api_config.json         # 通用配置唯一来源（已建立）
├─ config.py               # 旧配置入口（迁移未完成前仍存在）
├─ core/
│  ├─ base_api.py          # 待去除私有登录与 RSA 逻辑
│  ├─ config_loader.py     # 新配置加载器
│  ├─ jsonplaceholder_api.py
│  └─ session.py
├─ tests/
│  ├─ test_config_loader.py
│  ├─ test_base_api_governance.py
│  ├─ test_jsonplaceholder_api.py
│  ├─ test_jsonplaceholder_resources.py
│  └─ test_run_test.py
├─ conftest.py             # 待移除账号文件与私有环境 fixture
├─ pytest.ini
├─ run_test.py             # 待改为正向 `public_baseline` 执行
├─ requirements.txt
├─ README.md
└─ QUICKSTART.md
```

## 当前目标

本轮重构完成后，`api_test/` 需要满足：

- `api_config.json` 作为唯一配置源
- `BaseAPI` 只保留通用 HTTP 能力
- 删除 RSA、公私有环境登录和旧 `PublicAPI` 专有链路
- `JsonPlaceholderAPI` 只作为公开示例适配层
- `run_test.py --public-baseline` 正向执行公开基线用例

## 当前限制

当前工作分支还没有完成以下迁移，因此不能把 `api_test/` 视为已完成状态：

- `core/__init__.py` 仍受旧私有导入链路影响
- `conftest.py` 仍依赖历史账号与私有环境概念
- `BaseAPI` 仍包含登录和 RSA 相关逻辑
- `run_test.py` 仍使用旧的 `private_env` 排除语义
- `api_test` 全量回归尚未在当前重构分支重新通过

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
