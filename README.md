# 🏛️ THE COUNCIL - Multi-Agent AI Research Terminal

**THE COUNCIL** is a sophisticated terminal-based research application that orchestrates multiple AI agents (Local Ollama models + Web APIs) to produce high-quality, verified research outputs. By using consensus voting and iterative elimination, it significantly reduces AI hallucinations and provides cited, reliable information.

## ✨ Key Features

- **Multi-Agent Orchestration:** Run multiple LLMs (Ollama, Gemini, Claude, OpenAI) simultaneously.
- **Anti-Hallucination Engine:** 
  - **Cross-Validation:** Agents evaluate and score each other's work.
  - **Consensus Voting:** Requires an 80% agreement threshold (configurable) for facts.
  - **Iterative Elimination:** Automatically removes the lowest-performing agent if consensus isn't reached.
- **Hybrid Knowledge:** Combines **Web Search** (DuckDuckGo) with **RAG** (Retrieval-Augmented Generation) from your past research sessions.
- **Interactive TUI:** A beautiful Terminal User Interface built with `Textual`.
- **Flexible Modes:**
  - `/council research`: Competitive mode where weak agents are eliminated.
  - `/council begin`: Collaborative mode where agents refine a single answer together.

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Ollama** (Recommended for local models) - [Download here](https://ollama.com/)

### Installation
Clone the repository and run the automated installer:

```bash
git clone https://github.com/saadsh15/ai_council.git
cd ai_council
bash scripts/install.sh
```

After installation, restart your terminal or run `source ~/.bashrc`.

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
| `/council add <provider> [model]` | Add a specific agent (e.g., `gemini`, `ollama`). |
| `/council remove <agent_id>` | Remove a specific agent from the council. |
|council preferences <text> | Set global research tailoring preferences|
| `/council research <query>` | Start a research task with the elimination mechanism. |
| `/council begin <query>` | Start a deliberative/collaborative research session. |
| `/council list` | List all active agents and available models. |
| `/council config` | View current configuration. |
| `/council history` | View previous research sessions. |
| `/council clear` | Clear research session history. |
| `/quit` | Exit the application. |

## ⚙️ Configuration

You can tailor research results and system behavior:
```bash
/council config preferences "I prefer technical deep-dives with academic citations."
/council config model "llama3:8b"     # Set default Ollama model
/council config threshold 85          # Set consensus threshold (0-100)
```

## 🏗️ Architecture

- **Core:** Async orchestration of agent lifecycles.
- **Consensus:** Weighted scoring based on Accuracy, Completeness, Source Quality, and Clarity.
- **Storage:** JSON-based session management and vector storage for RAG.
- **UI:** Modern TUI with real-time logs and agent status tracking.

## 📄 License
MIT License - See [LICENSE](LICENSE) for details.
