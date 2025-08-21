from utils.processor.indexer import Indexer
from typing import List

class RetrievalPipeline:
    def __init__(self):
        self.indexer = Indexer()

    async def retrieval(self, query: str , limit: int = 5 , knowledge_base_id  : List[str] = None):
        return await self.indexer.search(query=query, limit=limit,knowledge_base_id=knowledge_base_id)