

---

# protocols/observability/observability_v1.md

## Observability Protocol v1

**Status:** Stable
**Applies to:** Runtime / Policy / Memory / Tooling
**First introduced in:** P09 — Observability v1

---

## 0. 核心原则（Constitutional Principles）

1. **Observability produces facts, not opinions**
   可观测性不是调试工具，而是系统事实的生成机制。

2. **Definition before precision**
   口径优先于精度。粗估可以，漂移不可以。

3. **Events first, dashboards later**
   原始事件是本体，指标是可重算的派生物。

4. **Replayability is mandatory**
   所有统计必须可由事件流离线重算。

5. **Layer separation is non-negotiable**
   IR / Policy / Runtime / Tool 的观测必须分层。

---

## 1. Observability 的职责边界

Observability Protocol **只负责回答三类问题**：

1. 系统**发生了什么**（What happened）
2. 系统**花了多少代价**（How much it cost）
3. 系统**是否正在劣化**（Is it regressing）

它 **不负责**：

* 决策（Decision）
* 纠错（Correction）
* 优化策略（Optimization policy）

这些属于 Policy / Scheduler 层。

---

## 2. 观测层级划分（Observation Layers）

所有观测事件 **必须** 标注其所属层级：

| Layer   | Description      |
| ------- | ---------------- |
| IR      | 语义编译、事实识别、原语生成   |
| Policy  | 规则校验、门禁、治理判断     |
| Runtime | Agent 生命周期、调度、路径 |
| Tool    | 外部工具 / API 调用    |

`layer` 是 **强制字段**。

---

## 3. 标准观测事件（Canonical Events）

### 3.1 Run Lifecycle

```json
{
  "event_type": "run_started",
  "run_id": "uuid",
  "app_name": "p00-agent-os-mvp",
  "timestamp": "iso8601"
}
```

```json
{
  "event_type": "run_finished",
  "run_id": "uuid",
  "status": "success | failed | aborted",
  "timestamp": "iso8601"
}
```

---

### 3.2 Tool Invocation

```json
{
  "event_type": "tool_call_started",
  "run_id": "uuid",
  "tool_name": "string",
  "layer": "tool",
  "timestamp": "iso8601"
}
```

```json
{
  "event_type": "tool_call_finished",
  "run_id": "uuid",
  "tool_name": "string",
  "status": "success | error",
  "latency_ms": 123,
  "timestamp": "iso8601"
}
```

---

### 3.3 Policy Gate

```json
{
  "event_type": "policy_check_started",
  "run_id": "uuid",
  "policy_name": "string",
  "layer": "policy",
  "timestamp": "iso8601"
}
```

```json
{
  "event_type": "policy_check_finished",
  "run_id": "uuid",
  "policy_name": "string",
  "decision": "allow | block",
  "timestamp": "iso8601"
}
```

---

### 3.4 Memory Writes

```json
{
  "event_type": "memory_write_proposed",
  "run_id": "uuid",
  "memory_zone": "active | legacy",
  "schema_version": "vX",
  "timestamp": "iso8601"
}
```

```json
{
  "event_type": "memory_write_committed | memory_write_blocked",
  "run_id": "uuid",
  "reason": "string",
  "timestamp": "iso8601"
}
```

---

### 3.5 Error Events

```json
{
  "event_type": "error_raised",
  "run_id": "uuid",
  "layer": "ir | policy | runtime | tool",
  "error_type": "string",
  "trace_id": "string",
  "timestamp": "iso8601"
}
```

---

## 4. 核心指标定义（Metrics v1）

### 4.1 `tool_calls_total`

**Definition**
工具调用完成次数。

**Counting rules**

* 只统计 `tool_call_finished`
* retry **算多次**
* cache hit **算一次调用**

**Dimensions**

* tool_name
* status
* app_name

---

### 4.2 `errors_total`

**Definition**
系统显式抛出的错误数量。

**Counting rules**

* 只统计 `error_raised`
* 同一 trace_id 可多次计数

**Dimensions**

* layer
* error_type

---

### 4.3 `latency_ms`

**Definition**
事件完成时间减去开始时间。

**Tracked scopes**

* run_total
* tool_call
* policy_check
* memory_write

---

### 4.4 `token_estimate`

**Definition**
LLM token 使用量的估计值。

**Notes**

* 允许粗估
* 必须长期一致

**Fields**

* prompt_tokens
* completion_tokens
* total_tokens

---

### 4.5 `cost_estimate`

**Definition**
基于 token_estimate × 单价表的成本估算。

**Notes**

* 精度不要求高
* 用于趋势与回归判断

---

## 5. 回归与阈值（Regression Gates）

Observability v1 **允许定义但不强制执行** 以下规则：

* latency 增幅 > X% → warning
* tool_calls_total 突增 → investigate
* cost_estimate 超预算 → policy hook
* error_rate 连续上升 → block deployment

这些规则 **只生成事实，不做决策**。

---

## 6. 数据保存与重算原则

1. 原始事件 **不可修改**
2. 聚合结果 **可丢弃**
3. 任何指标必须可由事件流重算
4. 事件至少保存至系统可追溯期结束

---

## 7. 版本演进说明

* v1：单机 / 单 agent / 基础事实层
* v2（计划）：multi-agent / cross-run correlation
* v3（计划）：governance-grade observability

---

## 8. 非目标（Explicit Non-Goals）

* 实时可视化
* APM 自动优化
* 智能调参

这些属于更高层的系统策略。

---

## 9. 结语

> **If P07 decides what is allowed,
> and P08 decides what persists,
> then P09 decides what is real.**

Observability is the system’s memory of its own behavior.

---

