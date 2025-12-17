from google import genai
from event_ledger import Session
import json


class MinimalAgent:
    def __init__(self, name: str, instructions: str, model: str = "gemini-2.0-flash"):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.client = genai.Client()

    def ask_gemini(self, prompt: str) -> str:
        resp = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
        )
        return resp.text

    def run_once(self, user_message: str, session: Session) -> str:
        # Log user message
        session.ledger.add("user_message", content=user_message)

        # Prepare system prompt
        prompt = f"{self.instructions}\n\nUser: {user_message}"

        # Log tool call
        session.ledger.add("tool_call", tool="ask_gemini", prompt=prompt)

        # Execute tool
        try:
            output = self.ask_gemini(prompt)
            session.ledger.add("tool_result", result=output)
        except Exception as e:
            session.ledger.add("error", message=str(e))
            raise e

        # Log final output
        session.ledger.add("final_output", content=output)

        return output


def main():
    print("[P02] Stateful Sessions & Event Ledger Demo")

    agent = MinimalAgent(
        name="root_agent",
        instructions="You are a minimal agent cell with an event ledger.",
    )

    # Create a session for this run
    session = Session(agent)
    print("Session ID:", session.session_id)

    user_question = "Give me a 1-sentence summary of this week's AI news."

    answer = agent.run_once(user_question, session)
    print("\nAgent:", answer)

    print("\n--- Event Ledger ---")
    print(json.dumps(session.ledger.dump(), indent=2))


if __name__ == "__main__":
    main()
