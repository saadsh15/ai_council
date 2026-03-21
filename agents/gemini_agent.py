import httpx
import json
import uuid
import os
from typing import List, Optional
from agents.base_agent import BaseAgent
from utils.models import Output, Scores, AgentStatus
from datetime import datetime
from storage.config import get_api_key

class GeminiAgent(BaseAgent):
    def __init__(self, agent_id: str, model: str = "gemini-1.5-flash"):
        super().__init__(agent_id, model, "gemini")
        self.api_key = get_api_key("gemini")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(self, prompt: str, context: Optional[str] = None) -> Output:
        if not self.api_key:
            raise ValueError(f"API key for {self.provider} not found.")

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        full_prompt = (
            "You are a specialized research agent. Provide a detailed, fact-based response. "
            "You MUST include verifiable sources and citations for all claims. "
            "State your confidence level (0.0 to 1.0) at the end of your response in the format: "
            "CONFIDENCE: <score>\n\n"
            f"QUERY: {prompt}"
        )

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}]
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data['candidates'][0]['content']['parts'][0]['text']

        confidence = 0.8
        if "CONFIDENCE:" in content:
            try:
                conf_str = content.split("CONFIDENCE:")[1].strip().split()[0]
                confidence = float(conf_str)
            except:
                pass

        import re
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

        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
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
            "contents": [{"parts": [{"text": eval_prompt}]}],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            eval_data = json.loads(data['candidates'][0]['content']['parts'][0]['text'])
            
            return Scores(
                accuracy=eval_data.get('accuracy', 0.0),
                completeness=eval_data.get('completeness', 0.0),
                source_quality=eval_data.get('source_quality', 0.0),
                clarity=eval_data.get('clarity', 0.0),
                average=eval_data.get('average', 0.0)
            )
