# api_test Quickstart

## 适用范围

本指南对应 2026-04-01 开始的通用测试框架重构阶段。

当前已完成并验证配置收口、运行时治理、`BaseAPI` 工具拆分、公开基线执行入口和代理控制能力。

## 1. 安装依赖

```bash
cd api_test
python -m pip install -r requirements.txt
```

说明：

- `requirements.txt` 已改为固定版本约束；
- 当前仓库禁止使用 `latest`、`>=`、`^` 等宽松依赖写法。

## 2. 查看唯一配置文件

当前新的统一配置文件为：

- [api_config.json](/D:/AI/api-test-platform/api_test/api_config.json)

当前说明：

- 该文件已经建立，并作为当前唯一配置源；
- `config.py` 已删除；
- 后续客户端也应直接读写该文件中的相关字段。

如需开启代理，请在 `api_config.json` 中调整：

```json
"proxy": {
  "enabled": true,
  "url": "http://127.0.0.1:7890"
}
```

说明：

- 默认设计值为 `enabled=false`
- 当前实现会同时为 `http/https` 请求挂代理
- 后续客户端应直接控制这两个字段
- 对 `jsonplaceholder.typicode.com` 相关公开回归，建议按“先开启代理执行，完成后恢复 `enabled=false`”的流程操作

## 3. 运行当前已验证测试

在仓库根目录执行：

```bash
cd api_test && python -m pytest tests -m jsonplaceholder -v --basetemp ..\.pytest_tmp\api_test_jsonplaceholder_acceptance
python api_test/run_test.py --public-baseline
cd api_test && python run_test.py --public-baseline
cd api_test && python -m pytest tests -m "not jsonplaceholder" -v --basetemp ..\.pytest_tmp\api_test_non_jsonplaceholder_acceptance
cd api_test && python -m pytest tests/test_config_loader.py -v --noconftest --basetemp ..\.pytest_tmp\config_loader_after_proxy_restore_fix
python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader
python -m pytest api_test/tests/test_base_api_governance.py api_test/tests/test_common_tools.py -v --noconftest --basetemp .pytest_tmp/base_api_split_docs
python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_base_api_split_full
python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_after_base_api_split
python -m pytest tests -v --basetemp .pytest_tmp/root_after_base_api_split
python api_test/run_test.py --public-baseline
cd api_test && python run_test.py --public-baseline
```

当前结果：

- `12 passed, 27 deselected`
- `12 passed, 27 deselected`
- `12 passed, 27 deselected`
- `27 passed, 12 deselected`
- `6 passed`
- `5 passed`
- `19 passed`
- `39 passed`
- `63 passed`
- `70 passed`
- `12 passed, 27 deselected`
- `12 passed, 27 deselected`

## 4. 当前建议优先使用的入口

以下入口已经完成当前轮基础验证：

- `api_test/conftest.py`
- `api_test/core/base_api.py`
- `api_test/core/common_tools.py`
- `api_test/run_test.py`

补充：

- `api_test` 全量测试回归已通过；
- `run_test.py --public-baseline` 已在仓库根目录和 `api_test/` 目录两种方式下通过；
- `BaseAPI` 的非 HTTP 工具方法已迁移到 `common_tools.py`，当前公共层边界更清晰；
- 代理能力已通过端口探测、真实代理请求和公开基线双入口复验；
- 2026-04-03 正式验收复验已确认：`jsonplaceholder` 相关用例可在临时开启代理后稳定通过，完成后恢复默认关闭仍可保证配置/治理用例通过；
- 默认关闭代理直连公开站点时，最新一次 `api_test` 全量复验出现 `SSL handshake/read timeout`，对外网回归建议优先开启代理。
- 当前已新增中文注释治理测试，`api_config.json` 的中文说明字段不会影响配置加载。
- 当前 `api_test` 通用回归链路已满足 V1 阶段目标，后续更复杂平台能力转入 `platform_core` / V2 阶段继续扩展。

## 5. 下一步参考

如需了解本轮完整目标与范围，优先查看：

- [api_test/README.md](/D:/AI/api-test-platform/api_test/README.md)
- [generic-test-framework-refactor-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-01-generic-test-framework-refactor-design.md)
- [generic-test-framework-refactor.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-01-generic-test-framework-refactor.md)
- [v1-base-api-responsibility-split-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-base-api-responsibility-split-design.md)
- [v1-base-api-responsibility-split.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-base-api-responsibility-split.md)
