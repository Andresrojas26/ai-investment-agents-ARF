from agents.base_agent import BaseAgent

class ExplainabilityAgent(BaseAgent):
    def __init__(self):
        super().__init__("Explainability Agent")

    def run(self, analysis_result):
        return {
            "fundamentals_weight": 70,
            "sentiment_weight": 30,
            "explanation": (
                "The recommendation is based mostly on strong financial fundamentals "
                "with additional influence from recent news sentiment."
            )
        }