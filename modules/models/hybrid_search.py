from qdrant_client import QdrantClient, models
from core.config import settings


class HybridSearcher:
    DENSE_MODEL = settings.dense_model_name
    SPARSE_MODEL = settings.sparse_model_name

    def __init__(self, collection_name):
        self.collection_name = collection_name
        self.qdrant_client = QdrantClient()

    def search(self, text: str):
        search_result = self.qdrant_client.query_points(
            collection_name=self.collection_name,
            query=models.FusionQuery(
                fusion=models.Fusion.RRF  # we are using reciprocal rank fusion here
            ),
            prefetch=[
                models.Prefetch(
                    query=models.Document(text=text, model=self.DENSE_MODEL),
                    using=self.DENSE_MODEL,
                ),
                models.Prefetch(
                    query=models.Document(text=text, model=self.SPARSE_MODEL),
                    using=self.SPARSE_MODEL,
                ),
            ],
            query_filter=None,  # If you don't want any filters for now
            limit=5,  # 5 the closest results
        ).points
        # `search_result` contains models.QueryResponse structure
        # We can access list of scored points with the corresponding similarity scores,
        # vectors (if `with_vectors` was set to `True`), and payload via `points` attribute.

        # Select and return metadata
        metadata = [point.payload for point in search_result]
        return metadata
