# P10 — Minimal System Process Pack  
# P10 最小系统进程包

## System Constitution v1 / 系统宪法 v1

> This document is not a tutorial.  
> It is a constitutional declaration of what the system **is**,  
> what it **must do**, and what it **must never violate**.
> 本文不是教程，而是对系统“是什么、必须做什么、绝不能违背什么”的宪法式声明。

---

## I. Purpose / 存在目的

P10 exists to establish a single, irreversible fact:

> **This system is no longer a script.  
> It is a process that exists in time.**
> **系统不再是脚本，而是存在于时间中的进程。**

From P10 onward, the system MUST be able to:
- start,
- stop,
- crash,
- recover,
- and explain its own history.
自 P10 起，系统必须能：启动、停止、崩溃、恢复，并解释自己的历史。

Any system that cannot do this is not a long-term system.
不能做到这些的系统，不是长期系统。

---

## II. Ontology / 本体声明

From P10 forward, the system recognizes three identities:

1. **system_id**  
   Identifies *which system this is* across time.
   标识跨时间的“哪个系统”。

2. **process_id**  
   Identifies *which process instance is running*.
   标识“哪个进程实例”在运行。

3. **run_id**  
   Identifies *which execution cycle occurred*.
   标识“哪次执行循环”发生。

These identities are not implementation details.  
They are **facts written into the ledger**.
这些身份不是实现细节，而是写入账本的事实。

---

## III. Lifecycle Events / 生命周期事件

P10 defines the **minimum system lifecycle**.
P10 定义最小系统生命周期。

### Required Events
- `system.boot`
- `system.shutdown`
必需事件：`system.boot`、`system.shutdown`

Every execution MUST begin with `system.boot`.

A normal execution MUST end with `system.shutdown`.
每次执行必须以 `system.boot` 开始，以 `system.shutdown` 结束。

There are no exceptions.
没有例外。

---

## IV. Boot Modes / 启动模式

Every `system.boot` MUST declare exactly one `boot_mode`.
每个 `system.boot` 必须声明一个且仅一个 `boot_mode`。

### 1. `cold`
- No durable system state exists.
- The system is born for the first time.
无持久状态，首次启动。

### 2. `warm`
- Durable state exists.
- The previous run was complete.
有持久状态，上一运行完整结束。

### 3. `recover`
- Durable state exists.
- The previous run was **incomplete**.
- The system explicitly acknowledges this fact.
有持久状态，上一运行不完整，系统需显式承认。

Recovery is not failure.  
Recovery is **honesty**.
恢复不是失败，而是诚实。

---

## V. Crash & Recovery Law / 崩溃与恢复法则

A run is defined as:

- **complete**  
  if and only if a matching `system.shutdown` exists.
有匹配的 `system.shutdown` 则为完整。

- **incomplete**  
  if `system.boot` exists without a corresponding `system.shutdown`.
有 `system.boot` 无对应 `system.shutdown` 则为不完整。

### Constitutional Rule
If the most recent run is incomplete,  
the next startup MUST:

- emit `system.boot` with `boot_mode = recover`
- set `recovered_from_run_id`
若最近一次运行不完整，下一次启动必须以 recover 模式并记录 `recovered_from_run_id`。

Silent recovery is forbidden.
禁止静默恢复。

---

## VI. Invariants / 不可违背的硬约束

1. Every `run_id` SHOULD have exactly one `system.boot`.

2. Every `run_id` MUST have at most one `system.shutdown`.

3. A run without `system.shutdown` is **incomplete by definition**.

4. Incomplete runs MUST influence the next boot.

5. Lifecycle facts MUST be written to the **Event Ledger**, not Memory.

These invariants are not preferences.  
They are **law**.
以上不是偏好，而是法律。

---

## VII. Separation of Concerns / 边界宪法

P10 explicitly enforces the following boundaries:

- **Event Ledger**  
  Records system facts in time.

- **Memory**  
  Records world-level responsibility and meaning.

Lifecycle events MUST NOT mutate Memory.

Observability MUST NOT retroactively rewrite facts.
事件账本记录系统事实；记忆记录世界责任。生命周期事件不得修改记忆；可观测性不得改写历史事实。

---

## VIII. Non-Goals / 明确不做的事

P10 does NOT attempt to:
- schedule agents,
- optimize intelligence,
- checkpoint full state,
- manage concurrency,
- predict future behavior.
P10 不做：调度智能体、优化智能、做全量快照、管理并发、预测未来。

P10 only guarantees one thing:

> **The system can survive time.**
P10 只保证一件事：**系统能在时间中存活。**

---

## IX. Completion Criteria / 完成判据

P10 is considered complete when:

- Normal runs always close (boot → shutdown).
- Crashes leave observable traces.
- Recovery is explicit and auditable.
- The ledger alone is sufficient to reconstruct system history.
当正常运行总能关闭、崩溃可观、恢复显式可审计、仅凭账本可重建历史时，P10 即完成。

At that point, the system qualifies as:

> **A minimal living system.**
此时系统才算“最小的生命化系统”。

---

## X. Amendment Policy / 修宪原则

This constitution may evolve.

But any amendment MUST preserve:
- identity continuity,
- lifecycle auditability,
- and explicit recovery semantics.
宪法可演进，但必须保留身份连续、生命周期可审计、恢复语义显式。

Anything less is regression.
否则即为退化。

---

### Final Declaration

P10 marks the moment this project stopped being a demo.

From here on,  
**every line of code is accountable to time.**
自此项目不再是演示，每一行代码都要向时间负责。
