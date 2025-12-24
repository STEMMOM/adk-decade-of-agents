# Memory Schema Migration (p08) — Plan & Checklist  
# 记忆架构迁移（p08）—— 计划与检查清单

## Purpose 目的
- Migrate world memory to newer schema versions without losing responsibility guarantees.  
- 在迁移到新版架构时，保持责任约束与可审计性。

## Scope 范围
- Applies to `runtime_data/memory_store.json` and zoned memory containers.  
- 适用于 `runtime_data/memory_store.json` 及分区记忆。

## Principles 原则
- Audit-first: every migration step is logged. 审计优先，迁移步骤必须记录。  
- No silent upgrades: version changes are explicit. 禁止静默升级，版本变更需显式执行。  
- Preserve legacy: on failure, keep legacy data read-only. 失败时保留只读遗留数据。

## Migration Steps 迁移步骤
1. Inventory: detect current `schema_version` and legacy zones.  
   清点：检测当前 `schema_version` 与遗留分区。  
2. Plan: map source zones/keys to target schema fields.  
   规划：映射源分区/键到目标架构字段。  
3. Execute: transform with checksums and backups.  
   执行：携带校验和与备份进行转换。  
4. Validate: verify zone separation, provenance, and version tags.  
   验证：确认分区隔离、溯源与版本标记。  
5. Commit: write new store; retain legacy snapshot for audit.  
   提交：写入新存储，并保留遗留快照以供审计。

## Validation Checklist 验证清单
- `schema_version` updated and declared. `schema_version` 已更新并声明。  
- Zones intact: World / Decision / Observation / Legacy separated. 分区完好：世界/决策/观察/遗留清晰分隔。  
- Provenance preserved or upgraded; none lost. 溯源保留或升级，无丢失。  
- Events emitted for proposal / check / commit (P07 path). 已记录事件：提案/检查/提交（P07 流程）。  
- Legacy snapshot stored read-only. 遗留快照已只读存档。
