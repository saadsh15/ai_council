# THE COUNCIL - Multi-Agent AI Research Terminal Application

## Project Overview

Create a terminal-based AI application named "the council" that orchestrates multiple AI agents from different providers (Ollama local models + web-based AI APIs) to produce research outputs with minimal hallucination through consensus voting and elimination mechanisms.

## Core Architecture Requirements

### 1. Multi-Agent System Design

- Implement a **multi-agent multi-LLM architecture** where each agent operates independently [[2]]
- Support both **local Ollama models** (via REST API at localhost:11434) [[11]] and **web-based AI providers** (Gemini, Claude, OpenAI, etc.)
- Each agent must be **task-specialized** but can be configured by the user [[7]]
- Agents must operate **autonomously** with independent decision-making [[9]]

### 2. Hallucination Reduction Mechanisms

Implement the following anti-hallucination strategies [[20]][[26]]:

- **Cross-validation**: Each agent's output must be validated by at least 2 other agents
- **Consensus-building**: Require agreement threshold before accepting facts
- **Source citation requirement**: All claims must include verifiable sources
- **Confidence scoring**: Each agent must provide confidence levels for their outputs
- **Adversarial validation**: Designate one agent as "critic" to challenge outputs [[25]]

### 3. Voting & Elimination System

- **Initial round**: All agents produce independent outputs
- **Ranking system**: Score each output on:
  - Accuracy (verified facts)
  - Completeness (coverage of topic)
  - Source quality (verifiable references)
  - Confidence level (agent's self-assessment)
- **Average calculation**: Compute weighted average score for each output
- **Elimination**: Terminate the lowest-rated agent from the conversation round
- **Iteration**: Continue until consensus threshold (e.g., 80% agreement) or minimum agents (2) reached [[41]]

## Technical Specifications

### 4. Ollama Integration

API Endpoint: http://localhost:11434
Chat Endpoint: /api/chat
Models Endpoint: /api/tags


- Use Ollama's REST API for local model access [[13]]
- Support model listing, pulling, and selection
- Implement streaming responses for terminal display
- Handle model availability checks before assignment

### 5. Web API Integration

- Support multiple provider APIs:
  - Google Gemini API
  - Anthropic Claude API
  - OpenAI API
  - Any OpenAI-compatible endpoints
- Implement API key management (secure storage, not hardcoded)
- Rate limiting and quota tracking per provider
- Fallback mechanisms if API fails

### 6. Terminal CLI Interface

- **Command prefix**: All commands use `/` operator
- **Fixed command set**: No dynamic command generation (user control) [[33]]
- **Interactive mode**: Real-time agent output display
- **Session management**: Save/load research sessions

## Command Structure

### 7. Required Commands (Fixed Set)

/council start - Initialize the council with selected agents
/council add <provider> - Add an agent from specified provider
/council remove <agent_id> - Remove an agent from the council
/council list - List all available and active agents
/council research <query> - Begin research query with all active agents
/council vote - Trigger manual voting round
/council eliminate - Manually eliminate lowest-rated agent
/council export <format> - Export research results (json, md, txt)
/council config - View/modify configuration
/council history - View session history
/council clear - Clear current session
/council help - Display all available commands
/quit - Exit the application


### 8. Configuration Commands

/config provider <name> - Set default AI provider
/config model <name> - Set default model for provider
/config threshold <value> - Set consensus threshold (0-100)
/config timeout <seconds> - Set agent response timeout
/config verbose <on|off> - Toggle detailed output



## Data Structures

### 9. Agent Object

```json
{
  "agent_id": "unique_identifier",
  "provider": "ollama|gemini|claude|openai",
  "model": "model_name",
  "status": "active|eliminated|error",
  "confidence_score": 0.0-1.0,
  "response_count": 0,
  "accuracy_history": []
}

10. Output Object

{
  "output_id": "unique_identifier",
  "agent_id": "reference_to_agent",
  "content": "response_text",
  "sources": ["url1", "url2"],
  "confidence": 0.0-1.0,
  "timestamp": "ISO8601",
  "scores": {
    "accuracy": 0.0,
    "completeness": 0.0,
    "source_quality": 0.0,
    "average": 0.0
  },
  "votes_from": ["agent_id1", "agent_id2"]
}

11. Session Object

{
  "session_id": "unique_identifier",
  "created_at": "ISO8601",
  "query": "research_topic",
  "agents": [],
  "outputs": [],
  "elimination_rounds": [],
  "final_consensus": "",
  "status": "active|completed|terminated"
}

Implementation Requirements
12. Programming Language & Framework
Primary language: Python 3.11+ (best CLI library support) 
python.plainenglish.io
CLI framework: Use click or typer for command parsing
Async support: Use asyncio for parallel agent calls
Terminal UI: Use rich or textual for formatted output
Configuration: YAML or JSON config files

13. File Structure
the_council/
├── main.py                 # Application entry point
├── cli/
│   ├── commands.py         # Command handlers
│   └── interface.py        # Terminal interface
├── agents/
│   ├── base_agent.py       # Abstract agent class
│   ├── ollama_agent.py     # Ollama implementation
│   ├── gemini_agent.py     # Gemini implementation
│   ├── claude_agent.py     # Claude implementation
│   └── openai_agent.py     # OpenAI implementation
├── consensus/
│   ├── voting.py           # Voting mechanisms
│   ├── scoring.py          # Output scoring logic
│   └── elimination.py      # Agent elimination logic
├── storage/
│   ├── sessions.py         # Session management
│   └── config.py           # Configuration management
├── utils/
│   ├── hallucination_check.py  # Anti-hallucination validators
│   └── source_validator.py     # Source verification
├── config/
│   └── default_config.yaml
├── requirements.txt
└── README.md

14. Security Requirements
API keys: Store in environment variables or encrypted config 
nexaitech.com
No hardcoded credentials: All secrets externalized
Input validation: Sanitize all user inputs
Rate limiting: Prevent API abuse
Session encryption: Encrypt stored session data
15. Error Handling
Agent timeout: Handle slow/non-responsive agents
API failures: Graceful degradation with fallback agents
Network issues: Retry logic with exponential backoff
Invalid commands: Clear error messages with suggestions
Model errors: Automatic agent removal on repeated failures
Consensus Algorithm
16. Voting Mechanism Implementation
12345678910
17. Scoring Criteria
Criteria
Weight
Description
Accuracy
35%
Factual correctness, verifiable claims
Completeness
25%
Topic coverage, depth of analysis
Source Quality
25%
Citation quality, source credibility
Clarity
15%
Readability, logical structure
18. Hallucination Detection
Cross-reference check: Compare claims across all agents 
领英企业服务
Source verification: Validate all cited sources exist
Confidence threshold: Flag low-confidence claims
Contradiction detection: Identify conflicting information
Fact-checking API: Optional integration with fact-check services 
DEV社区
User Experience
19. Terminal Display
Agent identification: Color-code each agent's output
Progress indicators: Show agent status in real-time
Score visualization: Display scores as progress bars
Elimination notifications: Clear alerts when agents are removed
Final consensus: Highlighted display of agreed conclusions
20. Session Management
Auto-save: Save session state periodically
Session resume: Continue from previous state
Export formats: JSON, Markdown, Plain Text
History search: Search through past research sessions
Testing Requirements
21. Test Coverage
Unit tests: All agent classes, scoring, voting logic
Integration tests: API connections, Ollama communication
End-to-end tests: Full research workflow
Load tests: Multiple concurrent agents
Error scenario tests: Network failures, API limits
22. Validation Tests
Test with known factual queries (verify accuracy)
Test hallucination resistance (compare with single-agent)
Test elimination logic (verify lowest-scored removed)
Test command parsing (all /commands work correctly)
Documentation Requirements
23. User Documentation
Installation guide (all platforms)
Configuration tutorial
Command reference (all /commands)
Provider setup guides (Ollama, Gemini, etc.)
Troubleshooting section
24. Developer Documentation
Architecture diagrams
API reference
Extension guide (adding new providers)
Contributing guidelines
Performance Requirements
25. Response Times
Agent response: < 30 seconds per agent (configurable)
Voting round: < 10 seconds calculation
Session load: < 2 seconds
Command execution: < 1 second (non-API commands)
26. Resource Usage
Memory: < 500MB base + per-agent overhead
CPU: Efficient async processing
Network: Minimize API calls, cache when possible
Compliance & Ethics
27. Requirements
Transparency: Show which agents contributed to final output
Attribution: Credit all sources used
Privacy: No data sent to third parties without consent
Bias disclosure: Note potential model biases
Audit trail: Log all agent decisions for review 
nexaitech.com
Deployment
28. Distribution
Package: PyPI package (the-council)
Installer: pip install the-council
Docker: Optional container deployment
Platform support: Linux, macOS, Windows 
docs.ollama.com
29. Version Control
Semantic versioning: Major.Minor.Patch
Changelog: Document all changes
Release notes: Per version documentation
Success Metrics
30. Quality Indicators
Hallucination rate: < 5% (vs 15-20% single agent) 
gafowler.medium.com
Consensus achievement: > 80% of sessions reach consensus
User satisfaction: Command usability score > 4/5
Accuracy improvement: > 30% vs single-agent baseline 
medium.com
IMPORTANT INSTRUCTIONS FOR GEMINI CLI
Do not assume any implementation details not specified above
Ask for clarification if any requirement is ambiguous
Follow the fixed command structure - do not add dynamic commands
Prioritize hallucination reduction over speed
Implement all security requirements before feature completion
Create comprehensive tests before marking any feature complete
Document all code with docstrings and comments
Use async/await for all API calls to maximize parallelism
Implement graceful degradation - app should work with minimum 1 agent
Validate all user inputs before processing

First Steps
Create the project structure as specified
Implement the base agent abstract class
Implement Ollama agent (most accessible for testing)
Implement CLI command parser
Implement voting/scoring system
Add web API agents (Gemini, Claude, OpenAI)
Implement session management
Add comprehensive testing
Create documentation
Package for distribution



