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
        """Perform web and news search for the latest info."""
        self.log(f"Searching web and news for: [cyan]{query}[/]")
        
        # Parallel search for speed
        web_task = self.web_searcher.search(query)
        news_task = self.web_searcher.search_news(query)
        
        web_results, news_results = await asyncio.gather(web_task, news_task)
        
        return format_search_results(web_results, news_results)

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

    async def run_deliberation(self, query: str, use_web: bool = False):
        """A more interactive deliberation where agents see each other's work and refine."""
        if not self.agents:
            self.log("[red]Error: No active agents in the council.[/]")
            return

        # Phase 0: Knowledge Retrieval
        rag_context = await self._get_rag_context(query)
        web_context = ""
        if use_web:
            web_context = await self._get_web_context(query)
            
        user_pref_context = f"USER PREFERENCES:\n{self.config.user_preferences}\n" if self.config.user_preferences else ""
        
        web_instruction = ""
        if use_web and web_context:
            web_instruction = "\nINSTRUCTION: You MUST incorporate relevant information and recent news from the provided web/news context into your research. Cite sources where possible.\n"

        initial_context = f"{user_pref_context}\n{web_context}\n{rag_context}{web_instruction}".strip()

        self.log(f"Starting Council Deliberation: [bold cyan]{query}[/]")
        
        self.current_session = Session(
            session_id=str(uuid.uuid4()),
            query=query,
            agents=[Agent(agent_id=a.agent_id, provider=a.provider, model=a.model) for a in self.agents]
        )

        active_agents = [a for a in self.agents if a.status == "active"]
        
        # Round 1: Initial Proposals
        self.log("\n[bold green]--- Phase 1: Initial Proposals ---[/]")
        tasks = [a.generate(query, context=initial_context) for a in active_agents]
        outputs = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_proposals = []
        for i, output in enumerate(outputs):
            if isinstance(output, Output):
                valid_proposals.append(output)
                self.log(f"  - {active_agents[i].agent_id} proposed a solution.")
            else:
                self.log(f"  - [red]{active_agents[i].agent_id} failed: {output}[/]")

        if not valid_proposals:
            self.log("[red]Deliberation failed: No valid initial proposals.[/]")
            return

        iteration = 1
        max_iterations = 3
        final_answer = ""
        consensus_threshold = 0.82

        while iteration <= max_iterations:
            self.log(f"\n[bold green]--- Deliberation Round {iteration} ---[/]")
            
            # 1. Ranking & Cross-Validation
            self.log("Ranking current proposals...")
            consensus_mgr = ConsensusManager(active_agents)
            scored_outputs = await consensus_mgr.run_voting_round(valid_proposals)
            scored_outputs.sort(key=lambda x: x.scores.average, reverse=True)
            
            best_output = scored_outputs[0]
            self.log(f"  Current Best: {best_output.agent_id} (Score: {best_output.scores.average:.2f})")

            # 2. Hallucination Check
            self.log("Checking for contradictions and hallucinations...")
            checker_agent = next(a for a in active_agents if a.agent_id == best_output.agent_id)
            checker = HallucinationChecker(checker_agent)
            contradictions = await checker.check_contradictions(scored_outputs)
            
            critique_context = ""
            if contradictions:
                self.log(f"  [bold red]Hallucinations detected![/] Incorporating critique into next round.")
                critique_context = f"\nCRITICAL FEEDBACK ON PREVIOUS ROUND:\n{contradictions[0]}\n"

            # 3. Check Consensus
            # We check if the BEST answer meets the 0.82 threshold from ALL agents
            if best_output.scores.average >= consensus_threshold and not contradictions:
                self.log(f"[bold green]Consensus reached! (Score: {best_output.scores.average:.2f})[/]")
                final_answer = best_output.content
                break
            
            if iteration == max_iterations:
                self.log("[yellow]Max deliberation rounds reached.[/]")
                final_answer = best_output.content
                break

            # 4. Refinement Round
            self.log("Refining proposals based on council feedback...")
            deliberation_text = "CURRENT COUNCIL PROPOSALS:\n"
            for o in scored_outputs[:3]: # Only top 3 for context management
                deliberation_text += f"AGENT {o.agent_id} (Score: {o.scores.average:.2f}):\n{o.content}\n\n"

            refinement_tasks = []
            for agent in active_agents:
                own_proposal = next((o.content for o in valid_proposals if o.agent_id == agent.agent_id), "")
                
                refine_prompt = (
                    f"You are in a high-stakes council deliberation for: '{query}'.\n\n"
                    f"YOUR PREVIOUS VERSION:\n{own_proposal}\n\n"
                    f"COUNCIL BEST PROPOSALS:\n{deliberation_text}\n"
                    f"{critique_context}"
                    "INSTRUCTIONS:\n"
                    "1. Address the hallucinations and errors identified above.\n"
                    "2. Synthesize the best elements from all proposals into a COHERENT, LOGICAL, and FACTUAL final answer.\n"
                    "3. Ensure the structure is clear and the reasoning is sound.\n"
                    "4. Output your consolidated final answer."
                )
                refinement_tasks.append(agent.generate(refine_prompt))

            outputs = await asyncio.gather(*refinement_tasks, return_exceptions=True)
            valid_proposals = [o for o in outputs if isinstance(o, Output)]
            
            if not valid_proposals:
                self.log("[red]Refinement failed: No valid outputs.[/]")
                break
                
            iteration += 1

        self.current_session.final_consensus = final_answer
        self.current_session.status = SessionStatus.COMPLETED
        self.current_session.outputs.extend(valid_proposals)

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

    async def run_research(self, query: str, use_web: bool = False):
        if not self.agents:
            self.log("[red]Error: No active agents in the council.[/]")
            return

        # Phase 0: Knowledge Retrieval
        # RAG - Context Retrieval
        rag_context = await self._get_rag_context(query)
        
        # Web Search Retrieval (Optional)
        web_context = ""
        if use_web:
            web_context = await self._get_web_context(query)
        
        # User Preference Tailoring
        user_pref_context = ""
        if self.config.user_preferences:
            user_pref_context = f"USER PREFERENCES:\n{self.config.user_preferences}\n"

        # Explicit instruction for web research if web_context exists
        web_instruction = ""
        if use_web and web_context:
            web_instruction = "\nINSTRUCTION: You MUST incorporate relevant information and recent news from the provided web/news context into your research. Cite sources where possible.\n"

        full_context = f"{user_pref_context}\n{web_context}\n{rag_context}{web_instruction}".strip()

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

            # Phase 2: Voting and Scoring (Ranking)
            self.log("Ranking responses based on Accuracy, Relevance, and Clarity...")
            consensus_mgr = ConsensusManager(active_agents)
            scored_outputs = await consensus_mgr.run_voting_round(valid_outputs)
            
            # Sort outputs by average score to show ranking
            scored_outputs.sort(key=lambda x: x.scores.average, reverse=True)
            
            for i, o in enumerate(scored_outputs):
                self.log(f"  - Rank {i+1}: {o.agent_id} | Score: [bold]{o.scores.average:.2f}[/]")

            self.current_session.outputs.extend(scored_outputs)

            # Phase 3: Hallucination Check
            self.log("Performing hallucination checks on the highest-ranked output...")
            # Use the best agent for checking
            best_output = scored_outputs[0]
            checker_agent = next(a for a in active_agents if a.agent_id == best_output.agent_id)
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
