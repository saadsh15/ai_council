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


class ClaudeAgent(BaseAgent):
    def __init__(self, agent_id: str, model: str = "claude-sonnet-4-20250514",
                 generate_timeout: float = 300.0, evaluate_timeout: float = 120.0):
        super().__init__(agent_id, model, "claude", generate_timeout=generate_timeout, evaluate_timeout=evaluate_timeout)
        self.api_key = get_api_key("claude")
        self.base_url = "https://api.anthropic.com/v1/messages"

    async def generate(self, prompt: str, context: Optional[str] = None) -> Output:
        if not self.api_key:
            raise ValueError(f"API key for {self.provider} not found. Please set CLAUDE_API_KEY.")

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
            "max_tokens": 4096,
            "messages": [
                {"role": "user", "content": full_prompt}
            ],
            "system": "You are a specialized research agent."
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        async def _do_request():
            async with httpx.AsyncClient(timeout=self.generate_timeout) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        data = await retry_async(_do_request)
        content = data['content'][0]['text']

        confidence = 0.85
        if "CONFIDENCE:" in content:
            try:
                conf_str = content.split("CONFIDENCE:")[1].strip().split()[0]
                confidence = float(conf_str)
            except (ValueError, IndexError):
                pass

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
            "max_tokens": 1024,
            "messages": [
                {"role": "user", "content": eval_prompt}
            ],
            "system": "You are an expert critic. Respond ONLY with JSON."
        }

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        async def _do_request():
            async with httpx.AsyncClient(timeout=self.evaluate_timeout) as client:
                response = await client.post(self.base_url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        data = await retry_async(_do_request)
        content = data['content'][0]['text']

            # Parse JSON from response (handle markdown code blocks)
            json_str = content
            if "```" in content:
                json_str = content.split("```")[1]
                if json_str.startswith("json"):
                    json_str = json_str[4:]
                json_str = json_str.strip()
            elif "{" in content and "}" in content:
                json_str = content[content.find("{"):content.rfind("}") + 1]

            eval_data = json.loads(json_str)

            return Scores(
                accuracy=eval_data.get('accuracy', 0.1),
                completeness=eval_data.get('completeness', 0.1),
                source_quality=eval_data.get('source_quality', 0.1),
                clarity=eval_data.get('clarity', 0.1),
                average=eval_data.get('average', 0.1)
            )
