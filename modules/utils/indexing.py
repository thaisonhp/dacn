from utils.processor.indexer import Indexer


class IndexingPipeline:
    def __init__(self , collection_name: str = None):
        self.indexer = Indexer(collection_name=collection_name)

    async def add_file(self, file_path: str):
        return await self.indexer.indexing(file_path)