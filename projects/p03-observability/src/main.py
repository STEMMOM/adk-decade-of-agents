from google import genai
from observer import Observer
import uuid
import json


# ------------------------------------------------------------
# Minimal Agent (same as P01/P02, but extended with observer)
# ------------------------------------------------------------
class MinimalAgent:
    def __init__(self, name: str, instructions: str, model: str = "gemini-2.0-flash"):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.client = genai.Client()


    def ask_gemini(self, prompt: str, observer: Observer):
        observer.trace(2, "Calling Gemini model")
        observer.inc("tool_calls")

        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return resp.text


    def run_once(self, user_message: str, observer: Observer):
        observer.trace(1, "Received user message")
        observer.log(f"User: {user_message}")

        prompt = f"{self.instructions}\n\nUser: {user_message}"

        try:
            output = self.ask_gemini(prompt, observer)
            observer.log("Model returned successfully")
        except Exception as e:
            observer.log(f"Error: {str(e)}")
            observer.inc("errors")
            raise e

        observer.trace(3, "Returning final output")
        observer.log(f"Agent Output: {output}")

        return output


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------
def main():
    print("[P03] Observability Demo\n")

    observer = Observer()

    agent = MinimalAgent(
        name="root_agent",
        instructions="You are a minimal agent with observability.",
    )

    question = "Give me a one-sentence summary of this week's AI news."

    answer = agent.run_once(question, observer)

    print("\n--- FINAL OUTPUT ---")
    print(answer)

    print("\n--- OBSERVABILITY REPORT ---")
    print(json.dumps(observer.dump(), indent=2))


if __name__ == "__main__":
    main()
