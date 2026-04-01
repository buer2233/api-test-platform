# 通用测试框架大重构设计说明

## 1. 文档信息
- 日期：2026-04-01
- 主题：将当前测试框架重构为面向通用网站测试的配置驱动底座
- 适用范围：`api_test/`、`platform_core/`、仓库级 README 与 V1 阶段文档
- 关联目标：
  - 删除当前私有网站特化链路
  - 将全部全局配置收口到 `api_test/api_config.json`
  - 保持 V1 平台主链路可运行
  - 使 `api_test/` 满足“通用测试框架 + 公开站点示例适配”的定位

## 2. 背景与问题
当前仓库虽然已经完成 V1 最小闭环的首批落地，但 `api_test/` 仍然遗留明显的站点特化设计：
- `config.py` 不是唯一配置源，且存在运行参数散落问题；
- `BaseAPI` 混入了 RSA、登录、公私有环境账号状态等私有链路能力；
- `PublicAPI`、`legacy_api_catalog`、`private_env` 等能力都绑定某个历史私有网站；
- `run_test.py` 的“公开回归基线”依赖 `private_env` 排除语义，不适合作为通用框架长期设计；
- `platform_core/` 内还存在对旧 `PublicAPI` 目录的硬编码桥接；
- README、快速入门、V1 阶段文档、测试说明仍包含大量过时的私有链路描述。

这与当前产品方向不一致。当前仓库需要面向“统一接口测试资产平台 + AI 生成/编排能力 + 规则校验与执行验证闭环”演进，而 `api_test/` 在该方向下应承担的是：
- 通用 HTTP 测试底座；
- 配置驱动运行入口；
- 公开站点测试示例；
- 平台过渡阶段的稳定回归基线。

它不应继续承担某个私有网站的业务接口库职责。

## 3. 改造目标

### 3.1 主目标
将当前测试框架重构为：

> 通用 HTTP 测试框架 + JSON 配置驱动 + 公开站点示例适配 + 平台化可承接的最小底座

### 3.2 必须达成的结果
1. `api_test/api_config.json` 成为唯一配置源；
2. 删除 `api_test/config.py` 及全部引用；
3. 删除 RSA、公私有环境登录、旧 `PublicAPI` 目录等站点特化能力；
4. `BaseAPI` 收口为纯通用 HTTP 客户端基类；
5. `run_test.py` 在仓库根目录与 `api_test/` 目录执行时行为一致；
6. `run_test.py --public-baseline` 改为正向执行公开基线，而不是通过排除 `private_env` 实现；
7. `platform_core/` 删除当前硬编码旧站点桥接，保留平台主链路；
8. 所有相关文档与测试同步更新。

### 3.3 非目标
本轮不做以下内容：
1. 不扩展 V2 的功能用例驱动或抓包驱动实现；
2. 不新增 Web 或 Desktop 正式实现；
3. 不引入新的数据库或服务端持久化；
4. 不把 `api_test/` 改造成多站点插件系统成品，仅为后续预留配置与适配结构。

## 4. 设计原则
1. 配置唯一来源：所有全局配置统一来自 `api_config.json`。
2. 通用能力优先：底座只保留跨站点可复用能力。
3. 示例与框架分离：`JsonPlaceholderAPI` 是示例适配层，不是框架核心。
4. 测试先行：严格按 TDD 顺序先写失败测试，再做最小实现。
5. 文档同步：每一轮代码、测试、验证结果变化后同步更新文档。
6. 平台主线不倒退：`platform_core` 的文档驱动主链路必须保持可运行。

## 5. 目标结构

### 5.1 `api_test/` 目标结构
```text
api_test/
├─ api_config.json
├─ core/
│  ├─ base_api.py
│  ├─ config_loader.py
│  ├─ session.py
│  └─ jsonplaceholder_api.py
├─ tests/
│  ├─ test_base_api_governance.py
│  ├─ test_config_loader.py
│  ├─ test_jsonplaceholder_api.py
│  ├─ test_jsonplaceholder_resources.py
│  └─ test_run_test.py
├─ conftest.py
├─ pytest.ini
├─ run_test.py
├─ README.md
└─ QUICKSTART.md
```

### 5.2 需要删除的 `api_test/` 站点特化项
- `config.py`
- `core/private_env.py`
- `core/public_api.py`
- `legacy_api_catalog.py`
- `core/legacy_assets.py`
- `tests/test_demo.py`
- `tests/test_public_api_governance.py`

