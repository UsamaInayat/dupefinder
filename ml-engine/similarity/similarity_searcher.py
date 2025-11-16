"""
DupeFinder ML Engine - Similarity Search Module
Task 2.4: Implement similarity calculation and search

This module handles:
- Computing cosine similarity between embeddings
- Finding top-K most similar items
- Efficient search across product catalog
- Filtering by categories and thresholds
"""

import numpy as np
from scipy.spatial.distance import cosine, cdist
from typing import List, Tuple, Dict, Union, Optional
from pathlib import Path
import pickle
import time


class SimilaritySearcher:
    """
    Searches for similar items using cosine similarity on embeddings.
    
    Uses numpy/scipy for efficient similarity computation. Can be upgraded
    to FAISS for large-scale datasets (60% milestone).
    """
    
    def __init__(
        self,
        embeddings: np.ndarray = None,
        metadata: List[Dict] = None,
        metric: str = 'cosine'
    ):
        """
        Initialize the similarity searcher.
        
        Args:
            embeddings: Numpy array of shape (N, D) where N=number of items, D=embedding dimension
            metadata: List of dictionaries containing item metadata (paths, ids, categories, etc.)
            metric: Distance metric ('cosine', 'euclidean', 'manhattan')
        """
        self.embeddings = embeddings
        self.metadata = metadata or []
        self.metric = metric
        self.num_items = len(embeddings) if embeddings is not None else 0
        
        if embeddings is not None:
            print(f"[INFO] SimilaritySearcher initialized with {self.num_items} items")
            print(f"[INFO] Embedding dimension: {embeddings.shape[1]}")
            print(f"[INFO] Distance metric: {metric}")
    
    def add_items(
        self,
        embeddings: np.ndarray,
        metadata: List[Dict] = None
    ):
        """
        Add items to the search index.
        
        Args:
            embeddings: Numpy array of embeddings to add
            metadata: List of metadata dictionaries for each embedding
        """
        if self.embeddings is None:
            self.embeddings = embeddings
            self.metadata = metadata or []
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])
            if metadata:
                self.metadata.extend(metadata)
        
        self.num_items = len(self.embeddings)
        print(f"[INFO] Added items. Total items: {self.num_items}")
    
    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        target_embedding: np.ndarray
    ) -> float:
        """
        Compute similarity between two embeddings.
        
        Args:
            query_embedding: Query embedding vector
            target_embedding: Target embedding vector
        
        Returns:
            Similarity score (higher = more similar)
            - Cosine: [0, 1] where 1 is identical
            - Euclidean/Manhattan: distance (lower = more similar)
        """
        if self.metric == 'cosine':
            # Cosine similarity: 1 - cosine_distance
            return 1 - cosine(query_embedding, target_embedding)
        elif self.metric == 'euclidean':
            return -np.linalg.norm(query_embedding - target_embedding)
        elif self.metric == 'manhattan':
            return -np.sum(np.abs(query_embedding - target_embedding))
        else:
            raise ValueError(f"Unsupported metric: {self.metric}")
    
    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = None,
        return_scores: bool = True
    ) -> Union[List[int], List[Tuple[int, float]]]:
        """
        Search for most similar items to the query embedding.
        
        Args:
            query_embedding: Query embedding vector of shape (D,)
            top_k: Number of top similar items to return
            threshold: Minimum similarity threshold (optional)
            return_scores: Whether to return similarity scores along with indices
        
        Returns:
            List of indices (if return_scores=False) or list of (index, score) tuples
        """
        if self.embeddings is None or self.num_items == 0:
            raise ValueError("No items in the search index. Use add_items() first.")
        
        # Ensure query is 1D
        if query_embedding.ndim > 1:
            query_embedding = query_embedding.flatten()
        
        # Compute similarities for all items
        if self.metric == 'cosine':
            # Efficient batch cosine similarity using cdist
            similarities = 1 - cdist(
                query_embedding.reshape(1, -1),
                self.embeddings,
                metric='cosine'
            )[0]
        else:
            # Compute similarity for each item
            similarities = np.array([
                self.compute_similarity(query_embedding, emb)
                for emb in self.embeddings
            ])
        
        # Apply threshold if specified
        if threshold is not None:
            valid_indices = np.where(similarities >= threshold)[0]
            if len(valid_indices) == 0:
                return [] if return_scores else []
            similarities = similarities[valid_indices]
        else:
            valid_indices = np.arange(len(similarities))
        
        # Get top-k indices (sorted by similarity descending)
        top_k = min(top_k, len(similarities))
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        # Map back to original indices
        result_indices = valid_indices[top_indices]
        result_scores = similarities[top_indices]
        
        if return_scores:
            return list(zip(result_indices.tolist(), result_scores.tolist()))
        else:
            return result_indices.tolist()
    
    def search_with_metadata(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        threshold: float = None,
        category_filter: str = None
    ) -> List[Dict]:
        """
        Search and return results with metadata.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            threshold: Minimum similarity threshold
            category_filter: Filter by category (optional)
        
        Returns:
            List of dictionaries with item metadata and similarity scores
        """
        # Apply category filter if specified
        if category_filter and self.metadata:
            # Get indices of items matching category
            filtered_indices = [
                i for i, meta in enumerate(self.metadata)
                if meta.get('category') == category_filter
            ]
            
            if len(filtered_indices) == 0:
                return []
            
            # Search only within filtered items
            filtered_embeddings = self.embeddings[filtered_indices]
            filtered_metadata = [self.metadata[i] for i in filtered_indices]
            
            # Compute similarities
            if self.metric == 'cosine':
                similarities = 1 - cdist(
                    query_embedding.reshape(1, -1),
                    filtered_embeddings,
                    metric='cosine'
                )[0]
            else:
                similarities = np.array([
                    self.compute_similarity(query_embedding, emb)
                    for emb in filtered_embeddings
                ])
            
            # Apply threshold
            if threshold is not None:
                valid_mask = similarities >= threshold
                similarities = similarities[valid_mask]
                filtered_indices = [idx for i, idx in enumerate(filtered_indices) if valid_mask[i]]
                filtered_metadata = [meta for i, meta in enumerate(filtered_metadata) if valid_mask[i]]
            
            # Get top-k
            top_k = min(top_k, len(similarities))
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for i in top_indices:
                result = filtered_metadata[i].copy()
                result['similarity_score'] = float(similarities[i])
                result['index'] = filtered_indices[i]
                results.append(result)
            
            return results
        else:
            # No filtering, search all items
            search_results = self.search(query_embedding, top_k, threshold, return_scores=True)
            
            results = []
            for idx, score in search_results:
                result = self.metadata[idx].copy() if idx < len(self.metadata) else {}
                result['similarity_score'] = float(score)
                result['index'] = int(idx)
                results.append(result)
            
            return results
    
    def save(self, file_path: Union[str, Path]):
        """
        Save the search index to disk.
        
        Args:
            file_path: Path to save the index
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'embeddings': self.embeddings,
            'metadata': self.metadata,
            'metric': self.metric,
            'num_items': self.num_items
        }
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"[INFO] Search index saved to {file_path}")
    
    @staticmethod
    def load(file_path: Union[str, Path]) -> 'SimilaritySearcher':
        """
        Load a search index from disk.
        
        Args:
            file_path: Path to the saved index
        
        Returns:
            SimilaritySearcher instance
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Index file not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            data = pickle.load(f)
        
        searcher = SimilaritySearcher(
            embeddings=data['embeddings'],
            metadata=data.get('metadata', []),
            metric=data.get('metric', 'cosine')
        )
        
        print(f"[INFO] Search index loaded from {file_path}")
        return searcher
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about the search index.
        
        Returns:
            Dictionary with index statistics
        """
        if self.embeddings is None:
            return {'num_items': 0, 'embedding_dim': 0}
        
        stats = {
            'num_items': self.num_items,
            'embedding_dim': self.embeddings.shape[1],
            'metric': self.metric,
            'has_metadata': len(self.metadata) > 0,
            'memory_usage_mb': self.embeddings.nbytes / (1024 * 1024)
        }
        
        # Category distribution if metadata available
        if self.metadata:
            categories = [m.get('category', 'unknown') for m in self.metadata]
            from collections import Counter
            stats['category_distribution'] = dict(Counter(categories))
        
        return stats
    
    def benchmark_search(
        self,
        num_queries: int = 100,
        top_k: int = 5
    ) -> Dict:
        """
        Benchmark search performance.
        
        Args:
            num_queries: Number of random queries to test
            top_k: Number of results per query
        
        Returns:
            Dictionary with benchmark results
        """
        if self.embeddings is None or self.num_items == 0:
            raise ValueError("No items in the search index")
        
        print(f"[INFO] Running benchmark with {num_queries} queries...")
        
        # Generate random query embeddings
        embedding_dim = self.embeddings.shape[1]
        random_queries = np.random.randn(num_queries, embedding_dim)
        
        # Normalize if using cosine similarity
        if self.metric == 'cosine':
            random_queries = random_queries / np.linalg.norm(random_queries, axis=1, keepdims=True)
        
        # Measure search time
        start_time = time.time()
        for query in random_queries:
            self.search(query, top_k=top_k, return_scores=False)
        total_time = time.time() - start_time
        
        avg_time_ms = (total_time / num_queries) * 1000
        queries_per_second = num_queries / total_time
        
        results = {
            'num_queries': num_queries,
            'total_time_sec': total_time,
            'avg_time_ms': avg_time_ms,
            'queries_per_second': queries_per_second,
            'top_k': top_k,
            'num_items_searched': self.num_items
        }
        
        print(f"[INFO] Benchmark complete:")
        print(f"       - Average search time: {avg_time_ms:.2f}ms")
        print(f"       - Queries per second: {queries_per_second:.2f}")
        
        return results


def create_searcher(
    embeddings: np.ndarray,
    metadata: List[Dict] = None,
    metric: str = 'cosine'
) -> SimilaritySearcher:
    """
    Factory function to create a SimilaritySearcher instance.
    
    Args:
        embeddings: Numpy array of embeddings
        metadata: List of metadata dictionaries
        metric: Distance metric to use
    
    Returns:
        SimilaritySearcher instance
    """
    return SimilaritySearcher(embeddings=embeddings, metadata=metadata, metric=metric)


def find_similar_items(
    query_embedding: np.ndarray,
    catalog_embeddings: np.ndarray,
    top_k: int = 5
) -> List[Tuple[int, float]]:
    """
    Quick function to find similar items without creating a searcher instance.
    
    Args:
        query_embedding: Query embedding vector
        catalog_embeddings: Catalog embeddings matrix
        top_k: Number of results to return
    
    Returns:
        List of (index, similarity_score) tuples
    """
    searcher = SimilaritySearcher(embeddings=catalog_embeddings)
    return searcher.search(query_embedding, top_k=top_k, return_scores=True)









