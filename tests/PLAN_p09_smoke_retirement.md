# Plan: Retire / Split `test_p09_observability_smoke.py`  
# 计划：拆分并淘汰 `test_p09_observability_smoke.py`

Status 状态: Draft / Actionable  
Owner 负责人: tests maintainers  
Goal 目标: 用显式不变量测试替代 legacy 冒烟测试，全面对齐《System Identity Protocol v1.0》。

---

## 0) Why 为什么
- 过去存在 run_id 混用（session vs system run）、exporter 不稳定、boot 身份未贯通。  
- 现在语义已规范：run_id=系统生命轴，session_id=应用会话，exporter 从 events.jsonl 的 boot/shutdown 推导 run，runtime 事件携带 run/system/process/session 顶层。  
- 烟测不再应“兜底”，应被拆分为：  
  - 薄的 pipeline 健康检查，或  
  - 完全退役，由不变量测试覆盖。

## 1) 现有权威测试（已具备）
- Runtime invariant（运行时守卫）: `tests/test_observability_run_id_invariant.py`  
  - 保证最新运行无 run_id=null/unknown，run_id 前缀 run_...；边界：runtime 写入。  
- Export invariant（导出守卫）: `tests/test_obs_export_p09_invariants.py`  
  - 保证导出 P09 仅有 run_... run_id，`tool_call_*` 保留 session_id；边界：exporter。  
- 上述定义了“P09 正确”的含义，smoke 不应重复。

## 2) 拆分策略
### 2.1 从 smoke 中拆出职责
- 典型 smoke 内容：文件存在、导出产出、聚合 JSON、字段存在、run/tool 计数。  
- 划分：  
  - 协议不变量 → 已在 A/B；保持那里。  
  - 管线健康检查 → 可保留薄 smoke。  
  - 指标校验 → 独立“指标契约测试”。

## 3) 目标状态
### 3.1 保留的显式不变量
- ✅ `test_observability_run_id_invariant.py`  
- ✅ `test_obs_export_p09_invariants.py`  
- ⏳ 可选补充：`test_system_identity_invariants.py`（boot/shutdown 配对、system_id 稳定、recover 语义）。

### 3.2 薄 smoke（可选）
- 新文件 `tests/test_p09_pipeline_health.py`：仅跑 exporter & daily aggregator，断言输出文件可生成和解析；不检查身份语义。

### 3.3 指标契约（可选）
- `tests/test_daily_metrics_contract.py`：只检查 daily_metrics_summary schema/必需键、非负数；无身份语义。

## 4) 退役步骤（3 commits）
1. 提取指标检查：新建 `test_daily_metrics_contract.py`，从 smoke 移出 summary 断言，smoke 仍通过。  
2. 删除 smoke 中身份断言；加注释“身份语义由不变量测试保证”。  
3. 重命名或删除 smoke：  
   - 方案 A 推荐：改名 `test_p09_pipeline_health.py`，保留薄烟；删除旧 smoke。  
   - 方案 B：完全删除 smoke，依赖不变量+指标契约。  

## 5) 防止回潮的规则
- Smoke 不得断言协议语义；凡属宪法级语义，必须放入不变量测试。  
- Smoke 允许断言：文件存在、JSON 可解析、脚本能产出。  

## 6) 验收标准
- 身份/run/session 语义仅由不变量测试守卫。  
- 导出正确性由导出不变量守卫。  
- 指标正确性由指标契约守卫（如保留）。  
- 无“兜底式”大而全烟测。

## 7) 推荐最终测试布局
```
tests/
├─ README.md
├─ test_observability_run_id_invariant.py        # runtime identity guard
├─ test_obs_export_p09_invariants.py             # export boundary guard
├─ test_p09_pipeline_health.py                   # (optional) pipeline-only smoke
├─ test_daily_metrics_contract.py                # (optional) metrics schema
└─ test_p08_memory_gate_ci.py
```
