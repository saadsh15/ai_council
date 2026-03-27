import asyncio
from typing import List, Dict
from duckduckgo_search import DDGS

class WebSearcher:
    def __init__(self, max_results: int = 5):
        self.max_results = max_results

    async def search(self, query: str) -> List[Dict]:
        """Perform a web search for a given query."""
        try:
            results = await asyncio.to_thread(self._do_search, query)
            return results
        except Exception as e:
            print(f"Web Search Error: {e}")
            return []

    async def search_news(self, query: str) -> List[Dict]:
        """Perform a news search for a given query."""
        try:
            results = await asyncio.to_thread(self._do_news_search, query)
            return results
        except Exception as e:
            print(f"News Search Error: {e}")
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

    def _do_news_search(self, query: str) -> List[Dict]:
        """Synchronous part of the news search."""
        with DDGS() as ddgs:
            results = list(ddgs.news(query, max_results=self.max_results))
            return [
                {
                    "title": r.get('title', ''),
                    "snippet": r.get('body', ''),
                    "link": r.get('url', ''),
                    "source": r.get('source', ''),
                    "date": r.get('date', '')
                } for r in results
            ]

def format_search_results(results: List[Dict], news_results: List[Dict] = None) -> str:
    """Format search and news results for injection into the prompt."""
    formatted = ""
    
    if news_results:
        formatted += "LATEST RELEVANT NEWS ARTICLES:\n"
        for i, res in enumerate(news_results):
            formatted += f"{i+1}. {res['title']}\n"
            formatted += f"   Source: {res['source']} | Date: {res['date']}\n"
            formatted += f"   URL: {res['link']}\n"
            formatted += f"   Snippet: {res['snippet']}\n\n"

    if results:
        formatted += "LATEST WEB SEARCH RESEARCH RESULTS:\n"
        for i, res in enumerate(results):
            formatted += f"{i+1}. {res['title']}\n"
            formatted += f"   Source: {res['link']}\n"
            formatted += f"   Snippet: {res['snippet']}\n\n"
            
    return formatted or "No research results found."
