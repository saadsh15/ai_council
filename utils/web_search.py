import asyncio
from typing import List, Dict
from duckduckgo_search import DDGS

class WebSearcher:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    async def search(self, query: str) -> List[Dict]:
        """Perform a web search for a given query."""
        try:
            # Wrap synchronous DDGS in a thread for async compatibility
            results = await asyncio.to_thread(self._do_search, query)
            return results
        except Exception as e:
            print(f"Web Search Error: {e}")
            return []

    def _do_search(self, query: str) -> List[Dict]:
        """Synchronous part of the search."""
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=self.max_results))
            return [
                {
                    "title": r.get('title', ''),
                    "snippet": r.get('body', ''),
                    "link": r.get('href', '')
                } for r in results
            ]

def format_search_results(results: List[Dict]) -> str:
    """Format search results for injection into the prompt."""
    if not results:
        return "No web search results found."
        
    formatted = "LATEST WEB SEARCH RESEARCH RESULTS:\n"
    for i, res in enumerate(results):
        formatted += f"{i+1}. {res['title']}\n"
        formatted += f"   Source: {res['link']}\n"
        formatted += f"   Snippet: {res['snippet']}\n\n"
    return formatted
