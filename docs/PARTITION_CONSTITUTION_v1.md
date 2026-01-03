

`docs/PARTITION_CONSTITUTION_v1.md`

（我默认选择：**tools/**；history 采用 **方案 1：`runtime_data/history/` 子域**；并保留你现有的 `adk_runtime/` 作为 kernel zone。）

---

# Partition Constitution v1.0

**Repository:** `adk-decade-of-agents`
**Status:** Adoptable (v1)
**Scope:** Root partitions, placement law, governance/history/tools integration, enforcement

---

## Preamble

本仓库不是“代码集合”，而是一个可在十年后解释的**制度化系统体**。
因此分区（partition）不是美学问题，而是以下能力的根基：

* **可审计**（auditability）：任何产物可解释其来源、归属与变更路径
* **可重放**（replayability）：关键过程可在新环境中复现结论
* **可演化**（evolvability）：演进切片清晰、可升格、可回滚
* **可治理**（governability）：规则可执行、违规可检测、修订可追溯

本宪法规定：**任何产物必须有合法归属区**；任何新增分区必须通过制度化变更流程；任何跨区流动必须可追溯；任何执行主体（如 RRB）不得越权自证合法性。

---

## Article 1 — Root Sovereignty

### 1.1 Root 仅允许承载“宪法层入口”

Root 是宪法空间：只允许**入口、协议、分区容器、治理机构、回归执法机关**存在。

**Root Allowed Set（一级目录白名单）**

* `adk_runtime/` — Kernel Zone（薄内核：稳定库/Runtime 能力）
* `protocols/` — Sovereign Contract Zone（协议/红线/版本化 schema）
* `projects/` — Evolution Zone（演进切片：P00–PXX）
* `runtime_data/` — Evidence Zone（运行证据链：append-only 事实材料）
* `tests/` — Enforcement Zone（回归与不变量：宪法执法机关）
* `scripts/` — Maintenance Scripts（维护/迁移脚本：非稳定 API）
* `docs/` — Documentation Zone（宪法、规范、日志、白皮书）
* `modules/` — Curriculum Zone（结构化模块：m01–mXX）
* `assets/` — Static Artifacts（图片/图表等静态资源）
* `examples/` — Examples Only（示例模板，不含私有实例）
* `governance/` — Governance Zone（政策包、override 宪章、review loop）
* `tools/` — Capability Tools（可插拔执行器：RRB 等）
* `.github/` — CI & templates（可选）

**Root Files Allowed**

* `README.md`, `REGRESSION.md`, `LICENSE`, `.gitignore`, `.gitattributes`
* `pytest.ini`
* `requirements.txt` / `pyproject.toml`
* `PROJECTS.md`（允许但不鼓励；建议迁入 `docs/`）

### 1.2 Root Forbidden Set（根目录禁止项）

Root 禁止出现任何“运行产物 / 临时物 / 实例态配置 / 个人碎片笔记”：

* `*.jsonl`, `*.log`, `*.db`, `*.sqlite`, `*.tmp`, `*.bak`
* `.env`（只允许 `.env.example`）
* `persona.json`, `memory_store.json` 等实例态文件
* `notebooks/`（如需存在，必须归档进 `docs/notebooks/` 或 `research/`）

> Root 的功能是“识别系统”，不是“收纳系统”。

---

## Article 2 — Partition Definitions and Boundaries

每个分区必须满足：**存在理由、边界、禁止项、进入/退出机制**。
以下分区构成当前仓库的“制度器官”。

### 2.1 `adk_runtime/` — Kernel Zone (Thin Kernel)

**Purpose**：稳定、复用、跨项目的 runtime 能力与可测试模块。
**Allowed**：纯库代码、协议实现、稳定工具类、可测试组件。
**Forbidden**：运行数据、一次性实验、个人配置、项目 demo。
**Stability**：默认高稳定；breaking change 必须附迁移说明与回归更新。

### 2.2 `protocols/` — Sovereign Contract Zone

**Purpose**：协议、红线、schema、版本化契约。
**Allowed**：`v1/ v2/` 版本结构、schema、规范、示例（example）。
**Forbidden**：实现代码、运行数据、随笔。
**Rule**：协议变更必须可对比、可解释，并作为 replay/治理引用的版本依据。

### 2.3 `projects/` — Evolution Zone

**Purpose**：以 P00–PXX 形式记录系统演进与实验切片。
**Allowed**：可运行 demo、实验、阶段性实现、项目级 README。
**Forbidden**：长期稳定库（应升格到 `adk_runtime/` 或 `tools/`）、运行产物（应进 `runtime_data/`）。
**Rule**：每个项目必须声明：

* Inputs（输入/依赖）
* Outputs（产物/写入点）
* How to run（运行方法）
* Dependencies（对 `protocols/` / `adk_runtime/` / `tools/` 的依赖）

### 2.4 `runtime_data/` — Evidence Zone (Append-only)

**Purpose**：系统在时间中产生的证据链与 replay 基准（事实材料）。
**Allowed**：jsonl ledger、replay plan/report、baseline、registry、logs、db（可分层）。
**Forbidden**：源代码、无 schema 的散乱文件。
**Rule**：

* 任何可重放产物必须可指向其来源（`request_hash` / `policy_version` / `schema_version` / `replay_plan_id`）
* 允许备份与 corrupt 文件，但必须遵循命名规则（含 timestamp）

#### 2.4.1 `runtime_data/history/` — Institutional History Subzone (Append-only)

**Purpose**：制度事实历史（不可篡改的条目集合）。
**Canonical Ledgers（建议标准化）**：

* `release_intents.jsonl`
* `decision_records.jsonl`
* `overrides.jsonl`
* `amendments.jsonl`
* `executions.jsonl`
  **Rule**：history 子域只追加不覆盖；任何“改判/override”只能追加更高权威事实条目。

### 2.5 `tests/` — Enforcement Zone (Regression & Invariants)

**Purpose**：保证宪法与分区规则长期不被破坏。
**Rule**：

* 必须包含 repo hygiene tests（目录/文件落位、禁止项检测）
* 必须包含 replay regression tests（关键证据链可回放）
* 测试失败视为“制度违规”，不得以口头解释放行

### 2.6 `scripts/` — Maintenance Scripts Zone

**Purpose**：迁移器、导出器、格式化、维护脚本（快速迭代、非稳定 API）。
**Forbidden**：不可追溯的破坏性修改脚本、长期业务逻辑。
**Rule**：脚本若写入 `runtime_data/`，必须写入结构化路径，并输出 manifest/summary（可被审计）。

### 2.7 `docs/` — Documentation Zone

**Purpose**：长期叙事、制度文档、开发日志、规格说明。
**Rule**：docs 允许 `inbox/ drafts/`，但必须位于 `docs/` 子目录内，不污染 root；docs 不得承载运行证据（jsonl/db/log）。

### 2.8 `modules/` — Curriculum Zone

**Purpose**：模块化学习/能力进阶（m01–mXX），不等价于 projects。
**Forbidden**：运行数据、实验碎片、临时脚本、数据库。
**Rule**：每个 module 必须自带 README，说明目标与与 projects 的映射关系。

### 2.9 `assets/` / `examples/`

* `assets/`：仅静态资源（图、封面、示意图）
* `examples/`：仅示例模板（`*.example.*`），不得包含私有实例态配置

### 2.10 `governance/` — Governance Zone (Court + Policy Bundles)

**Purpose**：治理制度与政策包：决定“应不应该”，不负责“执行”。
**Allowed**：

* policy bundles（例如 `governance/policies/<name>-v0/`）
* override constitution / risk acceptance templates
* review loops（override 触发修订机制）
  **Forbidden**：运行产生的 ledger（那在 `runtime_data/history/`）、bot 实现代码（那在 `tools/`）。
  **Rule**：governance 引用 `protocols/` 的版本；任何治理变更必须能被 replay 解释。

### 2.11 `tools/` — Capability Tools Zone (Executors)

**Purpose**：可插拔执行器/能力组件（如 Repo Release Bot / replay tooling）。
**Allowed**：

* `tools/rrb/`（Repo Release Bot）
* `tools/replay/`（若从 scripts 升格）
* `tools/inspect/`（registry/inspector）
  **Forbidden**：policy bundles（在 governance）、evidence ledgers（在 runtime_data/history）、随手脚本（在 scripts）。
  **Hard Rule（越权禁止）**：tools 不得自证合法性；必须：

1. 读取 governance 的 policy bundle（依据 protocols 版本）
2. 输出 decision / intent / execution 记录到 `runtime_data/history/`（append-only）

---

## Article 3 — Data Placement Law（数据落位法）

### 3.1 运行数据一律归 `runtime_data/`

以下类型不得出现在 root 或 `projects/`：

* 数据库文件（`.db`, `.sqlite`）
* 日志（`.log`）
* ledger（`.jsonl`）
* replay 报告（`.json` / `.diff.json` 等）

### 3.2 实例态配置必须区分：示例 vs 本地

* 示例：`examples/*.example.*`（可提交）
* 本地：`runtime_data/local/`（默认 gitignore）
* 任何“默认配置”若需提交，应以 `*.default.*` 形式进入 `adk_runtime/`（或 tools 内的 config）

### 3.3 命名规则（强制）

* 证据链文件必须携带可追溯标识：`schema_version` 或 `policy_version` 或 `replay_plan_id` 或 `request_hash`
* 备份/损坏文件必须含 timestamp：`*.corrupt.YYYYMMDD-HHMMSS` / `*.bak.YYYYMMDD-HHMMSS`

---

## Article 4 — Cross-Zone Promotion（跨区升格法）

当某项目产物达到稳定复用标准时，必须“升格”（promotion），并留下迁移痕迹。

**Promotion Path**

* `projects/` → `adk_runtime/`（库化：稳定 API）
* `projects/` → `tools/`（能力化：可执行组件）
* `projects/` → `protocols/`（契约化：schema/红线/规范）
* `projects/` → `docs/`（叙事化：说明与决策记录）
* `projects/` → `runtime_data/`（证据化：baseline / replay / ledger）

**Promotion Trigger**

* 被 ≥2 个项目复用
* 需要稳定 API
* 需要长期 replay 依据

**Promotion Must Include**

* 迁移记录（what moved, why）
* 回归用例更新（tests）

---

## Article 5 — Partition Change Governance（分区变更治理）

### 5.1 新增一级目录门槛

新增一级目录必须同时满足：

* 明确目的（1 句话）
* 边界与禁止项（至少 3 条）
* 与现有分区不重叠的对照说明
* 增加 repo hygiene test 覆盖（否则视为不合规）

### 5.2 宪法修订机制

* 宪法变更必须以 PR 提交
* 必须更新：`docs/PROJECT_STRUCTURE_v0.1.md` 或 `docs/REPO_LAYOUT.md`
* 必须更新相应执法测试：`tests/test_repo_hygiene.py`

---

## Article 6 — Enforcement（执行）

### 6.1 强制执行点

* `tests/test_repo_hygiene.py`：root 白名单 + 禁止项扫描 + 分区落位检查
* CI（可选但建议）：每次 PR 必跑 `pytest -q`
* RRB / replay：依赖本宪法判定“结构合法性”，并把裁决写入 `runtime_data/history/`

### 6.2 违规处理

* 违规文件必须迁移到正确分区或加入 `.gitignore`
* 不允许通过“解释”绕过规则（解释只能导致“修宪”，不能直接放行）

---

## Appendix A — Minimal Repo Hygiene Ruleset（可直接转成测试）

* root 目录名必须 ∈ Root Allowed Set
* root 不允许出现：`*.db`, `*.log`, `*.jsonl`, `.env`
* `projects/` 下不允许出现：`*.db`, `*.log`, `*.jsonl` 等运行产物
* `runtime_data/` 允许：`.jsonl/.json/.diff.json/.bak/.corrupt.*`
* `examples/` 下允许：`*.example.*`；禁止出现私有实例（如 `persona.json` 无 example 标识）
* `governance/policies/` 下 policy 必须版本化命名（如 `*-v0`, `*-v1`）

---

## Immediate Adoption Steps（立刻落地）

1. 保存本文件：`docs/PARTITION_CONSTITUTION_v1.md`
2. 在 `docs/PROJECT_STRUCTURE_v0.1.md` 顶部加入一句：
   **“本宪法为分区最高约束，任何目录/数据落位以此为准。”**
3. 更新执法：增强 `tests/test_repo_hygiene.py` 覆盖 Appendix A

---

如果你现在就要“能用 + 能执法”，下一步我建议你直接把 **现有** `tests/test_repo_hygiene.py` 贴出来——我会把它改成严格符合本宪法的版本（root 白名单、后缀禁令、projects 禁止运行产物、examples/example 规则、governance/policies 版本规则、history 子域要求）。
