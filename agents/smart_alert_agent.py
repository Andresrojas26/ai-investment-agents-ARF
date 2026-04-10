from agents.base_agent import BaseAgent

class SmartAlertAgent(BaseAgent):
    def __init__(self):
        super().__init__("Smart Alert Agent")

    def run(self, analysis_result):
        if analysis_result["sentiment_score"] < 3 and analysis_result["financial_score"] > 7:
            return {
                "alert": True,
                "type": "Opportunity",
                "message": "Negative sentiment but strong fundamentals → possible undervaluation"
            }

        return {"alert": False}