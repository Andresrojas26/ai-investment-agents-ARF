# agents/base_agent.py

class BaseAgent:
    def __init__(self, name):
        self.name = name

    def run(self, *args, **kwargs):
        raise NotImplementedError("Each agent must implement the run method")

