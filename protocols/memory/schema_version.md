# Schema Version — Temporal Generation Contract  
# 架构版本 —— 跨时代的契约

## 1. Definition 定义
- `schema_version` identifies the generation of world understanding under which a memory entry was created.  
- It is a temporal contract, not just a technical label.  
`schema_version` 表示记忆条目创建时所属的世界理解“世代”。这是时间上的契约，而不仅是技术标签。

## 2. Core Commitments 核心承诺
- Every memory entry must declare `schema_version`.  
- Writes are allowed only under the current `schema_version`.  
- The system prefers refusal over temporal inconsistency.  
每条记忆必须声明 `schema_version`；仅允许在当前版本下写入；系统宁可拒绝也不接受时间上的不一致。

## 3. Runtime Obligations 运行时义务
- At startup, the runtime must confront memory versioning before any session.  
- The system must be able to state:  
  - Which schema version it supports  
  - Which version stored memory belongs to  
  - Whether legacy memory exists  
- Silent compatibility is forbidden.  
启动时先处理版本；系统必须声明支持的版本、存储的版本、是否存在遗留记忆；禁止静默兼容。

## 4. Evolution Rule 演进规则
- Upgrades may expand understanding and reinterpret future behavior.  
- They must not deny past understanding.  
- A system may grow wiser, but must never pretend it was always so.  
升级可以拓展理解、影响未来行为，但不得否认历史理解。系统可以变得更聪明，但不能假装一直如此。
