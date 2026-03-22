from abc import ABC, abstractmethod
from typing import List, Optional
from utils.models import Output, Scores

class BaseAgent(ABC):
    def __init__(self, agent_id: str, model: str, provider: str, system_prompt: Optional[str] = None):
        self.agent_id = agent_id
        self.model = model
        self.provider = provider
        self.status = "active"
        self.system_prompt = system_prompt

    @abstractmethod
    async def generate(self, prompt: str, context: Optional[str] = None) -> Output:
        """Generate research output for a given prompt."""
        pass

    @abstractmethod
    async def evaluate(self, other_output: Output) -> Scores:
        """Evaluate another agent's output for consensus/voting."""
        pass

    def __repr__(self):
        return f"<Agent {self.agent_id} ({self.provider}:{self.model})>"
