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

## 3. 运行当前已验证测试

在仓库根目录执行：

```bash
python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader
```

当前结果：

- `5 passed`

## 4. 当前不应作为完成态使用的入口

以下入口仍在本轮改造中，当前文档不把它们作为已复验通过的能力：

- `api_test/conftest.py`
- `api_test/core/base_api.py`
- `api_test/run_test.py`
- `api_test` 全量测试回归

## 5. 下一步参考

如需了解本轮完整目标与范围，优先查看：

- [api_test/README.md](/D:/AI/api-test-platform/api_test/README.md)
- [generic-test-framework-refactor-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-01-generic-test-framework-refactor-design.md)
- [generic-test-framework-refactor.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-01-generic-test-framework-refactor.md)
