# Canonical World Memory Store (v0)  
# 世界记忆存储规范（v0）

## 1. Purpose 目的
- Define the minimal canonical shape of world memory: containers and responsibility boundaries, not content fields.  
- 界定世界记忆的最小规范形状：关注容器与责任边界，而非具体字段。

## 2. Mandatory Top-Level Concepts 顶层必备概念
- Store Version 存储版本：识别存储结构本身的版本。  
- Current Schema Version 当前架构版本：标识运行时的理解世代。  
- Memory Zones 记忆分区：四个责任分区的容器。  
- Legacy Container 遗留容器：显式隔离、只读的历史记忆。  
- Minimal Provenance Indicator 最低来源标识：可接受的最小溯源等级。

## 3. Canonical Responsibility Shape (Conceptual) 责任结构（概念）
- Distinguish World State / Decision / Observation. 区分世界状态/决策/观察。  
- Distinguish current generation vs legacy generation. 区分当前世代与遗留世代。  
- Distinguish active memory vs historical memory. 区分活跃记忆与历史记忆。  
Exact serialization is implementation-defined, but zone boundaries and version visibility are mandatory.  
具体序列化由实现决定，但分区边界与版本可见性不可缺省。

## 4. Provenance (Minimal Requirement) 最低溯源要求
- World State must indicate at least one: user-declared, tool-verified, or human-approved.  
- 世界状态至少注明：用户声明、工具验证或人工确认之一。  
- Absence of provenance disqualifies World State writes. 无溯源则不得写入世界状态。

## 5. Forbidden Practices 禁止事项
- Mixing zones in the same container. 不得在同一容器混合分区。  
- Writing to legacy memory. 不得写入遗留记忆。  
- Omitting `schema_version`. 不得省略 `schema_version`。  
- Inferring zone from content. 不得根据内容推断分区。  
- Auto-upgrading old memory without audit. 不得无审计自动升级旧记忆。

## 6. Canonical Principle 根本原则
- If memory cannot be migrated, it must at least be preserved.  
- 若无法迁移，至少应被保留。
