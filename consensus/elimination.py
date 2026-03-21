from typing import List, Tuple
from utils.models import Agent, Output, AgentStatus

def find_lowest_rated_agent(outputs: List[Output]) -> str:
    """Find the agent ID with the lowest average score."""
    if not outputs:
        return ""
    
    # Map agent_id to their average score
    scores = {}
    for output in outputs:
        scores[output.agent_id] = output.scores.average
        
    # Sort agents by score
    sorted_agents = sorted(scores.items(), key=lambda x: x[1])
    return sorted_agents[0][0] if sorted_agents else ""

def eliminate_agent(agents: List[Agent], agent_id: str) -> List[Agent]:
    """Mark an agent as eliminated."""
    for agent in agents:
        if agent.agent_id == agent_id:
            agent.status = AgentStatus.ELIMINATED
            break
    return agents
