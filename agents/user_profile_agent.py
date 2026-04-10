from agents.base_agent import BaseAgent

class UserProfileAgent(BaseAgent):
    def __init__(self):
        super().__init__("User Profile Agent")

    def run(self, risk_level, investment_horizon, capital):
        return {
            "risk_level": risk_level,  # low, medium, high
            "investment_horizon": investment_horizon,  # short, medium, long
            "capital": capital
        }