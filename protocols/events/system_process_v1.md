# System Process Events v1 (P10)  
# 系统进程事件 v1（P10）

## Envelope / 信封
- JSONL, append-only. | JSONL 追加写入。  
- Fields 字段: `ts` (ISO-8601 UTC), `event_type`, `session_id`, `payload`.

## Event Types / 事件类型
- `system.boot`  
  - payload: `system_id`, `process_id`, `run_id`, `boot_mode`, `started_at`, `recovered_from_run_id`  
  - 负载字段：`system_id`、`process_id`、`run_id`、`boot_mode`、`started_at`、`recovered_from_run_id`
- `system.shutdown`  
  - payload: `system_id`, `process_id`, `run_id`, `exit_reason`  
  - 负载字段：`system_id`、`process_id`、`run_id`、`exit_reason`

## boot_mode Semantics / boot_mode 语义
- `cold`: no prior store; first boot. | 无历史存储，首次启动。  
- `warm`: clean shutdown previously recorded. | 曾有干净的关机记录。  
- `recover`: prior boot without matching shutdown. | 之前启动未记录关机，需恢复。

## Invariants / 不变式
- Every `run_id` SHOULD have exactly one `system.boot`. | 每个 `run_id` 应有且仅有一个 `system.boot`。  
- Every `run_id` MUST have at most one `system.shutdown`. | 每个 `run_id` 至多一个 `system.shutdown`。  
- A run without `system.shutdown` is incomplete and triggers `recover` on the next boot. | 缺少 `system.shutdown` 的运行视为不完整，下一次启动触发 `recover`。
