

---

# 📘 **ENVIRONMENT.md**

**ADK · Decade of Agents — Execution Environment Guide**
**运行环境指南（双语）**

---

## 🧭 Overview · 概述

This document defines the **unified execution environment** for all projects in the **adk-decade-of-agents** repository (P01–P50).
To ensure consistent behavior, reproducibility, and evolutionary continuity across Sessions, Memory, Persona, Preference, Router, and Tooling projects, **all environment settings are centralized here**.

本文件定义了整个 `adk-decade-of-agents` 仓库所有项目（P01–P50）的**统一运行环境**。
为了保证 Session、Memory、Persona、Preference、Router、Tools 等模块在演化过程中的**一致性、可重复性与连续性**，所有环境配置均在此文件统一维护。

最新说明请访问：
👉 **[https://www.entropycontroltheory.com](https://www.entropycontroltheory.com)**

---

# 1. System Requirements

# 1. 系统要求

* **OS / 操作系统**: macOS / Linux / Windows
* **Python**: Recommended / 推荐使用 **3.11+**
* **Network**: Must access Google Generative AI API
  网络需可访问 Google Generative AI API

---

# 2. Virtual Environment

# 2. 虚拟环境

All ADK projects must use the **same root-level virtual environment**:

所有 ADK 项目必须使用仓库根目录的统一虚拟环境：

```
adk-decade-of-agents/.venv
```

Create / 创建：

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
.\.venv\Scripts\activate         # Windows PowerShell
```

---

# 3. Dependencies

# 3. 依赖安装

All projects share one dependency file:

所有项目共享统一的依赖文件：

```
requirements.txt
```

Install / 安装：

```bash
pip install -r requirements.txt
```

Recommended dependencies include / 推荐依赖包含：

```
google-generativeai>=0.7.0
google-ai-agents>=0.1.0
python-dotenv>=1.0
rich>=13.0
sqlalchemy>=2.0
pydantic>=2.8
httpx>=0.27
```

---

# 4. API Key Configuration

# 4. API Key 配置

Create a root-level `.env` file:

在仓库根目录创建 `.env` 文件：

```
adk-decade-of-agents/.env
```

Content / 内容：

```
GOOGLE_API_KEY=your_api_key_here
```

The `.env` file is ignored by Git, preventing accidental uploads.
`.env` 已加入 `.gitignore` 避免泄露。

---

# 5. ADK Runtime Stack

# 5. ADK 运行时栈

All ADK projects depend on the unified ADK Runtime, including:

所有项目依赖统一的 ADK Runtime，包括：

* **Session Runtime**（事件与上下文管理）
* **Event Ledger & Event Compaction**（事件账本与压缩）
* **Memory Store**（长期记忆库）
* **Structured State**（结构化工作记忆）
* **Runners: InMemoryRunner / SQLiteRunner**（多 Runner 支持）
* **Tools / Tool Execution**
* **Persona Injection & Preference Models**（人格与偏好)
* **Router / Strategy Dispatch**（路由器）
* **Observability: logs, traces, metrics**（可观测性）

Install ADK:

```bash
pip install -U google-ai-agents
```

---

# 6. Running a Project

# 6. 运行单个项目

Each project follows the same structure:

每个项目遵循相同目录结构：

```
projects/p18-preference-extraction/
    src/main.py
```

Run:

```bash
cd projects/pXX-some-project
python src/main.py
```

---

# 7. Shared Global Data Structures

# 7. 全局共享数据结构

All ADK projects evolve through the same system-level structures:

所有 ADK 项目共享并共同演化以下结构：

### Short-term Memory

* `session.events` —— 会话事件账本

### Working Memory

* `session.state` —— Agent 工作记忆（结构化）

### Long-term Memory

* `memory_store.json` —— 长期存储的人格、偏好、配置等

### Additional Global Structures

* Persona Cards
* Preference Models
* Router Strategy Config

这些结构在整个 P01–P50 项目链中持续演化，保持智能体的“代际连续性”。

---

# 8. Notes · 补充说明

* Environment setup will **not** be repeated inside individual project folders.
  单个项目中**不再重复**环境配置说明。
* Any updates to the environment will be made **only in this file**.
  所有环境更新将**统一集中在本文件**维护。
* For the latest documentation:
  👉 **[https://www.entropycontroltheory.com](https://www.entropycontroltheory.com)**

---

