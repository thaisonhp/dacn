from utils.processor.indexer import Indexer


class RetrievalPipeline:
    def __init__(self):
        self.indexer = Indexer()

    async def retrieval(self, query: str , limit: int = 5):
        return await self.indexer.search(query=query, limit=limit)