

---

# MCP Contract — Season 2 Regression & Inheritance Constitution  
# MCP 合同 —— 第 2 季回归与继承宪法

Status 状态: Constitutional / Enforced  
Applies 适用: Season 2 (MCP introduction and evolution)  
Scope 范围: Regression, inheritance, governance, failure safety  
Non-goal 非目标: MCP 工具功能设计

---

## 0. Definition — Regression Inheritance / 回归继承
> Any Season 2 capability MUST preserve Season 1 life-cycle, replayability, auditability, and be fully disable-able.  
> 第 2 季新增能力必须保留第 1 季的生命循环、可重放、可审计，并且可完全关闭。

Inheritance = No Breakage + Graceful Degradation + Full Auditability  
继承 = 不破坏 + 优雅降级 + 完整可审计  
MCP 关闭时，Season 1 行为必须不变。

---

## 1. Constitutional Anchors / 宪法锚点

### 1.1 Season 1 Frozen Core / 不可动的核心
Season 2 不得修改（除非明确声明 Season 3 迁移）：  
- Event/Ledger: Schema, append-only  
- Memory Store: `schema_version`，迁移纪律  
- Policy Gate: `proposed → check → committed/blocked`  
- System Process Pack: boot 语义（recover/warm），`run_id` 连续  
- Regression Suite: P00, P10, P14, P20A  
以上构成 **Kernel ABI**：`intent → gate → ledger → replay → process`。违背即违宪。

---

### 1.2 Allowed Extensions / 允许的扩展面
MCP 只能通过以下接口挂载：  
- Tool ABI / Capability Bus  
- Router/Selector（persona-aware, policy-aware）  
- Observability Extensions（不得改变现有指标定义）  
- Policy Proposals（仅增量，不可旁路宪法路径）  
- Optional Stores（仅增量，不得替换/遮蔽 `memory_store`）

---

## 2. Regression Layering Model / 分层回归模型
Season 2 回归分三层，严禁混合。

---

### Layer A — Season 1 Invariants / 第一层：S1 不变量
- 必须随每次 MCP 变更执行。  
- 需通过：P00、P10、P14、P20A、仓库卫生、干净工作区。  
- 规则：Layer A 失败的改动即为无效。

---

### Layer B — MCP Contract Tests / 第二层：MCP 合同测试
- 定义 MCP 最低宪法行为。  
#### B1 MCP Disabled：关闭 MCP，行为等同 Season 1（路由、输出、账本）。  
#### B2 MCP Enabled, No Calls：开启但未被选择；无调用、无副作用。  
#### B3 MCP Call Logged：调用时账本记录 `capability_provider="mcp"`, `server_id`, `tool_name`, `request_id/hash`, `policy_basis`, `latency_ms`, `status (ok|timeout|error|blocked)`，确保可观测。  
#### B4 MCP Failure Safe：服务器不可用/超时/工具错误时，系统必须 fallback/blocked，禁止静默、无日志、崩溃。

---

### Layer C — MCP Integration Scenarios / 第三层：集成场景（可选/夜跑）
- 示例：多 MCP 路由、人格驱动选择、延迟/成本趋势、多会话压力隔离。  
- 规则：Layer C 失败不阻塞合并，除非提升为 Layer B。

---

## 3. MCP Degradability Rules / 可降级性原则

MCP is treated as a **pluggable organ**, not a vital system.

---

### Rule 3.1 — Default Off

* MCP MUST be disabled by default
* Explicit configuration is required to enable

**Regression invariant:**

> Default-off MCP MUST produce identical behavior to Season 1.

---

### Rule 3.2 — Capability Audit Is Mandatory

Every MCP invocation MUST produce an auditable trail.

No exceptions.

---

### Rule 3.3 — Failure Degrades, Never Crashes

On MCP failure, only these outcomes are allowed:

* graceful fallback
* explicit policy-based block
* bounded retry (policy-controlled)

**Never allowed:**

* silent ignore
* implicit success
* uncontrolled retries

---

## 4. Regression Redlines (Absolute Prohibitions)

MCP MUST NEVER:

* Write directly to `memory_store`
* Modify existing ledger entries
* Change `schema_version`
* Become a required dependency for P00–P20A
* Introduce non-observable execution paths

Violating any redline constitutes a **constitutional breach**.

---

## 5. Branching & Versioning Strategy

### Branches

* `main`

  * Season 1 frozen core
  * Accepts Season 2 changes ONLY if Layer A + B pass
* `mcp-capability-bus`

  * Primary Season 2 development branch
* feature branches

  * Derived from `mcp-capability-bus`

---

### Tags

* `season1-p20A` — Season 1 sealed baseline
* `season2-mcp-v0` — First MCP version with full contract compliance

---

## 6. Repository Artifacts (Required)

```
docs/
  MCP_CONTRACT.md
tests/
  test_mcp_contract_disabled.py
  test_mcp_contract_enabled_no_calls.py
  test_mcp_contract_call_logged.py
  test_mcp_contract_failure_safe.py
```

---

## 7. Canonical Regression Command Set

### Quick Regression (Per Commit)

```bash
# Season 1 invariants
PYTHONPATH=. python3 projects/p00-agent-os-mvp/src/main.py
PYTHONPATH=. python3 projects/p10-minimal-system-process-pack/main.py
PYTHONPATH=. python3 projects/p14-session-isolation/src/main.py
PYTHONPATH=. python3 projects/p20-preference-aware-router-mocking/src/main.py

# Governance
pytest tests/test_repo_hygiene.py

# Season 2 MCP contracts
pytest -q tests/test_mcp_contract_disabled.py
pytest -q tests/test_mcp_contract_enabled_no_calls.py
pytest -q tests/test_mcp_contract_call_logged.py
pytest -q tests/test_mcp_contract_failure_safe.py
```

---

## 8. Final Principle

> **MCP is never allowed to become a shortcut to power.**
> It is only a capability interface:
>
> **explicit · optional · auditable · degradable**

---

