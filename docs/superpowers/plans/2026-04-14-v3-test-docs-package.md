# V3 Test Docs Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete V3 test-document package, including one total index document and three detailed phase test documents for P0, P1, and P2.

**Architecture:** Follow the confirmed V3 test-docs design: keep one lightweight index document for rules and matrices, then split detailed cases into three phase-scoped documents. After the package is written, sync the V3 stage plan, README, and local progress records so repository status stays consistent.

**Tech Stack:** Markdown documentation, repository phase documents, local planning records

---

### Task 1: Create The V3 Test Index Document

**Files:**
- Create: `docs/superpowers/plans/2026-04-14-v3-test-docs-package.md`
- Create: `product_document/测试文档/详细测试用例说明书(V3-总索引).md`
- Modify: `product_document/阶段文档/V3阶段工作计划文档.md`

- [ ] **Step 1: Write the index document skeleton**

```markdown
# 详细测试用例说明书（V3-总索引）
## 1. 文档说明
## 2. V3 测试目标
## 2.1 当前公开接口测试基线站点
## 3. 适用范围与阶段边界
## 4. 文档包结构说明
## 5. 编号规则
## 6. 测试分层定义
## 7. 分阶段独立验收原则
## 8. 阶段测试矩阵
## 9. 文档映射关系
## 10. 当前维护规则与更新要求
## 11. 结论
```

- [ ] **Step 2: Fill the index rules, matrices, and mapping content**

```markdown
- 明确 `TC-V3-Px-LAYER-XXX` 的统一编号规则
- 明确 `DOC / MODEL / MIG / ISO / API / EXEC / UI / INT` 的固定层级
- 明确 `P0 / P1 / P2` 各自独立验收与 V3 总体验收关系
- 明确 `V3-总索引` 与 `V3-P0 / P1 / P2` 的职责边界
```

- [ ] **Step 3: Review the index document for duplicated detailed cases**

Run: `rg -n "### TC-V3" "product_document/测试文档/详细测试用例说明书(V3-总索引).md"`
Expected: no matches, because the index document should not duplicate detailed test cases

- [ ] **Step 4: Sync V3 stage plan references**

```markdown
- 在 `V3阶段工作计划文档.md` 中补充 V3 测试文档关联关系
- 将 V3 测试文档设计/编写进度写入开发进度和测试进度记录
```

---

### Task 2: Create The V3 P0 Detailed Test Document

**Files:**
- Create: `product_document/测试文档/详细测试用例说明书(V3-P0).md`
- Modify: `product_document/阶段文档/V3阶段工作计划文档.md`

- [ ] **Step 1: Write the P0 document skeleton**

```markdown
# 详细测试用例说明书（V3-P0）
## 1. 文档说明
## 2. P0 测试目标
## 2.1 当前公开接口测试基线站点
## 3. P0 测试边界
## 4. P0 测试分层结构
## 5. 文档约束测试用例
## 6. 模型测试用例
## 7. 迁移与兼容测试用例
## 8. 隔离与边界测试用例
## 9. 服务与接口测试用例
## 10. 执行与调度测试用例
## 11. 交互入口测试用例
## 12. 主线集成与阶段验收测试用例
## 13. P0 通过标准
## 14. P0 不通过判定
## 15. 变更记录
```

- [ ] **Step 2: Add detailed P0 cases using the approved template**

```markdown
- 编号
- 名称
- 目标
- 背景
- 前置条件
- 输入
- 执行步骤
- 检查点
- 失败判定
- 优先级
- 预期结果
- 归属阶段验收
- 后续联动测试
```

- [ ] **Step 3: Ensure P0 focus stays on migration, isolation, and minimal governance UI**

Run: `rg -n "Windows Demo|AI 自愈|macOS 正式实现" "product_document/测试文档/详细测试用例说明书(V3-P0).md"`
Expected: only boundary references, not P0 core commitments

- [ ] **Step 4: Sync P0-related progress in the V3 stage plan**

```markdown
- 将 `V3-TEST-002` 更新为已完成
- 补充 P0 测试文档已建立的说明
```

---

### Task 3: Create The V3 P1 Detailed Test Document

**Files:**
- Create: `product_document/测试文档/详细测试用例说明书(V3-P1).md`
- Modify: `product_document/阶段文档/V3阶段工作计划文档.md`

- [ ] **Step 1: Write the P1 document skeleton**

