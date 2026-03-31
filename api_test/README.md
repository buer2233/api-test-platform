# api_test

`api_test/` 是当前仓库保留的历史接口自动化测试框架底座，也是 V1 过渡阶段的本地回归基线之一。

它当前承担两类职责：

1. 提供原有 `BaseAPI` / `PublicAPI` 能力与公开示例；
2. 作为新平台能力落地前的过渡验证对象，帮助识别旧框架中与平台化方向不兼容的部分。

---

## 1. 目录说明

```text
api_test/
├─ core/                  # 基础请求能力、会话构建与私有环境依赖治理
├─ tests/                 # 历史 pytest 用例
├─ test_data/             # 测试数据
├─ report/                # 测试报告输出目录
├─ config.py              # 当前配置
├─ conftest.py            # pytest fixture / hook
├─ pytest.ini             # pytest 配置与测试标记
├─ requirements.txt       # 依赖清单
├─ run_test.py            # 原有测试执行入口
└─ README.md              # 本文件
```

---

## 2. 安装依赖

```bash
cd api_test
python -m pip install -r requirements.txt
```

---

## 3. 运行测试

### 默认本地回归

```bash
cd api_test
python -m pytest -v
```

截至 2026-03-31，默认本地结果为：

- `15 passed, 4 skipped`

### 公开示例用例

```bash
cd api_test
python -m pytest tests/test_baidu_sug.py -v
```

### 私有环境登录链路用例

`tests/test_demo.py` 中依赖真实账号、私有环境与登录链路的用例都标记为 `private_env`，默认不会纳入本地回归。

如需显式执行：

```powershell
cd api_test
$env:ENABLE_PRIVATE_API_TESTS = '1'
python -m pytest tests/test_demo.py -v -m private_env
```

说明：

- 这类用例依赖私有环境、真实账号和有效 RSA 公钥。
- 当前必须通过环境变量 `API_TEST_RSA_PUBLIC_KEY` 显式提供有效公钥，缺失时 `BaseAPI.password_rsa()` 会直接报错，避免继续使用占位配置。
- 回归结束后，如需恢复当前会话环境变量，可执行 `Remove-Item Env:ENABLE_PRIVATE_API_TESTS`。

---

## 4. 当前可用测试标记

当前 `pytest.ini` 中已声明以下标记：

- `basic`
- `smoke`
- `auth`
- `user`
- `workflow`
- `document`
- `attend`
- `calendar`
- `crm`
- `report`
- `P0`
- `P1`
- `P2`
- `P3`
- `integration`
- `unit`
- `regression`
- `private_env`

---

## 5. 当前基线说明

`api_test/` 仍然是旧框架，不代表未来平台最终形态。当前阶段对它的要求是：

1. 公开示例和纯本地工具类测试可稳定执行；
2. 依赖私有环境的示例必须被显式隔离，不能污染默认回归；
3. 会话、配置和私有环境依赖需要逐步拆分，不能继续堆积在单一 `BaseAPI` 中；
4. 与新平台方向冲突的能力需要逐步治理，而不是继续无规则扩展。

---

## 6. 当前环境变量入口

`api_test/` 当前已支持以下显式环境变量入口：

- `API_TEST_BASE_URL`
- `API_TEST_IS_HTTPS`
- `API_TEST_TIMEOUT`
- `API_TEST_RSA_PUBLIC_KEY`

---

## 7. 与 V1 平台核心的关系

当前仓库的 V1 第一阶段主基线已经转移到：

- `platform_core/`
- `tests/platform_core/`

`api_test/` 的定位是：

- 提供过渡期底座能力；
- 为后续改造提供现状参考；
- 作为本地综合回归的一部分，帮助确认旧能力没有被本轮改动破坏。

---

## 8. 结论

如果你要验证 V1 当前主能力，请优先运行：

```bash
python -m pytest tests/platform_core -v
```

说明：

- 根目录 `pytest.ini` 已统一配置 `--basetemp=.pytest_tmp`，`platform_core` 执行器也会为生成工作区传入本地临时目录，因此无需再手工指定临时目录参数。

如果你要确认旧框架基线没有被破坏，再运行：

```bash
cd api_test
python -m pytest -v
```
