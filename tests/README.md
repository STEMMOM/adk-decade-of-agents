# System Identity & Observability Tests  
# 系统身份与可观测性测试

This directory contains **protocol-level tests** that function as
**constitutional guards** for a long-lived, replayable agent system.  

本目录包含**协议级测试**，它们不是普通功能测试，而是作为
**长寿命、可回放智能系统的“宪法守卫”**存在。

These tests define **non-negotiable invariants** around identity, time,
and observability. Once established, they must never silently regress.

这些测试定义了围绕**身份、时间与可观测性**的
**不可协商不变量**，一旦确立，绝不允许被悄然破坏。

---

## Test Groups  
## 测试分组

### 1. Runtime Observability Invariants  
### 运行时可观测性不变量

- **File 文件**:  
  `test_observability_run_id_invariant.py`

- **Purpose 目的**:  
  Ensure that runtime observability **never writes**
  `run_id = null` or `run_id = "unknown"`.  
  The latest active system run **must always be identifiable**.

  确保运行时可观测性数据**绝不写入**
  `run_id = null` 或 `run_id = "unknown"`，  
  系统的最新运行实例**必须始终可识别**。

- **Boundary 边界**:  
  Runtime write path (`observability.log_event`).  
  运行时写入路径。

---

### 2. Export Boundary Invariants (P09)  
### 导出边界不变量（P09）

- **File 文件**:  
  `test_obs_export_p09_invariants.py`

- **Purpose 目的**:  
  Ensure exported P09 observability data:
  - Uses **system-level run identifiers** (`run_...`)
  - Never falls back to legacy identifiers (`p00-...`) or `unknown`
  - Preserves `session_id` for `tool_call_*` events

  确保导出的 P09 可观测性数据：
  - 使用**系统级 run_id**（`run_...`）
  - 不得回退到旧标识（`p00-...`）或 `unknown`
  - `tool_call_*` 事件必须保留 `session_id`

- **Boundary 边界**:  
  Exporter (`obs_export_p09.py`).  
  导出器边界。

---

### 3. Smoke Tests (Transitional)  
### 冒烟测试（过渡期）

- **File 文件**:  
  `test_p09_observability_smoke.py`

- **Purpose 目的**:  
  Provide high-level sanity checks for the P09 observability pipeline.  
  These tests are **early warning signals**, not formal invariants.

  为 P09 可观测性管线提供高层 sanity 检查，  
  属于**早期预警机制**，而非正式不变量。

- **Status 状态**:  
  Transitional. Over time, these tests should be:
  - Refined
  - Split
  - Absorbed into explicit invariant tests

  过渡状态。未来将被：
  - 精化
  - 拆分
  - 并入显式不变量测试体系

---

## Design Philosophy  
## 设计理念

- **Runtime invariants protect the system while it is alive.**  
  运行时不变量保护“活着的系统”。

- **Export invariants protect data once it leaves runtime.**  
  导出不变量保护离开运行时后的数据。

- **Smoke tests warn early but are not authoritative.**  
  冒烟测试用于早期预警，但不具备裁决权。

- **Identity semantics are enforced by invariants, not convention.**  
  身份语义由不变量强制，而不是靠约定或习惯。

---

## Test Classifications  
## 测试分类制度

Tests in this repository are intentionally classified to distinguish
**historical guarantees** from **developmental flexibility**.

本仓库的测试被有意分级，用于区分
**历史不可破坏性**与**开发期灵活性**。

- **institution**  
  *Constitutional invariants.*  
  These tests define protocol- and history-level red lines.  
  If they fail, **system identity, history, or legality has been violated**.

  **宪法级不变量测试**。  
  定义协议与历史红线，一旦失败，意味着  
  **系统身份、历史或合法性被破坏**。

- **gate**  
  *Sovereign release gate.*  
  Must be green before any release.

  **主权发布门禁测试**。  
  发布前必须全部通过。

- **legacy**  
  *Non-blocking tests.*  
  Represent technical debt or transitional behavior.  
  Failures are tolerated but tracked.

  **非阻塞测试**。  
  表示技术债或过渡行为，允许失败，但必须被追踪。

---

> **Principle 原则**  
> A system that cannot defend its own identity in tests  
> cannot be trusted to evolve safely over time.
>
> 一个无法在测试中捍卫自身身份的系统，  
> 不具备安全演化的资格。
