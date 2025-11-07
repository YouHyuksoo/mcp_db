"""
Embedding Service
Converts text to vector embeddings using sentence-transformers
"""

from sentence_transformers import SentenceTransformer
from typing import List, Union
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Text to vector embedding service"""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding model

        Args:
            model_name: Name of the sentence-transformers model
                       Default: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
                       Alternatives:
                       - all-mpnet-base-v2 (768 dim, better quality, slower)
                       - paraphrase-multilingual-MiniLM-L12-v2 (384 dim, multilingual)
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")

        try:
            self.model = SentenceTransformer(model_name)
            self.embedding_dim = self.model.get_sentence_embedding_dimension()
            logger.info(f"✓ Embedding model loaded (dimension: {self.embedding_dim})")
        except Exception as e:
            logger.error(f"✗ Failed to load embedding model: {e}")
            raise

    def embed_text(self, text: str) -> List[float]:
        """
        Convert single text to embedding

        Args:
            text: Input text

        Returns:
            List of floats representing the embedding
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.embedding_dim

        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        Convert multiple texts to embeddings (more efficient than one-by-one)

        Args:
            texts: List of input texts
            batch_size: Batch size for encoding (default: 32)

        Returns:
            List of embeddings
        """
        if not texts:
            return []

        # Filter out empty texts and track indices
        non_empty_texts = []
        non_empty_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text)
                non_empty_indices.append(i)

        # Initialize result with zero vectors
        result = [[0.0] * self.embedding_dim for _ in texts]

        if non_empty_texts:
            # Encode non-empty texts
            embeddings = self.model.encode(
                non_empty_texts,
                batch_size=batch_size,
                convert_to_numpy=True,
                show_progress_bar=len(non_empty_texts) > 100
            )

            # Place embeddings at correct indices
            for i, embedding in enumerate(embeddings):
                original_index = non_empty_indices[i]
                result[original_index] = embedding.tolist()

        return result

    def embed_table_summary(
        self,
        table_name: str,
        table_description: str,
        column_descriptions: List[str]
    ) -> List[float]:
        """
        Create embedding for table metadata (optimized for Stage 1)

        Args:
            table_name: Name of the table
            table_description: Korean/English description
            column_descriptions: List of column descriptions

        Returns:
            Embedding vector
        """
        # Combine all information into a rich summary
        summary_parts = [
            f"Table: {table_name}",
            f"Description: {table_description}"
        ]

        if column_descriptions:
            # Limit to top 10 most important columns to avoid too long text
            top_columns = column_descriptions[:10]
            summary_parts.append("Columns: " + ", ".join(top_columns))

        summary_text = "\n".join(summary_parts)
        return self.embed_text(summary_text)

    def embed_sql_pattern(self, question: str, sql_query: str) -> List[float]:
        """
        Create embedding for SQL pattern (question + SQL)

        Args:
            question: Natural language question
            sql_query: SQL query

        Returns:
            Embedding vector
        """
        # We primarily embed the question (since that's what we'll search)
        # But include SQL keywords for context
        pattern_text = f"{question}\nSQL: {sql_query}"
        return self.embed_text(pattern_text)

    def calculate_similarity(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray]
    ) -> float:
        """
        Calculate cosine similarity between two embeddings

        Args:
            embedding1: First embedding
            embedding2: Second embedding

        Returns:
            Similarity score (0-1, higher = more similar)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = dot_product / (norm1 * norm2)
        return float(similarity)

    def get_model_info(self) -> dict:
        """Get model information"""
        return {
            "model_name": self.model_name,
            "embedding_dimension": self.embedding_dim,
            "max_seq_length": self.model.max_seq_length
        }