```markdown
# 详细测试用例说明书（V3-P1）
## 1. 文档说明
## 2. P1 测试目标
## 2.1 当前公开接口测试基线站点
## 3. P1 测试边界
## 4. P1 测试分层结构
## 5. 文档约束测试用例
## 6. 模型测试用例
## 7. 迁移与兼容测试用例
## 8. 隔离与边界测试用例
## 9. 服务与接口测试用例
## 10. 执行与调度测试用例
## 11. 交互入口测试用例
## 12. 主线集成与阶段验收测试用例
## 13. P1 通过标准
## 14. P1 不通过判定
## 15. 变更记录
```

- [ ] **Step 2: Add detailed P1 cases for permissions, formal traffic-capture execution, portal deepening, Windows demo, and scheduling**

```markdown
- 权限体系与审计治理
- 抓包正式执行闭环
- Web 正式入口深化
- Windows Demo 实测链路
- 调度与执行中心
```

- [ ] **Step 3: Verify the Windows route follows the approved browser-first, Tauri-priority strategy**

Run: `rg -n "Tauri|浏览器先验|阶段性打包复验" "product_document/测试文档/详细测试用例说明书(V3-P1).md"`
Expected: matches present in P1 UI / INT sections

- [ ] **Step 4: Sync P1-related progress in the V3 stage plan**

```markdown
- 将 `V3-TEST-003` 更新为已完成
- 补充 P1 测试文档已建立的说明
```

---

### Task 4: Create The V3 P2 Detailed Test Document

**Files:**
- Create: `product_document/测试文档/详细测试用例说明书(V3-P2).md`
- Modify: `product_document/阶段文档/V3阶段工作计划文档.md`

- [ ] **Step 1: Write the P2 document skeleton**

```markdown
# 详细测试用例说明书（V3-P2）
## 1. 文档说明
## 2. P2 测试目标
## 2.1 当前公开接口测试基线站点
## 3. P2 测试边界
## 4. P2 测试分层结构
## 5. 文档约束测试用例
## 6. 模型测试用例
## 7. 迁移与兼容测试用例
## 8. 隔离与边界测试用例
## 9. 服务与接口测试用例
## 10. 执行与调度测试用例
## 11. 交互入口测试用例
## 12. 主线集成与阶段验收测试用例
## 13. P2 通过标准
## 14. P2 不通过判定
## 15. 变更记录
```

- [ ] **Step 2: Add detailed P2 cases for AI governance boundaries, approval gates, rollback, and auditability**

```markdown
- AI 建议不是事实源
- 审批门禁
- 回退与失败回滚
- 留痕与审计
- 独立阶段验收
```

- [ ] **Step 3: Verify P2 does not overpromise autonomous AI implementation**

Run: `rg -n "自动自愈正式落地|无人审批执行" "product_document/测试文档/详细测试用例说明书(V3-P2).md"`
Expected: only boundary or negative cases, not committed deliverables

- [ ] **Step 4: Sync P2-related progress in the V3 stage plan**

```markdown
- 将 `V3-TEST-004` 更新为已完成
- 补充 P2 测试文档已建立的说明
```

---

### Task 5: Sync The Repository-Level Documentation And Local Records

**Files:**
- Modify: `README.md`
- Modify: `product_document/阶段文档/全阶段工作规划文档.md`
- Modify: `product_document/阶段文档/V3阶段工作计划文档.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

- [ ] **Step 1: Update README to point to the V3 test-docs package**

```markdown
- 在“当前建议查看顺序”中加入 V3 总索引和 P0 / P1 / P2 测试文档
- 在“当前状态”中补记 V3 测试文档已建立
```

- [ ] **Step 2: Update the all-phase plan and V3 stage plan status**

```markdown
- 在 `全阶段工作规划文档.md` 中补记 V3 测试文档已完成设计 / 编写
- 在 `V3阶段工作计划文档.md` 中更新 V3-DOC-005、V3-TEST-002、V3-TEST-003、V3-TEST-004、V3-TEST-005 的状态
```

- [ ] **Step 3: Update local memory files**

```markdown
- 在 `task_plan.md` 中记录 V3 测试文档包正式编写
- 在 `findings.md` 中记录测试文档拆分与编号结论
- 在 `progress.md` 中记录当前轮执行结果和下一步
```

- [ ] **Step 4: Run static validation on the new documents**

Run: `rg -n "TBD|TODO|待补|待定" "product_document/测试文档/详细测试用例说明书(V3-总索引).md" "product_document/测试文档/详细测试用例说明书(V3-P0).md" "product_document/测试文档/详细测试用例说明书(V3-P1).md" "product_document/测试文档/详细测试用例说明书(V3-P2).md"`
Expected: no matches
