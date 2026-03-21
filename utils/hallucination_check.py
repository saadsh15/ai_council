from typing import List, Dict
from utils.models import Output
from agents.base_agent import BaseAgent

class HallucinationChecker:
    def __init__(self, agent: BaseAgent):
        self.agent = agent

    async def check_contradictions(self, outputs: List[Output]) -> List[str]:
        """Identify potential contradictions across multiple agent outputs."""
        if len(outputs) < 2:
            return []
            
        # Combine outputs for comparison
        combined_text = "\n\n".join([f"AGENT {o.agent_id} OUTPUT:\n{o.content}" for o in outputs])
        
        prompt = (
            "You are a fact-checker. Compare the following research outputs and identify any "
            "direct contradictions or conflicting claims. Be specific about which claims conflict. "
            "If no contradictions are found, state 'NO CONTRADICTIONS'.\n\n"
            f"OUTPUTS TO COMPARE:\n{combined_text}"
        )
        
        # Use the provided agent to perform the check
        result = await self.agent.generate(prompt)
        
        if "NO CONTRADICTIONS" in result.content:
            return []
            
        return [result.content]
