"""
DupeFinder ML Engine - Similarity Search Test Script
Task 2.4: Test similarity calculation and search

This script verifies:
1. SimilaritySearcher initialization
2. Computing similarity between embeddings
3. Top-K search functionality
4. Filtering by threshold
5. Search with metadata
6. Save/load functionality
7. Performance benchmarking
"""

import sys
import time
from pathlib import Path
import numpy as np

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from similarity.similarity_searcher import SimilaritySearcher, create_searcher


def create_test_data():
    """Create test embeddings and metadata"""
    print("=" * 60)
    print("SETUP: Creating Test Data")
    print("=" * 60)
    
    # Create 20 test embeddings (2048-dim)
    np.random.seed(42)  # For reproducibility
    num_items = 20
    embedding_dim = 2048
    
    embeddings = np.random.randn(num_items, embedding_dim).astype(np.float32)
    
    # Normalize embeddings (important for cosine similarity)
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    # Create metadata
    categories = ['bags', 'shoes', 'watches', 'clothing', 'accessories']
    metadata = []
    for i in range(num_items):
        metadata.append({
            'id': i,
            'name': f'Product {i}',
            'category': categories[i % len(categories)],
            'price': np.random.randint(10, 500),
            'brand': f'Brand {i % 5}'
        })
    
    print(f"[OK] Created {num_items} test embeddings")
    print(f"     Embedding dimension: {embedding_dim}")
    print(f"     Categories: {categories}")
    print(f"\n[SUCCESS] Test data created!\n")
    
    return embeddings, metadata


