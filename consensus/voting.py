from typing import List, Dict
import asyncio
from agents.base_agent import BaseAgent
from utils.models import Output, Session, Scores, AgentStatus
from consensus.scoring import update_output_scores

class ConsensusManager:
    def __init__(self, agents: List[BaseAgent]):
        self.agents = {a.agent_id: a for a in agents if a.status == AgentStatus.ACTIVE}

    async def run_voting_round(self, outputs: List[Output]) -> List[Output]:
        """Conduct a voting round where agents evaluate each other's outputs."""
        if len(self.agents) < 2:
            return outputs

        for output in outputs:
            peer_scores = []
            evaluators = [a for a in self.agents.values() if a.agent_id != output.agent_id]
            
            # Each output must be validated by at least 2 other agents (if available)
            tasks = []
            for agent in evaluators:
                tasks.append(agent.evaluate(output))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_scores = []
            for i, result in enumerate(results):
                if isinstance(result, Scores):
                    valid_scores.append(result)
                    output.votes_from.append(evaluators[i].agent_id)
                else:
                    print(f"Error during evaluation by {evaluators[i].agent_id}: {result}")
            
            update_output_scores(output, valid_scores)
            
        return outputs

    def check_consensus(self, outputs: List[Output], threshold: float = 0.8) -> bool:
        """Check if consensus is reached based on average scores."""
        if not outputs:
            return False
        
        avg_consensus = sum(o.scores.average for o in outputs) / len(outputs)
        return avg_consensus >= (threshold / 100.0)