### 5.3 `platform_core/` 需要去特化的项
- `platform_core/legacy_assets.py`
- `platform_core/cli.py` 中与旧 `PublicAPI` 快照相关的命令
- `platform_core/rules.py` 中与 `legacy_public_api` / `private_env` / `requires_private_env` 强绑定的专项规则
- 对应测试与文档描述

## 6. 配置设计

### 6.1 唯一配置文件
配置文件路径固定为：

```text
api_test/api_config.json
```

### 6.2 建议配置结构
```json
{
  "runtime": {
    "base_url": "https://jsonplaceholder.typicode.com",
    "timeout": 30,
    "verify_ssl": true,
    "default_headers": {
      "Content-Type": "application/json"
    }
  },
  "session": {
    "pool_connections": 100,
    "pool_maxsize": 100,
    "max_retries": 3
  },
  "execution": {
    "tests_root": "tests",
    "report_dir": "report",
    "default_pytest_args": [
      "-v",
      "--strict-markers",
      "--tb=short",
      "--disable-warnings"
    ],
    "public_baseline_marker": "public_baseline"
  },
  "logging": {
    "enabled": false,
    "stack": false,
    "headers": false,
    "body": false,
    "response": false,
    "trace_id": true,
    "http_log_info": "logs/http_info.log",
    "http_log_conn": "logs/http_conn.log"
  },
  "site_profiles": {
    "jsonplaceholder": {
      "enabled": true,
      "supported_resources": [
        "posts",
        "comments",
        "albums",
        "photos",
        "todos",
        "users"
      ]
    }
  }
}
```

### 6.3 配置加载方式
- 新增 `api_test/core/config_loader.py`；
- 配置加载器负责：
  - 定位 `api_config.json`；
  - 读取与基础校验；
  - 返回结构化配置对象；
  - 提供缓存入口，避免重复 IO；
- 配置路径必须基于 `api_test/` 目录定位，而不是当前工作目录；
- 不保留环境变量覆盖，也不保留 `RunConfig` 兼容壳。

## 7. 代码设计

### 7.1 `BaseAPI`
改造后的 `BaseAPI` 仅保留：
- Session 初始化；
- 通用 `request/get/post/put/patch/delete`；
- 允许 `expected_status` 的状态码断言；
- 通用默认请求头、超时与 SSL 配置；
- 纯通用工具能力：
  - 数据提取；
  - 日期时间转换；
  - 基础字符串/数据生成；
  - 与站点无关的基础加密工具。

改造后的 `BaseAPI` 必须删除：
- `password_rsa()`
- `login()`
- `get_admin_session()`
- 公私有环境账号状态字段
- 对某站点 cookie / 登录协议的直接假设

### 7.2 `JsonPlaceholderAPI`
保留为公开示例适配层，继续承接：
- posts 查询与伪写入；
- users 查询；
- todos 查询与嵌套路由；
- REST 状态码契约。

它的定位应改为：
- 一个示例站点适配器；
- 当前公开回归基线；
- 通用框架的最小站点适配示例。

### 7.3 `run_test.py`
目标行为：
- 无论从仓库根目录还是 `api_test/` 目录执行，都只运行 `api_test/tests`；
- 默认执行路径由 `api_config.json.execution.tests_root` 提供；
- `--public-baseline` 正向选择 `public_baseline` 标记；
- HTML 报告目录由 `api_config.json.execution.report_dir` 提供；
- `pytest` 配置文件路径显式指定为 `api_test/pytest.ini` 或在 `api_test` 目录内解析。

### 7.4 `conftest.py`
改造后仅保留：
- 通用测试环境基础 fixture；
- `base_url`；
- `jsonplaceholder_api`；
- HTML 报告 hook；
- 与当前公开示例相关的最小测试辅助逻辑。

需要删除：
- 账号文件读取；
- `admin_account` / `employee_account`；
- 任何私有环境启用逻辑。

## 8. `platform_core` 去特化设计

### 8.1 删除内容
- 基于 `api_test.legacy_api_catalog` 的硬编码桥接；
- 旧 `PublicAPI` 快照检查和导出命令；
- `legacy_public_api` / `private_env` / `requires_private_env` 站点特化规则；
- 对应测试。

### 8.2 保留内容
- 文档解析；
- 中间模型；
- 模板渲染；
- 通用规则；
- 资产清单；
- 工作区检查；
- CLI `run` 与 `inspect`；
- 文档驱动最小闭环。

