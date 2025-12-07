# P11 最小有记忆 Agent（InMemory Session） — Minimal Stateful Agent (InMemory Session)

简单演示如何用 ADK + InMemorySessionService 做到“同一会话内记住名字”。  
Simple demo showing how ADK + InMemorySessionService remembers a name within one session.

## 快速开始 — Quick Start

1) 确保已完成 Python 环境与 ADK 安装。  
1) Ensure Python environment and ADK are installed.

2) 运行示例：  
2) Run the demo:
```bash
python src/main.py
```

3) 观察输出：第一次告诉名字，第二次询问自己是谁，模型能复述名字。  
3) Observe output: first tell the name, then ask “who am I?”, the model repeats the name.

## 关键点 — Key Points

- 使用 `InMemorySessionService` 存储对话事件，LLM 本身是无状态的。  
- Use `InMemorySessionService` to store conversation events; the LLM itself is stateless.
- 通过固定 `session_id` 证明同一会话中的记忆。  
- A fixed `session_id` proves memory within the same session.
- 打印 `Session.events` 作为外部短期记忆时间线。  
- Print `Session.events` as the external short‑term memory timeline.

## 文件 — Files

- `src/main.py`：主入口，包含 Runner、Agent、Session 的创建与调用。  
- `src/main.py`: entry point; builds Runner, Agent, Session, and drives the calls.
- `project.card.yaml`：项目元数据，用于生成项目地图。  
- `project.card.yaml`: project metadata for tooling.

## 预期输出 — Expected Output

- CLI 演示：模型在同一 InMemory 会话里记住用户名字。  
- CLI demo: model remembers the user name within the same InMemory session.
- Session Dump：完整事件时间线打印。  
- Session Dump: printed event timeline.
