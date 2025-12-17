


## 🧠 三、`projects/p01-minimal-agent/src/main.py`

from google import genai


class MinimalAgent:
    """
    P01: 最小 Agent 细胞

    这里只做三件事：
    1. 持有一个系统说明（instructions）
    2. 接收用户问题
    3. 调用一个“工具”（这里是 ask_gemini），并返回回答
    """

    def __init__(self, name: str, instructions: str, model: str = "gemini-2.0-flash"):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.client = genai.Client()

    def ask_gemini(self, user_question: str) -> str:
        """
        作为 P01 的“工具函数（Tool）”：
        目前只是直接调用模型，后续可以替换为：
        - 带 Search 的模型
        - 带 Tool 调用的 Agent
        """
        prompt = (
            f"{self.instructions}\n\n"
            f"User question: {user_question}\n\n"
            "Answer in a concise way."
        )

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return resp.text

    def run_once(self, user_question: str) -> str:
        """
        最小 Runner：执行一次 Agent–Tool 调用链。
        后续 P02 开始，这里会被真正的 Runner + Session 替换/扩展。
        """
        return self.ask_gemini(user_question)


def main():
    print("[P01] Minimal Agent Cell Demo")

    # 1. 定义一个最小 Agent
    agent = MinimalAgent(
        name="root_agent",
        instructions=(
            "You are a minimal AI agent cell. "
            "Your job is to answer the user's question clearly and briefly. "
            "This is a health-check and structure-check run, not a production system."
        ),
    )

    # 2. 定义一个“真实世界问题”
    user_question = "What happened in AI this week? Please summarize briefly."

    print("User:", user_question)

    # 3. 通过最小 Runner 执行一次调用链
    try:
        answer = agent.run_once(user_question)
    except Exception as e:
        print("\n[ERROR] Agent failed to run:")
        print(repr(e))
        return

    # 4. 输出结果
    print("\nAgent:")
    print(answer)


if __name__ == "__main__":
    main()