### 8.3 平台概念保留
仍保留 `existing_api_asset` 作为中间模型概念扩展位，但本轮不再提供“某私有站点旧目录”的内建适配器。后续如果需要恢复该类能力，应以通用 adapter 接口重新设计。

## 9. TDD 测试设计

### 9.1 配置层测试
新增 `api_test/tests/test_config_loader.py`，覆盖：
1. 能从 `api_config.json` 读取唯一配置；
2. 缺失关键字段时报错；
3. 加载路径与当前工作目录无关；
4. 配置缓存行为可控。

### 9.2 底座测试
改造 `api_test/tests/test_base_api_governance.py`，覆盖：
1. Session 参数来自 JSON 配置；
2. 请求头、超时、SSL 参数来自 JSON 配置；
3. `request/get/post/put/patch/delete` 兼容；
4. 不再暴露 RSA / 登录相关能力。

### 9.3 执行入口测试
改造 `api_test/tests/test_run_test.py`，覆盖：
1. 命令构建显式指向 `api_test/tests`；
2. `--public-baseline` 使用正向 marker；
3. HTML 报告目录来自配置；
4. 根目录执行与 `api_test/` 目录执行行为一致。

### 9.4 示例站点测试
保留并调整：
- `test_jsonplaceholder_api.py`
- `test_jsonplaceholder_resources.py`

新增要求：
- 所有公开基线用例带 `public_baseline` 标记；
- 保留 `jsonplaceholder` 分类标记。

### 9.5 删除测试
直接删除：
- `api_test/tests/test_demo.py`
- `api_test/tests/test_public_api_governance.py`

### 9.6 `platform_core` 测试调整
删除与旧桥接强绑定的测试；
补齐删除后主链路仍成立的断言，确保：
- 解析层测试通过；
- 模板层测试通过；
- 通用规则测试通过；
- 工作区检查测试通过；
- CLI `run` / `inspect` 测试通过。

## 10. 实施顺序
1. 先补配置层测试；
2. 先补 `run_test.py` 行为测试；
3. 再补 `BaseAPI` 去特化测试；
4. 再删旧私有链路测试；
5. 再做 `api_test/` 最小实现；
6. 再处理 `platform_core` 去特化；
7. 每一轮实现后同步更新文档；
8. 最后做全量回归和验收。

## 11. 验收标准
只有同时满足以下条件，本轮才算完成：

### 11.1 代码层
- 不再存在 `config.py` 的有效引用；
- 不再存在 RSA / 私有登录 / 旧 `PublicAPI` 站点特化代码；
- `api_test/` 可作为通用公开站点测试底座运行；
- `platform_core/` 不再依赖某个私有网站的旧目录桥接。

### 11.2 测试层
- `python -m pytest tests/platform_core -v` 通过；
- `python -m pytest api_test/tests -v` 通过；
- `python api_test/run_test.py --public-baseline` 通过；
- `cd api_test && python run_test.py --public-baseline` 通过；
- 不再存在 `private_env` 相关测试口径。

### 11.3 文档层
以下文档必须同步更新并与代码结果一致：
- 仓库根 `README.md`
- `api_test/README.md`
- `api_test/QUICKSTART.md`
- `product_document/架构设计/总体架构设计说明书.md`
- `product_document/架构设计/现有接口自动化测试框架改造方案.md`
- `product_document/架构设计/中间模型设计说明书.md`
- `product_document/架构设计/模板体系与代码生成规范说明书.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`

## 12. 风险与控制

### 风险 1：`platform_core` 当前测试和实现深度绑定旧桥接
控制：
- 先改测试，再删除实现；
- 保持 `run` / `inspect` 主命令稳定。

### 风险 2：`run_test.py` 工作目录问题再次回归
控制：
- 将根目录执行与子目录执行写成显式测试。

### 风险 3：把“通用框架”误写成“只支持 JSONPlaceholder”
控制：
- 保留通用 `BaseAPI`；
- JSONPlaceholder 只作为默认公开示例适配。

### 风险 4：文档与代码再次脱节
控制：
- 每轮实现与测试结束后立即同步文档；
- 不允许最后一次性补文档。

## 13. 结论
本轮重构不是简单的配置迁移，而是一次明确的方向修正：

> 从“带有私有网站历史包袱的测试框架”重构为“通用测试框架 + JSON 配置驱动 + 平台主线可承接的公开测试底座”。

这次重构完成后，`api_test/` 才能真正服务于当前产品设计，而不是继续拖住平台化演进。
