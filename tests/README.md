# System Identity & Observability Tests  
# 系统身份与可观测性测试

This directory contains protocol-level tests that act as constitutional guards for a long-lived agent system. | 本目录包含协议级测试，作为长寿命系统的“宪法守卫”。

## Test Groups 测试分组

### 1. Runtime Observability Invariants / 运行时可观测性不变量
- File 文件: `test_observability_run_id_invariant.py`  
- Purpose 目的: ensure runtime observability never writes `run_id=null` or `run_id="unknown"` (latest run enforced). | 确保运行时可观测性不写入 `run_id=null` 或 `run_id="unknown"`（针对最新运行）。
- Boundary 边界: runtime write path (`observability.log_event`). | 运行时写路径。

### 2. Export Boundary Invariants (P09) / 导出边界不变量
- File 文件: `test_obs_export_p09_invariants.py`  
- Purpose 目的: exported P09 observability must use system run ids (`run_...`), never legacy `p00-...`/`unknown`; `tool_call_*` must keep `session_id`. | 导出的 P09 可观测性必须使用系统 run_id（`run_...`），不得出现 `p00-...`/`unknown`；`tool_call_*` 保留 `session_id`。
- Boundary 边界: exporter (`obs_export_p09.py`). | 导出器。

### 3. Smoke Tests (Transitional) / 过渡期冒烟测试
- File 文件: `test_p09_observability_smoke.py`  
- Purpose 目的: high-level sanity for P09 observability pipeline; transitional. | P09 可观测性管线的高层 sanity 检查，属于过渡期测试。
- Status 状态: to be absorbed into explicit invariants over time. | 后续将并入显式不变量测试。

## Design Philosophy 设计理念
- Runtime invariants protect the system while alive. | 运行时不变量保障活体系统。  
- Export invariants protect data once it leaves runtime. | 导出不变量保障离线数据。  
- Smoke tests warn early but are not authoritative. | 冒烟测试早期预警但非权威。  
- Identity semantics are enforced by invariants, not convention. | 身份语义由不变量强制，而非约定。
