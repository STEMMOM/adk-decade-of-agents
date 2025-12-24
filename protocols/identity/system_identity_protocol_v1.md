

---

# System Identity Protocol v1.0 / 系统身份与时间轴标识协议

Version 版本: 1.0  
Status 状态: Canonical  
Scope 范围: AI-Native Long-Term System  
Last Updated 最后更新: 2025-12-23

---

## 0. Purpose / 协议目的
- Define semantics, generation boundaries, and usage rules for all IDs. | 严格定义所有 ID 的语义、生成边界与使用规则。  
- Prevent timeline mixing; ensure auditability, replayability, governability. | 防止时间轴混淆，确保可审计、可回放、可治理。  
- “Did the system live?” must be answerable in engineering and philosophical terms. | “系统是否活过”需有工程与哲学上的确定性。  
- Any new ID must be registered here, otherwise it is illegal. | 任何新增 ID 必须登记，否则视为非法。

---

## 1. Canonical Taxonomy / ID 分层
- Five layers by existence level. | 按存在层级分五类。  
| Layer 层级 | ID 类型 | 核心问题 |
| --- | --- | --- |
| System | `system_id` | Which system? 是哪个系统？ |
| Process | `process_id` | Which process instance? 这次进程实例？ |
| Life | `run_id` | Did this run live? 系统这次活过吗？ |
| Session | `session_id` | Which session/interaction? 哪段交互/会话？ |
| Trace | `trace_id` / `span_id` | How did this execution flow? 执行链路？ |

---

## 2. `system_id`
- Definition: permanent identity of a logical system. | 逻辑系统的永久身份标识。  
- Scope: AI-Native OS instance; long-lived, upgradable, migratable. | 标识 AI-Native OS 实例，长期存在、可升级、可迁移。  
- Generation: by init/installation; first creation only. | 系统初始化/安装时生成，仅首次创建。  
- Example: `sys_095be687ecfa4442861b529af562ca6e`  
- Lifecycle: across processes, runs, reboots, upgrades. | 跨进程、跨 run、跨重启、跨升级。  
- Immutable rules: not generated at runtime; not per-run; not observability primary key. | 不可在运行时生成；不可区分单次运行；不可作为可观测性主键。

---

## 3. `process_id`
- Definition: identifies an OS-level process instance. | 操作系统层面的进程实例标识。  
- Question: which process start is this code running under? | 回答“当前代码属于哪次进程启动？”  
- Generation: OS/runtime boot; every process start. | 每次进程启动生成。  
- Example: `proc_f345dc8655674081906b753c2894163d`  
- Lifecycle: from process start to exit; may span multiple runs (edge). | 从进程启动到退出，极端可跨多个 run。  
- Boundaries: for crash/restart/recover diagnosis; not a life axis; not the sole join key. | 用于崩溃/重启/恢复诊断；不是生命轴；不得作为唯一关联键。

---

## 4. `run_id` — Core Life ID / 系统生命主键
- Definition: marks one complete life interval: `system.boot → system.shutdown`. | 标识一次完整生命区间：`system.boot → system.shutdown`。  
- Generation: by `system.boot` at responsibility start. | 在系统开始承担责任时由 `system.boot` 生成。  
- Example: `run_6e678cc83933485c83dc9462ad75ab58`  
- Semantics: run_id ≠ session/request/trace; primary key of system life. | 不等于 session/request/trace；系统生命主键。  
- Rules: not null; not reused by sessions/apps; not forged by observability; must be findable in `events.jsonl` with `system.boot`. | 不得为 null；不得被会话/应用复用；不得被可观测性伪造；必须在 `events.jsonl` 中找到对应 `system.boot`。

---

## 5. `session_id`
- Definition: interaction session for user/agent. | 用户或 agent 的交互会话标识。  
- Question: which dialogue/interaction is this? | 回答“哪一段对话/交互？”  
- Generation: app/agent runtime at session start. | 会话开始时生成。  
- Example: `p00-26f7f906-bad1-49a7-8ba6-8239f2a2c1b8`  
- Lifecycle: shorter than run; a run may include multiple sessions. | 通常短于 run；一个 run 可含多个 session。  
- Rules: never name it `run_id`; recommended field names `session_id`/`app_session_id`/`conversation_id`. | 不得命名为 `run_id`；推荐字段名如 `session_id` 等。

---

## 6. `trace_id`
- Definition: logical execution chain ID. | 逻辑执行链标识。  
- Question: how did this request/inference/tool call flow? | 回答“请求/推理/工具调用如何流转？”  
- Generation: runtime tracing system. | 由追踪系统生成。  
- Example: `26da9463-a50d-4b49-b8e1-abff066dfe76`  
- Traits: high concurrency/count, short-lived. | 高并发、高数量、短生命周期。  
- Rules: not a system identity; not a responsibility anchor; only for debugging/perf. | 不作为系统身份或责任锚，只用于调试/性能。

---

## 7. `span_id`
- Definition: node within a trace (tool.call, agent.reply, policy.check, memory.write). | trace 内部节点（如 tool.call 等）。  
- Usage: must attach to a trace_id; cannot exist alone. | 必须附属 trace_id，不可单独存在。

---

## 8. Canonical Join Order / ID 使用优先级
跨数据源关联必须遵循：  
```
run_id
  → process_id
    → session_id
      → trace_id
        → span_id
```
Any skip-level join is unsafe. | 任何跳级关联均视为不安全。

---

## 9. Observability Clauses / 可观测性条款
- Observability must carry `run_id`; missing run_id must be explicitly reasoned and is a defect. | 可观测性必须携带 `run_id`；缺失必须说明原因，视为缺陷。  
- Observability must not generate or override run_id. | 可观测性不得生成或覆盖 run_id。

---

## 10. Red Lines / 禁止事项
- ❌ Use run_id to mean session. | 禁止用 run_id 表示 session。  
- ❌ Use trace_id to mean system life. | 禁止用 trace_id 表示系统生命。  
- ❌ Allow run_id to be null. | 禁止 run_id 为 null。  
- ❌ Reuse run_id across systems. | 禁止跨系统复用 run_id。

---

## 11. Authority / 协议地位
This is the highest source of interpretation for system identity and timelines; all runtime/agent/observability/memory/ledger modules must comply. | 本协议为系统身份与时间轴的最高解释源，所有模块必须遵守。

---
