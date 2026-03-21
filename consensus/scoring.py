from typing import List
from utils.models import Scores, Output

def calculate_weighted_average(scores: Scores) -> float:
    """Calculate the weighted average based on project criteria."""
    weights = {
        "accuracy": 0.35,
        "completeness": 0.25,
        "source_quality": 0.25,
        "clarity": 0.15
    }
    
    weighted_sum = (
        scores.accuracy * weights["accuracy"] +
        scores.completeness * weights["completeness"] +
        scores.source_quality * weights["source_quality"] +
        scores.clarity * weights["clarity"]
    )
    
    return weighted_sum

def update_output_scores(output: Output, peer_scores: List[Scores]):
    """Update an output's scores based on multiple peer evaluations."""
    if not peer_scores:
        return

    num_evals = len(peer_scores)
    
    total_accuracy = sum(s.accuracy for s in peer_scores)
    total_completeness = sum(s.completeness for s in peer_scores)
    total_source_quality = sum(s.source_quality for s in peer_scores)
    total_clarity = sum(s.clarity for s in peer_scores)
    
    output.scores.accuracy = total_accuracy / num_evals
    output.scores.completeness = total_completeness / num_evals
    output.scores.source_quality = total_source_quality / num_evals
    output.scores.clarity = total_clarity / num_evals
    
    output.scores.average = calculate_weighted_average(output.scores)
