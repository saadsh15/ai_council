# 🏛️ THE COUNCIL - Multi-Agent AI Research Terminal

**THE COUNCIL** is a sophisticated terminal-based research application that orchestrates multiple AI agents (Local Ollama models + Web APIs) to produce high-quality, verified research outputs. By using multi-factor ranking, consensus voting, and iterative refinement, it significantly reduces AI hallucinations and provides cited, reliable information.

## ✨ Key Features

- **Multi-Agent Orchestration:** Run multiple LLMs (Ollama, Gemini, Claude, OpenAI, DeepSeek) simultaneously.
- **Anti-Hallucination Engine:** 
  - **Cross-Validation:** Agents evaluate and rank each other's work based on specific criteria.
  - **Consensus Voting:** Requires a 0.82 agreement threshold for facts in deliberation.
  - **Contradiction Detection:** Automatic identification of conflicting claims across agents.
- **Advanced Ranking System:** 
  - **Factual Accuracy & Faithfulness (40%)**: Groundedness in context and absence of hallucinations.
  - **Relevance & Completeness (40%)**: Coverage of the query and topic depth.
  - **Clarity & Usability (20%)**: Readability, logical structure, and practical utility.
- **Hybrid Knowledge & News:** 
  - **Web & News Search:** Integrated DuckDuckGo search (Web + News tab) for real-time data without API keys.
  - **RAG:** Retrieval-Augmented Generation from your past research sessions.
  - **Parallel Execution:** Searches are performed in parallel for maximum speed.
- **Interactive TUI:** A beautiful Terminal User Interface built with `Textual`.
- **Flexible Modes:**
  - `/council research`: Competitive mode where agents are ranked and potentially eliminated.
  - `/council begin`: Robust deliberative mode with iterative refinement and strict consensus thresholds.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Ollama** (Recommended for local models) - [Download here](https://ollama.com/)

### Installation
Clone the repository and run the automated installer for your platform:

#### Linux
```bash
git clone https://github.com/saadsh15/ai_council.git
cd ai_council
bash scripts/install.sh
```

#### macOS
```bash
git clone https://github.com/saadsh15/ai_council.git
cd ai_council
bash scripts/install_mac.sh
```

### Environment Configuration
The application can use both local models (Ollama) and web-based AI APIs. To use web-based providers, copy the `.env.example` file and add your API keys:

```bash
cp .env.example .env
```

Edit the `.env` file and provide keys for the models you want to use:
- **Gemini:** [Get API Key](https://aistudio.google.com/app/apikey)
- **DeepSeek:** [Get API Key](https://platform.deepseek.com/)

### Running the App
Simply type:
```bash
the-council
```

## 🛠️ Commands

All commands are prefixed with `/council`:

| Command | Description |
| :--- | :--- |
| `/council help` | Display all available commands. |
| `/council start` | Initialize the council with default local models. |
| `/council add <provider> [model]` | Add a specific agent (e.g., `gemini`, `ollama`, `deepseek`). |
| `/council remove <agent_id>` | Remove a specific agent from the council. |
| `/council preferences <text>` | Set global research tailoring preferences. |
| **`/council research <query>`** | **Offline Research:** Uses RAG and user preferences only. |
| **`/council web-research <query>`**| **Web Research:** Forces agents to use Web and News search results. |
| **`/council begin <query>`** | **Deliberation:** Collaborative mode with iterative refinement and a 0.82 consensus threshold. |
| `/council list` | List all active agents and available models. |
| `/council config` | View/modify current configuration. |
| `/council history` | View previous research sessions. |
| `/council clear` | Clear research session history. |
| `/quit` | Exit the application. |

## ⚙️ Configuration

You can tailor research results and system behavior:
```bash
/council config preferences "I prefer technical deep-dives with academic citations."
/council config model "llama3:8b"     # Set default Ollama model
/council config threshold 85          # Set consensus threshold (0-100)
/council config prompt "You are..."   # Set custom global system prompt
```

## 🏗️ Architecture

- **Core Deliberation Engine:** Uses an iterative refinement loop. If the best answer doesn't reach a 0.82 consensus score, agents receive critical feedback (including hallucination reports) and must refine the answer in the next round.
- **Ranking Logic:** Every model is forced to evaluate its peers against the three primary criteria (Accuracy, Relevance, Clarity).
- **News Integration:** Utilizes the DuckDuckGo News API for up-to-the-minute information from multiple sources.
- **Storage:** JSON-based session management and vector storage for RAG.
- **UI:** Modern TUI with real-time logs, ranking displays, and agent status tracking.

## 📄 License
MIT License - See [LICENSE](LICENSE) for details.
