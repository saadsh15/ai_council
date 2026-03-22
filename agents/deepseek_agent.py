import httpx
import json
import re
import uuid
from typing import List, Optional
from agents.base_agent import BaseAgent
from utils.models import Output, Scores, AgentStatus
from datetime import datetime
from storage.config import get_api_key
from utils.retry import retry_async

class DeepSeekAgent(BaseAgent):
    def __init__(self, agent_id: str, model: str = "deepseek-chat",
                 generate_timeout: float = 300.0, evaluate_timeout: float = 120.0):
        super().__init__(agent_id, model, "deepseek", generate_timeout=generate_timeout, evaluate_timeout=evaluate_timeout)
        self.api_key = get_api_key("deepseek")
        self.base_url = "https://api.deepseek.com/v1/chat/completions"

    async def generate(self, prompt: str, context: Optional[str] = None) -> Output:
        """Generate research output for a given prompt."""
        if not self.api_key:
            raise ValueError(f"API key for {self.provider} not found. Please set DEEPSEEK_API_KEY.")

        full_prompt = (
            "You are a specialized research agent. Provide a detailed, fact-based response. "
            "You MUST include verifiable sources and citations for all claims. "
            "State your confidence level (0.0 to 1.0) at the end of your response in the format: "
            "CONFIDENCE: <score>\n\n"
        )
        
        if context:
            full_prompt += f"CONTEXT (Use this for research and tailoring):\n{context}\n\n"

        full_prompt += f"QUERY: {prompt}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a specialized research agent."},
                {"role": "user", "content": full_prompt}
            ],
            "stream": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async def _do_request():
            async with httpx.AsyncClient(timeout=self.generate_timeout) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        data = await retry_async(_do_request)
        content = data['choices'][0]['message']['content']

        # Parse confidence score if available
        confidence = 0.85 # Default
        if "CONFIDENCE:" in content:
            try:
                conf_str = content.split("CONFIDENCE:")[1].strip().split()[0]
                confidence = float(conf_str)
            except (ValueError, IndexError):
                pass

        # Extract sources (look for URLs)
        sources = re.findall(r'https?://\S+', content)

        return Output(
            output_id=str(uuid.uuid4()),
            agent_id=self.agent_id,
            content=content,
            sources=list(set(sources)),
            confidence=confidence,
            timestamp=datetime.utcnow()
        )

    async def evaluate(self, other_output: Output) -> Scores:
        """Evaluate another agent's output for consensus/voting."""
        if not self.api_key:
            raise ValueError(f"API key for {self.provider} not found.")

        eval_prompt = (
            "You are an expert critic. Evaluate the following research output based on: "
            "1. Accuracy (factual correctness)\n"
            "2. Completeness (coverage of topic)\n"
            "3. Source Quality (verifiability of citations)\n"
            "4. Clarity (readability and logic)\n\n"
            "Output MUST be in JSON format with keys: 'accuracy', 'completeness', 'source_quality', 'clarity' "
            "(scores from 0.0 to 1.0) and an 'average' score.\n\n"
            f"OUTPUT TO EVALUATE:\n{other_output.content}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert critic. Respond ONLY with JSON."},
                {"role": "user", "content": eval_prompt}
            ],
            "stream": False,
            "response_format": {"type": "json_object"}
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        async def _do_request():
            async with httpx.AsyncClient(timeout=self.evaluate_timeout) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        data = await retry_async(_do_request)
        content = data['choices'][0]['message']['content']
        eval_data = json.loads(content)

        return Scores(
            accuracy=eval_data.get('accuracy', 0.1),
            completeness=eval_data.get('completeness', 0.1),
            source_quality=eval_data.get('source_quality', 0.1),
            clarity=eval_data.get('clarity', 0.1),
            average=eval_data.get('average', 0.1)
        )
