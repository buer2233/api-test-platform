# api_test Quickstart

## 适用范围

本指南对应 2026-04-01 开始的通用测试框架重构阶段。

当前已完成并验证的能力只有配置收口第一步，运行时、执行入口和公开基线回归仍在继续迁移。

## 1. 安装依赖

```bash
cd api_test
python -m pip install -r requirements.txt
```

## 2. 查看唯一配置文件

当前新的统一配置文件为：

- [api_config.json](/D:/AI/api-test-platform/api_test/api_config.json)

当前说明：

- 该文件已经建立，并作为后续唯一配置源；
- 旧 `config.py` 仍在迁移过程中，尚未完全删除；
- 当前阶段不要再新增对 `config.py` 的新引用。

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

## 3. 运行当前已验证测试

在仓库根目录执行：

```bash
python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader
python -m pytest api_test/tests/test_base_api_governance.py -v --noconftest --basetemp .pytest_tmp/base_api
```

当前结果：

- `5 passed`
- `10 passed`
- `29 passed`
- `12 passed, 17 deselected`
- `12 passed, 17 deselected`
- `1 failed, 28 passed`

## 4. 当前不应作为完成态使用的入口

以下入口仍在更大范围重构中，但当前轮已经完成基础验证：

- `api_test/conftest.py`
- `api_test/core/base_api.py`
- `api_test/run_test.py`

补充：

- `api_test` 全量测试回归已通过；
- `run_test.py --public-baseline` 已在仓库根目录和 `api_test/` 目录两种方式下通过；
- 代理能力已通过端口探测、真实代理请求和公开基线双入口复验；
- 默认关闭代理直连公开站点时，最新一次 `api_test` 全量复验出现 `SSL handshake/read timeout`，对外网回归建议优先开启代理。

## 5. 下一步参考

如需了解本轮完整目标与范围，优先查看：

- [api_test/README.md](/D:/AI/api-test-platform/api_test/README.md)
- [generic-test-framework-refactor-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-01-generic-test-framework-refactor-design.md)
- [generic-test-framework-refactor.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-01-generic-test-framework-refactor.md)
