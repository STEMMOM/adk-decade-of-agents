# Memory Schema v0 — World Memory Responsibility Zones  
记忆架构 v0 —— 世界记忆责任分区

## 1. Purpose 目的
Defines the minimum responsibility structure for long-running world memory. Any memory without a declared zone and schema version is invalid.  
定义长生命周期世界记忆的最小责任结构。未声明分区和版本的记忆视为无效。

## 2. Core Principle 核心原则
- Memory is a time responsibility contract, not just storage.  
- Each entry must belong to exactly one zone.  
- Zones cannot be mixed, inferred, or auto-upgraded.  
记忆是时间责任契约，而非存储；每条记忆必须且只能属于一个分区；分区不可混用、推断或自动升级。

## 3. Four Memory Zones 四个记忆分区

### I. World State Memory（世界状态记忆）
- Definition 定义: States treated as true at a given time. 系统确认的真实世界状态。  
- Temporal Responsibility 时间责任: Cross-generation required; not modifiable except migration/supersession. 跨代保留；仅迁移/替换可改。  
- Constraints 约束: Low-frequency, high-confidence; minimal provenance; no speculation. 低频高可信，最小溯源，无推测。  
- Responsibility 责任: Writing here accepts long-term accountability. 写入即承担长期责任。

### II. Decision & Action Record（决策与行动记录）
- Definition 定义: Decisions and resulting actions. 系统决策及执行记录。  
- Temporal Responsibility 时间责任: Cross-generation required; append-only; not reused for new decisions. 跨代保留、仅追加，不用于新决策。  
- Constraints 约束: May be wrong but never denied or rewritten. 可错但不可否认或改写。

### III. Observational / Ephemeral Memory（观察 / 短期记忆）
- Definition 定义: Observations, hypotheses, intermediate judgments. 观察、假设、中间判断。  
- Temporal Responsibility 时间责任: Cross-generation optional; modifiable. 跨代可选，可修改。  
- Constraints 约束: Not treated as fact; cannot auto-promote to World State; may expire/compress. 不作事实，不可自动晋升，可过期/压缩。  
- Integrity 完整性: Can be forgotten but not pretended nonexistent. 可遗忘但不可假装未曾存在。

### IV. Legacy / Historical Memory（遗留 / 历史记忆）
- Definition 定义: Data from older schemas or deprecated semantics. 旧版本或废弃语义下的记忆。  
- Temporal Responsibility 时间责任: Preserved; read-only; no decision participation. 保留、只读，不参与决策。  
- Constraints 约束: Access only via explicit migration or historical inspection. 仅迁移或历史审查可用。

## 4. Zone Integrity Rules 分区完整性规则
- Every entry must declare its zone. 每条记忆必须声明分区。  
- Cross-zone promotion is explicit only. 分区间提升必须显式进行。  
- Schema evolution must not reduce historical responsibility. 架构演进不得降低历史责任。  
- Legacy memory is preserved by default. 遗留记忆默认保留。

## 5. Minimal Validity Requirement 最小有效性要求
Schema v0 is active when:  
- All entries are zoned. 所有记忆已分区。  
- Legacy memory is separated. 遗留记忆独立。  
- World State is treated as high-responsibility data. 世界状态视为高责任数据。  
- Observations cannot silently become facts. 观察不得悄然变成事实。
