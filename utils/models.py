from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AgentStatus(str, Enum):
    ACTIVE = "active"
    ELIMINATED = "eliminated"
    ERROR = "error"

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    TERMINATED = "terminated"

class OllamaModel(BaseModel):
    name: str
    size: int
    modified_at: datetime
    digest: str

class Agent(BaseModel):
    agent_id: str
    provider: str
    model: str
    status: AgentStatus = AgentStatus.ACTIVE
    confidence_score: float = Field(0.0, ge=0.0, le=1.0)
    response_count: int = 0
    accuracy_history: List[float] = []

class Scores(BaseModel):
    accuracy: float = 0.0
    completeness: float = 0.0
    source_quality: float = 0.0
    clarity: float = 0.0
    average: float = 0.0

class Output(BaseModel):
    output_id: str
    agent_id: str
    content: str
    sources: List[str] = []
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    scores: Scores = Field(default_factory=Scores)
    votes_from: List[str] = []

class Session(BaseModel):
    session_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    query: str
    agents: List[Agent] = []
    outputs: List[Output] = []
    elimination_rounds: List[str] = [] # List of eliminated agent IDs in order
    final_consensus: str = ""
    status: SessionStatus = SessionStatus.ACTIVE
