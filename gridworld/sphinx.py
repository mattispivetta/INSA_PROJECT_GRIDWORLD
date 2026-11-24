"""One generated riddle and an in-memory conversation with its player."""
from gridworld.llm_support import GENERATION_PROMPT, JUDGE_PROMPT, llm_json


class Sphinx:
    def __init__(self, ask=llm_json):
        self.ask = ask
        self.riddle = None
        self.history = []

    def get_question(self) -> str:
        """Generate and cache one riddle; return only its public question."""
        if self.riddle is None:
            self.riddle = self.ask(GENERATION_PROMPT, {}, "riddle")
        return self.riddle["question"]

    def answer(self, player_text: str) -> dict:
        """Remember a failed answer and hint, or clear history on success."""
        self.get_question()
        data = {
            "question": self.riddle["question"],
            "expected_answer": self.riddle["expected_answer"],
            "player_answer": player_text,
            "history": self.history,
        }
        result = self.ask(JUDGE_PROMPT, data, "verdict")
        if result["correct"]:
            result["message"] = "Correct!"
            self.history.clear()
        else:
            self.history.append({"answer": player_text, "hint": result["message"]})
        return result
