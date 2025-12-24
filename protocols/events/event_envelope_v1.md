# Event Envelope Protocol v1

**Status:** Stable  
**Scope:** OS-level runtime events  
**Audience:** Runtime / Agent / Governance engineers  
**Version:** 1.0

## Purpose

The Event Envelope Protocol defines the minimal, non-drifting structure for runtime events.
Events are not logs; they are durable, structured facts that support auditability,
causal replay, and long-term system memory.

Once an event is written to `events.jsonl`, its structure and semantics must not be
changed implicitly.

## Design Principles

1. Determinism: The same payload must produce the same hash.
2. Minimal but sufficient: The envelope is fixed; semantics evolve via payload.
3. Machine-first: Fields must be stable and parseable.
4. Auditability: Important actions leave structured evidence.
5. Forward compatibility: New capabilities require new versions or new fields.

## Envelope Structure

Each event is a single JSON object (one line, JSONL) with the following top-level fields:

```json
{
  "schema_version": "1.0",
  "event_type": "...",
  "session_id": "...",
  "trace_id": "...",
  "ts": "...",
  "payload": { ... },
  "payload_hash": "..."
}
```

## Field Definitions

Field | Type | Required | Description
---|---|---|---
`schema_version` | string | yes | Protocol version, fixed as `"1.0"` in v1.
`event_type` | string | yes | Semantic category, e.g. `session.start`, `user.message`, `agent.reply`, `session.end`.
`session_id` | string | yes | Session identifier for a lifecycle instance.
`trace_id` | string | yes | Correlation identifier for a causal chain.
`ts` | string | yes | UTC timestamp in ISO 8601 / RFC3339 format with milliseconds and trailing `Z`.
`payload` | object | yes | Event-specific structured data. Defaults to `{}`.
`payload_hash` | string | yes | SHA-256 hex digest of the canonicalized `payload`.

## Canonicalization Rules

- `payload` is serialized as JSON with:
  - keys sorted
  - no whitespace
  - `ensure_ascii=false`
- `payload_hash` is the SHA-256 hex digest of the canonicalized `payload` string.

## Example

```json
{
  "schema_version": "1.0",
  "event_type": "user.message",
  "session_id": "p00-demo-session",
  "trace_id": "9b9b9c1e-2b1c-4df6-9e42-7a1b5e2b6d3a",
  "ts": "2024-12-17T03:21:45.123Z",
  "payload": {
    "text": "Hello, world."
  },
  "payload_hash": "9e6b5f0a1bcb13cdb2f8b2f6c36a9f59b8c64d3b7d2a2f3c7b2b84b1a5c9f1d2"
}
```

### 4.13 `prev_envelope_hash` (optional, recommended)

* 指向同一 session 中上一条事件的 `envelope_hash`
* 形成 **hash-linked event chain**
* 用于审计与防篡改检测

---

## 5. Event Ordering & Causality（顺序与因果）

* **时间顺序 ≠ 因果顺序**
* 因果关系由：

  * `trace_id`
  * `span_id`
  * `parent_span_id`
    决定

Replay / Debug / Audit 时 **必须优先使用因果结构**。

---

## 6. Backward & Forward Compatibility（兼容性原则）

* **旧事件永远有效**
* 新字段只能：

  * 增加为 optional
  * 或通过提升 `schema_version` 引入
* 禁止：

  * 重解释旧字段语义
  * 静默修改字段口径

---

## 7. Non-Goals（明确不做的事）

* 不试图描述 UI 行为
* 不作为人类日志系统
* 不嵌入模型 prompt 或思维链
* 不保证防篡改（只保证可检测）

---

## 8. Summary（一句话总结）

> **Event Envelope v1 定义了什么才算“真的发生过”。**
>
> 在这个 OS 里：
> **没进事件账本的事，从系统角度等于没发生。**

---
