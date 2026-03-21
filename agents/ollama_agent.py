import httpx
import json
import uuid
from typing import List, Optional
from agents.base_agent import BaseAgent
from utils.models import Output, Scores, AgentStatus
from datetime import datetime

class OllamaAgent(BaseAgent):
    def __init__(self, agent_id: str, model: str = "qwen3-coder:30b", base_url: str = "http://localhost:11434"):
        super().__init__(agent_id, model, "ollama")
        self.base_url = base_url

    async def generate(self, prompt: str, context: Optional[str] = None) -> Output:
        """Generate research output for a given prompt."""
        url = f"{self.base_url}/api/chat"
        
        system_msg = (
            "You are a specialized research agent. Provide a detailed, fact-based response. "
            "You MUST include verifiable sources and citations for all claims. "
            "State your confidence level (0.0 to 1.0) at the end of your response in the format: "
            "CONFIDENCE: <score>"
        )
        
        user_content = ""
        if context:
            user_content += f"--- RESEARCH CONTEXT ---\n{context}\n\n"
        
        user_content += f"--- RESEARCH QUERY ---\n{prompt}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_content}
            ],
            "stream": False,
            "options": {
                "num_ctx": 8192  # Reduced to 8k for better stability on 30b models
            }
        }

        async with httpx.AsyncClient(timeout=300.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('error', response.text)
                    except:
                        pass
                    raise Exception(f"Ollama Error {response.status_code}: {error_detail}")
                
                data = response.json()
                content = data['message']['content']
            except httpx.TimeoutException:
                raise Exception(f"Ollama Timeout: The model {self.model} took too long to respond (300s).")
            except httpx.ConnectError:
                raise Exception(f"Ollama Connection Error: Is Ollama running at {self.base_url}?")
            except Exception as e:
                raise Exception(f"Ollama generation error ({self.model}): {str(e)}")

        # Parse confidence score if available
        confidence = 0.7 # Default
        if "CONFIDENCE:" in content:
            try:
                conf_str = content.split("CONFIDENCE:")[1].strip().split()[0]
                confidence = float(conf_str)
            except:
                pass

        # Extract sources (look for URLs)
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
        """Evaluate another agent's output for consensus/voting."""
        url = f"{self.base_url}/api/chat"
        
        system_msg = "You are an expert research critic. Respond ONLY with JSON."
        
        eval_content = (
            "Evaluate the following research output based on:\n"
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
                {"role": "system", "content": system_msg},
                {"role": "user", "content": eval_content}
            ],
            "stream": False,
            "format": "json",
            "options": {
                "num_ctx": 8192
            }
        }

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")
                data = response.json()
            except Exception as e:
                # Log to researcher output specifically for deliberation failures
                print(f"Evaluation error ({self.model}): {e}")
                return Scores(average=0.1)
            
            # Robust JSON parsing
            content = data['message']['content']
            try:
                # Sometimes Ollama might return text around the JSON or non-standard format
                if "{" in content and "}" in content:
                    json_str = content[content.find("{"):content.rfind("}")+1]
                    eval_data = json.loads(json_str)
                else:
                    eval_data = json.loads(content)
            except Exception as e:
                # Fallback to low score if JSON fails
                return Scores(accuracy=0.1, completeness=0.1, source_quality=0.1, clarity=0.1, average=0.1)
            
            return Scores(
                accuracy=eval_data.get('accuracy', 0.1),
                completeness=eval_data.get('completeness', 0.1),
                source_quality=eval_data.get('source_quality', 0.1),
                clarity=eval_data.get('clarity', 0.1),
                average=eval_data.get('average', 0.1)
            )
