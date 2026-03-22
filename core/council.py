import asyncio
import uuid
import httpx
from typing import List, Optional, Callable
from agents.base_agent import BaseAgent
from agents.ollama_agent import OllamaAgent
from agents.gemini_agent import GeminiAgent
from agents.deepseek_agent import DeepSeekAgent
from utils.models import Session, Agent, Output, Scores, AgentStatus, SessionStatus, OllamaModel
from consensus.voting import ConsensusManager
from consensus.elimination import find_lowest_rated_agent, eliminate_agent
from storage.config import load_config, save_config, AppConfig
from storage.sessions import SessionManager
from utils.hallucination_check import HallucinationChecker
from utils.embeddings import Embedder
from storage.rag import VectorStore
from utils.web_search import WebSearcher, format_search_results
from datetime import datetime

class Council:
    def __init__(self, system_logger: Optional[Callable] = None, research_logger: Optional[Callable] = None):
        self.config: AppConfig = load_config()
        self.session_manager = SessionManager()
        self.agents: List[BaseAgent] = []
        self.current_session: Optional[Session] = None
        self.logger = system_logger or print
        self.research_logger = research_logger or self.logger
        self.available_ollama_models: List[OllamaModel] = []
        self.embedder = Embedder()
        self.vector_store = VectorStore()
        self.web_searcher = WebSearcher()

    def log(self, message: str):
        if self.logger:
            self.logger(message)
        else:
            print(message)

    def log_research(self, message: str):
        if self.research_logger:
            self.research_logger(message)
        else:
            self.log(message)

    async def _get_web_context(self, query: str) -> str:
        """Perform web search for the latest info."""
        self.log(f"Searching the web for latest research on: [cyan]{query}[/]")
        results = await self.web_searcher.search(query)
        return format_search_results(results)

    async def refresh_models(self):
        """Fetch available models from Ollama API."""
        self.log("Refreshing available Ollama models...")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get("http://localhost:11434/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    self.available_ollama_models = [
                        OllamaModel(
                            name=m['name'],
                            size=m['size'],
                            modified_at=m['modified_at'],
                            digest=m['digest']
                        ) for m in data.get('models', [])
                    ]
                    self.log(f"Found {len(self.available_ollama_models)} Ollama models.")
                    
                    # Update default model if the current one is not available
                    model_names = [m.name for m in self.available_ollama_models]
                    if self.config.default_model not in model_names and model_names:
                        # Find a reasonable default if qwen3-coder:30b isn't there
                        # Maybe just pick the first one for now
                        self.config.default_model = model_names[0]
                        self.log(f"Default model updated to: {self.config.default_model}")
                else:
                    self.log(f"[yellow]Failed to fetch Ollama models: HTTP {response.status_code}[/]")
        except Exception as e:
            self.log(f"[yellow]Ollama connection failed: {str(e)}[/]")

    def add_agent(self, provider: str, model: Optional[str] = None) -> str:
        agent_id = f"{provider}-{len(self.agents) + 1}"
        
        if provider == "ollama":
            model = model or self.config.default_model
            agent = OllamaAgent(agent_id, model, system_prompt=self.config.system_prompt)
        elif provider == "gemini":
            model = model or "gemini-1.5-flash"
            agent = GeminiAgent(agent_id, model, system_prompt=self.config.system_prompt)
        elif provider == "deepseek":
            model = model or "deepseek-chat"
            agent = DeepSeekAgent(agent_id, model, system_prompt=self.config.system_prompt)
        else:
            raise ValueError(f"Unsupported provider: {provider}")
        
        self.agents.append(agent)
        
        # Refresh UI sidebar if available
        if hasattr(self.logger, "__self__") and hasattr(self.logger.__self__, "update_agent_list"):
            self.logger.__self__.update_agent_list()
            
        return agent_id

    async def run_deliberation(self, query: str):
        """A more interactive deliberation where agents see each other's work and refine."""
        if not self.agents:
            self.log("[red]Error: No active agents in the council.[/]")
            return

        # Phase 0: Knowledge Retrieval
        rag_context = await self._get_rag_context(query)
        web_context = await self._get_web_context(query)
        user_pref_context = f"USER PREFERENCES:\n{self.config.user_preferences}\n" if self.config.user_preferences else ""
        initial_context = f"{user_pref_context}\n{web_context}\n{rag_context}".strip()

        self.log(f"Starting Council Deliberation: [bold cyan]{query}[/]")
        
        self.current_session = Session(
            session_id=str(uuid.uuid4()),
            query=query,
            agents=[Agent(agent_id=a.agent_id, provider=a.provider, model=a.model) for a in self.agents]
        )

        active_agents = [a for a in self.agents if a.status == "active"]
        
        # Round 1: Initial Proposals
        self.log("\n[bold green]--- Round 1: Initial Proposals ---[/]")
        tasks = [a.generate(query, context=initial_context) for a in active_agents]
        round1_outputs = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_round1 = []
        for i, output in enumerate(round1_outputs):
            if isinstance(output, Output):
                valid_round1.append(output)
                self.log(f"  - {active_agents[i].agent_id} proposed a solution.")
            else:
                self.log(f"  - [red]{active_agents[i].agent_id} failed: {output}[/]")

        if not valid_round1:
            self.log("[red]Deliberation failed: No valid initial proposals.[/]")
            return

        # Round 2: Deliberation & Refinement
        self.log("\n[bold green]--- Round 2: Peer Review & Refinement ---[/]")
        
        # Build the deliberation context (everyone sees everyone's round 1)
        deliberation_text = "CURRENT PROPOSALS FROM THE COUNCIL:\n"
        for o in valid_round1:
            deliberation_text += f"AGENT {o.agent_id} PROPOSED:\n{o.content}\n\n"
        
        # Only agents that succeeded in Round 1 should refine
        successful_agent_ids = [o.agent_id for o in valid_round1]
        refinement_agents = [a for a in active_agents if a.agent_id in successful_agent_ids]

        if not refinement_agents:
            self.log("[red]No agents available for refinement. Stopping.[/]")
            return

        refinement_tasks = []
        for agent in refinement_agents:
            # Find this agent's specific round 1 output to remind them of their own work
            own_proposal = next((o.content for o in valid_round1 if o.agent_id == agent.agent_id), "")
            
            refine_prompt = (
                f"You are participating in a council deliberation for the query: '{query}'.\n\n"
                f"YOUR INITIAL PROPOSAL:\n{own_proposal}\n\n"
                f"OTHER COUNCIL PROPOSALS:\n{deliberation_text}\n"
                "INSTRUCTIONS:\n"
                "1. Critically review your initial proposal against the other insights provided.\n"
                "2. Correct any factual errors or hallucinations in your work.\n"
                "3. Incorporate high-quality information found in other proposals.\n"
                "4. Provide your FINAL CONSOLIDATED RESEARCH ANSWER."
            )
            refinement_tasks.append(agent.generate(refine_prompt))
        
        round2_outputs = await asyncio.gather(*refinement_tasks, return_exceptions=True)
        
        valid_round2 = []
        for i, output in enumerate(round2_outputs):
            if isinstance(output, Output):
                valid_round2.append(output)
                self.log(f"  - {refinement_agents[i].agent_id} refined their answer.")
            else:
                self.log(f"  - [red]{refinement_agents[i].agent_id} failed to refine: {output}[/]")

        if not valid_round2:
            self.log("[red]Deliberation failed: All agents failed to refine their answers.[/]")
            return

        # Phase 3: Final Consensus (Voting on Refined Answers)
        self.log("\n[bold green]--- Round 3: Final Consensus Voting ---[/]")
        consensus_mgr = ConsensusManager(active_agents)
        scored_outputs = await consensus_mgr.run_voting_round(valid_round2)
        
        if not scored_outputs:
            self.log("[red]Voting failed to produce any scored outputs.[/]")
            return

        for o in scored_outputs:
            self.log(f"  - {o.agent_id} refined score: [bold]{o.scores.average:.2f}[/]")

        # Pick the best refined answer
        scored_outputs.sort(key=lambda x: x.scores.average, reverse=True)
        final_output = scored_outputs[0]
        self.current_session.final_consensus = final_output.content
        self.current_session.status = SessionStatus.COMPLETED
        self.current_session.outputs.extend(scored_outputs)

        # Save and Index
        self.session_manager.save_session(self.current_session)
        result_embedding = await self.embedder.get_embedding(self.current_session.final_consensus)
        if result_embedding:
            self.vector_store.add(
                text=self.current_session.final_consensus,
                embedding=result_embedding,
                metadata={"query": query, "type": "deliberation"}
            )

        self.log(f"Deliberation complete. Session saved: {self.current_session.session_id}")

        if self.current_session.final_consensus:
            self.log_research("\n[bold green]COUNCIL DELIBERATION FINAL ANSWER:[/]")
            self.log_research(self.current_session.final_consensus)
        else:
            self.log_research("[red]Deliberation failed: No final answer reached.[/]")

    def remove_agent(self, agent_id: str):
        self.agents = [a for a in self.agents if a.agent_id != agent_id]

    def list_agents(self) -> List[BaseAgent]:
        return self.agents

    async def _get_rag_context(self, query: str) -> str:
        """Retrieve relevant past interactions and user preferences."""
        self.log("Searching past interactions (RAG)...")
        query_embedding = await self.embedder.get_embedding(query)
        if not query_embedding:
            return ""
            
        matches = self.vector_store.search(query_embedding, top_k=2)
        if not matches:
            return ""
            
        context = "PAST RESEARCH FINDINGS (RAG):\n"
        for i, match in enumerate(matches):
            context += f"Result {i+1} (similarity: {match['similarity']:.2f}):\n{match['text']}\n"
        
        return context

    async def run_research(self, query: str):
        if not self.agents:
            self.log("[red]Error: No active agents in the council.[/]")
            return

        # Phase 0: Knowledge Retrieval
        # RAG - Context Retrieval
        rag_context = await self._get_rag_context(query)
        
        # Web Search Retrieval
        web_context = await self._get_web_context(query)
        
        # User Preference Tailoring
        user_pref_context = ""
        if self.config.user_preferences:
            user_pref_context = f"USER PREFERENCES:\n{self.config.user_preferences}\n"

        full_context = f"{user_pref_context}\n{web_context}\n{rag_context}".strip()

        self.log(f"Starting research on: [bold cyan]{query}[/]")
        if full_context:
            self.log("[dim cyan]Context retrieved (Web + RAG + Preferences) for research.[/]")
        
        self.current_session = Session(
            session_id=str(uuid.uuid4()),
            query=query,
            agents=[Agent(agent_id=a.agent_id, provider=a.provider, model=a.model) for a in self.agents]
        )

        round_num = 1
        while True:
            active_agents = [a for a in self.agents if a.status == "active"]
            if len(active_agents) < 2:
                self.log("[yellow]Minimum agents (2) reached or too few agents. Stopping iteration.[/]")
                break

            self.log(f"\n[bold green]--- Round {round_num} ---[/]")
            
            # Phase 1: Initial output generation
            self.log("Agents generating responses...")
            tasks = [a.generate(query, context=full_context) for a in active_agents]
            outputs = await asyncio.gather(*tasks, return_exceptions=True)
            
            valid_outputs = []
            for i, output in enumerate(outputs):
                if isinstance(output, Output):
                    valid_outputs.append(output)
                    self.log(f"  - {active_agents[i].agent_id} completed.")
                else:
                    self.log(f"  - [red]{active_agents[i].agent_id} failed: {output}[/]")
            
            if not valid_outputs:
                self.log("[red]No valid outputs this round.[/]")
                break

            # Phase 2: Voting and Scoring
            self.log("Cross-validation in progress...")
            consensus_mgr = ConsensusManager(active_agents)
            scored_outputs = await consensus_mgr.run_voting_round(valid_outputs)
            
            for o in scored_outputs:
                self.log(f"  - {o.agent_id} score: [bold]{o.scores.average:.2f}[/]")

            self.current_session.outputs.extend(scored_outputs)

            # Phase 3: Hallucination Check
            self.log("Performing hallucination checks...")
            # Use the best agent for checking
            best_agent = sorted(scored_outputs, key=lambda x: x.scores.average, reverse=True)[0]
            checker_agent = next(a for a in active_agents if a.agent_id == best_agent.agent_id)
            checker = HallucinationChecker(checker_agent)
            contradictions = await checker.check_contradictions(scored_outputs)
            
            if contradictions:
                for c in contradictions:
                    self.log(f"[bold red]Contradiction Detected:[/]\n{c}")

            # Phase 4: Consensus check and Elimination
            if consensus_mgr.check_consensus(scored_outputs, self.config.threshold):
                self.log(f"\n[bold green]Consensus reached at {self.config.threshold}%![/]")
                # Final output is the highest scored one
                final_output = sorted(scored_outputs, key=lambda x: x.scores.average, reverse=True)[0]
                self.current_session.final_consensus = final_output.content
                self.current_session.status = SessionStatus.COMPLETED
                break
            else:
                lowest_agent_id = find_lowest_rated_agent(scored_outputs)
                if lowest_agent_id:
                    self.log(f"Consensus below threshold. [bold red]Eliminating agent: {lowest_agent_id}[/]")
                    for a in self.agents:
                        if a.agent_id == lowest_agent_id:
                            a.status = "eliminated"
                    self.current_session.elimination_rounds.append(lowest_agent_id)
                    
                    # Refresh UI sidebar
                    if hasattr(self.logger, '__self__') and hasattr(self.logger.__self__, 'update_agent_list'):
                        self.logger.__self__.update_agent_list()
                else:
                    break

            round_num += 1
            if round_num > 5: # Safety limit
                self.log("[yellow]Maximum rounds reached. Stopping.[/]")
                break

        # If no strict consensus was reached, pick the best output available
        if not self.current_session.final_consensus and self.current_session.outputs:
            self.log("[yellow]No strict consensus reached. Selecting highest-scored output as fallback.[/]")
            final_output = sorted(self.current_session.outputs, key=lambda x: x.scores.average, reverse=True)[0]
            self.current_session.final_consensus = final_output.content
            self.current_session.status = SessionStatus.COMPLETED

        # Save session
        self.session_manager.save_session(self.current_session)
        
        # RAG - Index the result
        if self.current_session.final_consensus:
            self.log("Indexing research result for future RAG retrieval...")
            result_embedding = await self.embedder.get_embedding(self.current_session.final_consensus)
            if result_embedding:
                self.vector_store.add(
                    text=self.current_session.final_consensus,
                    embedding=result_embedding,
                    metadata={"query": query, "timestamp": datetime.utcnow().isoformat()}
                )

        # Log to system
        self.log(f"Session saved: {self.current_session.session_id}")

        # Log to researcher output
        if self.current_session.final_consensus:
            self.log_research("\n[bold cyan]FINAL RESEARCH OUTPUT:[/]")
            self.log_research(self.current_session.final_consensus)
        else:
            self.log_research("[red]Research failed: No valid consensus or output generated.[/]")
            
        # Final UI sidebar refresh
        if hasattr(self.logger, "__self__") and hasattr(self.logger.__self__, "update_agent_list"):
            self.logger.__self__.update_agent_list()
