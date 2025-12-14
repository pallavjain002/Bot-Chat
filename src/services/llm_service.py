import httpx
from src.config.settings import settings
from typing import List, Dict, Optional
import json

class LLMService:
    def __init__(self):
        self.api_key = settings.groq_api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"

    async def call_llm(self, messages: List[Dict], context_limit: int = 4000) -> Dict:
        # Trim messages to fit context limit (simple sliding window)
        total_tokens = sum(len(msg['content'].split()) for msg in messages)  # Rough estimate
        while total_tokens > context_limit and len(messages) > 1:
            messages.pop(0)
            total_tokens = sum(len(msg['content'].split()) for msg in messages)

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 1000
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "content": data["choices"][0]["message"]["content"],
                    "tokens_used": data.get("usage", {}).get("total_tokens", 0)
                }
            else:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")

    def retrieve_rag_context(self, query: str, document_chunks: List[str]) -> str:
        # Simple keyword-based retrieval
        query_words = set(query.lower().split())
        relevant_chunks = []
        for chunk in document_chunks:
            chunk_words = set(chunk.lower().split())
            if query_words & chunk_words:  # Intersection
                relevant_chunks.append(chunk)
        return " ".join(relevant_chunks[:3])  # Top 3 chunks