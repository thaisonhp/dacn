import os
from typing import List, Dict
from dotenv import load_dotenv
from models.parser import MarkItDownParser
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Qdrant
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import models
from core.config import settings
from uuid import uuid4
from fastembed import TextEmbedding, LateInteractionTextEmbedding, SparseTextEmbedding
from utils.manage_collection.collection_manager import CollectionManager
from modules.models.indexing.chunker import MarkdownChunker
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType
from core.config import graphiti
from datetime import datetime ,timezone

import json 
load_dotenv()


class Indexer:
    def __init__(self, collection_name: str = None):
        self.parser = MarkItDownParser()
        # self.text_splitter = RecursiveCharacterTextSplitter(
        #     chunk_size=512, chunk_overlap=50, length_function=len, add_start_index=True
        # )
        self.text_splitter = MarkdownChunker()
        # self.client = client
        self.collection_name = collection_name or settings.collection_name

        self.collection = None  # de chon ra collection de lam viec

        # self.collection_manager = CollectionManager(self.client, self.collection_name)
        # khoi tao cac vector embedding models phuc vu cho  hybrid search + rerank
        dense_embedding_model = TextEmbedding(settings.dense_model_name)
        self.embedding_model = dense_embedding_model
        bm25_embedding_model = SparseTextEmbedding(settings.bm25_embedding_model)
        self.sparse_embedding_model = bm25_embedding_model
        late_interaction_embedding_model = LateInteractionTextEmbedding(
            settings.late_model_name
        )
        self.late_interaction_embedding_model = late_interaction_embedding_model

    async def indexing(self, file_path: str):
        parsed = self.parser.parse(file_path)
        print("Parsed",parsed)
        chunks = self.text_splitter.chunk(parsed["text"], source_file=file_path)
        documents = [
            {
                "text": chunk.text,
                "metadata": {
                    "heading": chunk.heading,
                    "source": chunk.file,
                    **parsed["metadata"],
                },
            }
            for chunk in chunks
        ]
        print(documents[:2])  # Show first 2 documents for debugging

        episodes = []
        for i, text in enumerate(documents):
            episodes.append({
                'content':{
                    "name":f"chunk {i}",
                    "episode_body": text,
                    "source_description": "mp ta ma nguon ",
                },
                'type': EpisodeType.json,
                'description': 'podcast metadata',
            })
        print(episodes)
        for i, episode in enumerate(episodes):
            await graphiti.add_episode(
                name=f'Freakonomics Radio {i}',
                episode_body=json.dumps(episode['content']),
                source=episode['type'],
                source_description=episode['description'],
                reference_time=datetime.now(timezone.utc),
            )
            print(f'Added episode {i}')
        return len(documents)


    async def search(self, query: str, limit: int = 5):
        results = await graphiti.search(query , num_results=limit) # HYBIRD SEARCH + RANK :RRF 
        return results
