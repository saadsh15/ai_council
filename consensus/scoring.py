from typing import List
from utils.models import Scores, Output

def calculate_weighted_average(scores: Scores) -> float:
    """Calculate the weighted average based on project criteria."""
    # Weights for the new criteria
    weights = {
        "factual_accuracy_faithfulness": 0.40,
        "relevance_completeness": 0.40,
        "clarity_usability": 0.20
    }
    
    weighted_sum = (
        scores.factual_accuracy_faithfulness * weights["factual_accuracy_faithfulness"] +
        scores.relevance_completeness * weights["relevance_completeness"] +
        scores.clarity_usability * weights["clarity_usability"]
    )
    
    return weighted_sum

def update_output_scores(output: Output, peer_scores: List[Scores]):
    """Update an output's scores based on multiple peer evaluations."""
    if not peer_scores:
        return

    num_evals = len(peer_scores)
    
    total_factual_accuracy_faithfulness = sum(s.factual_accuracy_faithfulness for s in peer_scores)
    total_relevance_completeness = sum(s.relevance_completeness for s in peer_scores)
    total_clarity_usability = sum(s.clarity_usability for s in peer_scores)
    
    output.scores.factual_accuracy_faithfulness = total_factual_accuracy_faithfulness / num_evals
    output.scores.relevance_completeness = total_relevance_completeness / num_evals
    output.scores.clarity_usability = total_clarity_usability / num_evals
    
    output.scores.average = calculate_weighted_average(output.scores)