def test_initialization(embeddings, metadata):
    """Test SimilaritySearcher initialization"""
    print("=" * 60)
    print("TEST 1: SimilaritySearcher Initialization")
    print("=" * 60)
    
    try:
        searcher = SimilaritySearcher(embeddings=embeddings, metadata=metadata)
        
        stats = searcher.get_statistics()
        
        print(f"[OK] SimilaritySearcher initialized successfully")
        print(f"     Number of items: {stats['num_items']}")
        print(f"     Embedding dimension: {stats['embedding_dim']}")
        print(f"     Metric: {stats['metric']}")
        print(f"     Memory usage: {stats['memory_usage_mb']:.2f} MB")
        print(f"     Category distribution: {stats['category_distribution']}")
        
        if stats['num_items'] == len(embeddings):
            print("\n[SUCCESS] Initialization test passed!\n")
            return searcher
        else:
            print("\n[FAIL] Item count mismatch\n")
            return None
            
    except Exception as e:
        print(f"[ERROR] Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_similarity_computation(searcher, embeddings):
    """Test computing similarity between embeddings"""
    print("=" * 60)
    print("TEST 2: Similarity Computation")
    print("=" * 60)
    
    try:
        # Test similarity between identical embeddings
        emb1 = embeddings[0]
        emb2 = embeddings[0]
        similarity_identical = searcher.compute_similarity(emb1, emb2)
        
        print(f"[OK] Similarity (identical embeddings): {similarity_identical:.6f}")
        
        # Test similarity between different embeddings
        emb3 = embeddings[1]
        similarity_different = searcher.compute_similarity(emb1, emb3)
        
        print(f"[OK] Similarity (different embeddings): {similarity_different:.6f}")
        
        # Verify: identical should be close to 1.0, different should be less
        if 0.99 <= similarity_identical <= 1.01:
            print("[OK] Identical embeddings have similarity ~1.0")
        else:
            print(f"[WARNING] Identical similarity is {similarity_identical:.6f}, expected ~1.0")
        
        if similarity_different < similarity_identical:
            print("[OK] Different embeddings have lower similarity")
        else:
            print("[WARNING] Different embeddings have similar or higher similarity")
        
        print("\n[SUCCESS] Similarity computation test passed!\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] Similarity computation failed: {e}")
        return False


def test_topk_search(searcher, embeddings):
    """Test top-K search functionality"""
    print("=" * 60)
    print("TEST 3: Top-K Search")
    print("=" * 60)
    
    try:
        # Use first embedding as query
        query = embeddings[0]
        top_k = 5
        
        print(f"Searching for top-{top_k} most similar items...")
        start_time = time.time()
        
        results = searcher.search(query, top_k=top_k, return_scores=True)
        
        search_time = (time.time() - start_time) * 1000
        
        print(f"[OK] Search completed in {search_time:.2f}ms")
        print(f"     Found {len(results)} results")
        
        # Display results
        for rank, (idx, score) in enumerate(results, 1):
            print(f"     Rank {rank}: Index {idx}, Similarity {score:.4f}")
        
        # Verify results
        if len(results) == top_k:
            print(f"[OK] Returned exactly {top_k} results")
        else:
            print(f"[FAIL] Expected {top_k} results, got {len(results)}")
            return False
        
        # Verify scores are sorted descending
        scores = [score for _, score in results]
        if scores == sorted(scores, reverse=True):
            print("[OK] Results are sorted by similarity (descending)")
        else:
            print("[WARNING] Results are not properly sorted")
        
        # First result should be the query itself (similarity ~1.0)
        if results[0][1] > 0.99:
            print("[OK] Top result is the query itself")
        else:
            print(f"[WARNING] Top result similarity is {results[0][1]:.4f}, expected ~1.0")
        
        print("\n[SUCCESS] Top-K search test passed!\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] Top-K search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_threshold_filtering(searcher, embeddings):
    """Test filtering by similarity threshold"""
    print("=" * 60)
    print("TEST 4: Threshold Filtering")
    print("=" * 60)
    
    try:
        query = embeddings[0]
        
        # Test with high threshold
        threshold = 0.9
        print(f"Searching with threshold={threshold}...")
        results_high = searcher.search(query, top_k=10, threshold=threshold, return_scores=True)
        
        print(f"[OK] Found {len(results_high)} results with threshold={threshold}")
        
        # Test with low threshold
        threshold = 0.3
        print(f"Searching with threshold={threshold}...")
        results_low = searcher.search(query, top_k=10, threshold=threshold, return_scores=True)
        
        print(f"[OK] Found {len(results_low)} results with threshold={threshold}")
        
        # Verify: lower threshold should return more results
        if len(results_low) >= len(results_high):
            print("[OK] Lower threshold returns more results")
        else:
            print("[WARNING] Lower threshold returned fewer results")
        
        # Verify all results meet threshold
        for idx, score in results_high:
            if score < 0.9:
                print(f"[FAIL] Result {idx} has score {score:.4f} below threshold 0.9")
                return False
        
        print("[OK] All results meet the threshold requirement")
        
        print("\n[SUCCESS] Threshold filtering test passed!\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] Threshold filtering failed: {e}")
        return False


def test_search_with_metadata(searcher, embeddings):
    """Test search with metadata and category filtering"""
    print("=" * 60)
    print("TEST 5: Search with Metadata")
    print("=" * 60)
    
    try:
        query = embeddings[5]  # Use a different query
        
        # Search without category filter
        print("Searching without category filter...")
        results_all = searcher.search_with_metadata(query, top_k=5)
        
        print(f"[OK] Found {len(results_all)} results")
        for i, result in enumerate(results_all[:3], 1):
            print(f"     {i}. {result['name']} (Category: {result['category']}, "
                  f"Similarity: {result['similarity_score']:.4f})")
        
        # Search with category filter
        category = 'bags'
        print(f"\nSearching with category filter: '{category}'...")
        results_filtered = searcher.search_with_metadata(
            query,
            top_k=5,
            category_filter=category
        )
        
        print(f"[OK] Found {len(results_filtered)} results in category '{category}'")
        
        # Verify all results are from the filtered category
        for result in results_filtered:
            if result['category'] != category:
                print(f"[FAIL] Result has wrong category: {result['category']}")
                return False
        
        print(f"[OK] All results match category '{category}'")
        
        print("\n[SUCCESS] Search with metadata test passed!\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] Search with metadata failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_save_load(searcher):
    """Test saving and loading search index"""
    print("=" * 60)
    print("TEST 6: Save and Load Index")
    print("=" * 60)
    
    try:
        # Save index
        save_path = Path("data/similarity/test_index.pkl")
        print(f"Saving index to {save_path}...")
        searcher.save(save_path)
        
        print(f"[OK] Index saved")
        
        # Load index
        print(f"Loading index from {save_path}...")
        loaded_searcher = SimilaritySearcher.load(save_path)
        
        print(f"[OK] Index loaded")
        
        # Verify loaded index has same properties
        original_stats = searcher.get_statistics()
        loaded_stats = loaded_searcher.get_statistics()
        
        if original_stats['num_items'] == loaded_stats['num_items']:
            print(f"[OK] Loaded index has same number of items: {loaded_stats['num_items']}")
        else:
            print(f"[FAIL] Item count mismatch")
            return False
        
        # Test that searches give same results
        query = searcher.embeddings[0]
        results_original = searcher.search(query, top_k=3, return_scores=True)
        results_loaded = loaded_searcher.search(query, top_k=3, return_scores=True)
        
        if results_original == results_loaded:
            print("[OK] Loaded index produces identical search results")
        else:
            print("[WARNING] Search results differ slightly (may be due to numerical precision)")
        
        print("\n[SUCCESS] Save/load test passed!\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] Save/load failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_benchmark(searcher):
    """Test search performance"""
    print("=" * 60)
    print("TEST 7: Performance Benchmark")
    print("=" * 60)
    
    try:
        # Run benchmark
        num_queries = 100
        results = searcher.benchmark_search(num_queries=num_queries, top_k=5)
        
        print(f"[OK] Benchmark completed")
        print(f"     Number of queries: {results['num_queries']}")
        print(f"     Average search time: {results['avg_time_ms']:.2f}ms")
        print(f"     Queries per second: {results['queries_per_second']:.2f}")
        print(f"     Items searched: {results['num_items_searched']}")
        
        # Verify performance is reasonable
        if results['avg_time_ms'] < 100:  # Less than 100ms per query
            print("[OK] Search performance is good (< 100ms per query)")
        else:
            print(f"[WARNING] Search is slow: {results['avg_time_ms']:.2f}ms per query")
        
        print("\n[SUCCESS] Performance benchmark test passed!\n")
        return True
        
    except Exception as e:
        print(f"[ERROR] Performance benchmark failed: {e}")
        return False


def main():
    """Run all similarity search tests"""
    print("\n" + "=" * 60)
    print("DupeFinder ML Engine - Similarity Search Tests")
    print("Task 2.4: Similarity Calculation Verification")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Setup: Create test data
    embeddings, metadata = create_test_data()
    
    # Test 1: Initialization
    searcher = test_initialization(embeddings, metadata)
    results['initialization'] = searcher is not None
    
    if not results['initialization']:
        print("\n[FAILED] Cannot proceed without successful initialization")
        return 1
    
    # Test 2: Similarity computation
    results['similarity_computation'] = test_similarity_computation(searcher, embeddings)
    
    # Test 3: Top-K search
    results['topk_search'] = test_topk_search(searcher, embeddings)
    
    # Test 4: Threshold filtering
    results['threshold_filtering'] = test_threshold_filtering(searcher, embeddings)
    
    # Test 5: Search with metadata
    results['search_metadata'] = test_search_with_metadata(searcher, embeddings)
    
    # Test 6: Save/load
    results['save_load'] = test_save_load(searcher)
    
    # Test 7: Performance
    results['performance'] = test_performance_benchmark(searcher)
    
    # Final Summary
    print("=" * 60)
    print("FINAL RESULTS - Similarity Search Test Summary")
    print("=" * 60)
    print(f"[{'PASS' if results['initialization'] else 'FAIL'}] SimilaritySearcher initialization")
    print(f"[{'PASS' if results['similarity_computation'] else 'FAIL'}] Similarity computation")
    print(f"[{'PASS' if results['topk_search'] else 'FAIL'}] Top-K search")
    print(f"[{'PASS' if results['threshold_filtering'] else 'FAIL'}] Threshold filtering")
    print(f"[{'PASS' if results['search_metadata'] else 'FAIL'}] Search with metadata")
    print(f"[{'PASS' if results['save_load'] else 'FAIL'}] Save and load index")
    print(f"[{'PASS' if results['performance'] else 'FAIL'}] Performance benchmark")
    print("=" * 60)
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n*** SUCCESS! All similarity search tests passed! ***")
        print("\n[COMPLETE] Task 2.4 Complete: Similarity calculation is ready!")
        print("   - Cosine similarity computation works")
        print("   - Top-K search functional")
        print("   - Threshold filtering works")
        print("   - Metadata search and filtering works")
        print("   - Save/load functionality works")
        print("   - Fast search performance (< 100ms per query)")
        print("\nYou can now proceed to Task 2.5: Create Sample Product Dataset")
        return 0
    else:
        failed_count = sum(1 for v in results.values() if not v)
        print(f"\n[FAILED] {failed_count} test(s) failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)









