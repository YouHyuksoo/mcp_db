"""
Quick Backend Test Script
Run this to verify the backend is working correctly
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.vector_store import VectorStore
from app.core.embedding_service import EmbeddingService
from app.core.learning_engine import LearningEngine


async def test_vector_store():
    """Test Vector DB initialization"""
    print("\n=== Testing Vector Store ===")
    try:
        vector_store = VectorStore()
        await vector_store.initialize()

        stats = vector_store.get_stats()
        print(f"✓ Vector Store initialized")
        print(f"  - Metadata: {stats['metadata_count']} items")
        print(f"  - Patterns: {stats['patterns_count']} items")
        print(f"  - Business Rules: {stats['business_rules_count']} items")
        return vector_store
    except Exception as e:
        print(f"✗ Vector Store failed: {e}")
        return None


async def test_embedding_service():
    """Test Embedding Service"""
    print("\n=== Testing Embedding Service ===")
    try:
        embedding_service = EmbeddingService()

        # Test single embedding
        test_text = "고객 정보를 조회하는 테이블"
        embedding = embedding_service.embed_text(test_text)

        print(f"✓ Embedding Service initialized")
        print(f"  - Model: {embedding_service.model_name}")
        print(f"  - Dimension: {embedding_service.embedding_dim}")
        print(f"  - Test embedding length: {len(embedding)}")

        return embedding_service
    except Exception as e:
        print(f"✗ Embedding Service failed: {e}")
        return None


async def test_learning_engine(vector_store, embedding_service):
    """Test Learning Engine"""
    print("\n=== Testing Learning Engine ===")

    if not vector_store or not embedding_service:
        print("✗ Skipping (dependencies failed)")
        return

    try:
        learning_engine = LearningEngine(vector_store, embedding_service)

        # Test learning a pattern
        pattern_id = learning_engine.learn_sql_pattern(
            question="최근 1년간 구매한 고객 목록",
            sql_query="SELECT * FROM CUSTOMERS WHERE PURCHASE_DATE > ADD_MONTHS(SYSDATE, -12)",
            database_sid="TEST_DB",
            schema_name="TEST_SCHEMA",
            tables_used=["CUSTOMERS"],
            execution_success=True
        )

        print(f"✓ Learning Engine working")
        print(f"  - Learned pattern: {pattern_id}")

        # Test finding similar pattern
        match = learning_engine.find_similar_pattern(
            question="작년에 구매한 고객 리스트",
            database_sid="TEST_DB",
            schema_name="TEST_SCHEMA",
            similarity_threshold=0.80
        )

        if match:
            print(f"  - Found similar pattern: {match['pattern_id']}")
            print(f"    Similarity: {match['similarity']:.2f}")
        else:
            print(f"  - No similar pattern found (threshold too high)")

        # Get stats
        stats = learning_engine.get_pattern_stats()
        print(f"  - Total patterns: {stats['total_patterns']}")

    except Exception as e:
        print(f"✗ Learning Engine failed: {e}")


async def test_metadata_search(vector_store, embedding_service):
    """Test metadata search"""
    print("\n=== Testing Metadata Search ===")

    if not vector_store or not embedding_service:
        print("✗ Skipping (dependencies failed)")
        return

    try:
        # Add sample metadata
        test_data = [
            {
                "id": "TEST_DB.TEST_SCHEMA.CUSTOMERS",
                "summary": "고객 정보 테이블 (Customer Information Table). 고객 ID, 이름, 주소, 전화번호를 저장합니다.",
                "metadata": {
                    "database_sid": "TEST_DB",
                    "schema_name": "TEST_SCHEMA",
                    "table_name": "CUSTOMERS",
                    "korean_name": "고객",
                    "column_count": 10
                }
            },
            {
                "id": "TEST_DB.TEST_SCHEMA.ORDERS",
                "summary": "주문 정보 테이블 (Order Information Table). 주문 ID, 고객 ID, 주문 날짜, 금액을 저장합니다.",
                "metadata": {
                    "database_sid": "TEST_DB",
                    "schema_name": "TEST_SCHEMA",
                    "table_name": "ORDERS",
                    "korean_name": "주문",
                    "column_count": 8
                }
            }
        ]

        # Add to vector DB
        for item in test_data:
            embedding = embedding_service.embed_text(item["summary"])
            vector_store.add_metadata(
                table_id=item["id"],
                summary_text=item["summary"],
                embedding=embedding,
                metadata=item["metadata"]
            )

        print(f"✓ Added {len(test_data)} test tables")

        # Test search
        question = "고객 정보가 있는 테이블"
        query_embedding = embedding_service.embed_text(question)

        results = vector_store.search_metadata(
            query_embedding=query_embedding,
            n_results=2
        )

        print(f"  - Search: '{question}'")
        print(f"  - Found {len(results['ids'])} results:")
        for i, table_id in enumerate(results['ids']):
            distance = results['distances'][i]
            similarity = max(0, 1 - (distance / 2))
            print(f"    {i+1}. {table_id} (similarity: {similarity:.3f})")

    except Exception as e:
        print(f"✗ Metadata search failed: {e}")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Oracle NL-SQL Backend - Component Tests")
    print("="*60)

    # Test components
    vector_store = await test_vector_store()
    embedding_service = await test_embedding_service()

    if vector_store and embedding_service:
        await test_metadata_search(vector_store, embedding_service)
        await test_learning_engine(vector_store, embedding_service)

    print("\n" + "="*60)
    print("Tests Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Start the FastAPI server: python -m uvicorn app.main:app --reload")
    print("2. Visit Swagger UI: http://localhost:8000/api/docs")
    print("3. Test API endpoints")
    print()


if __name__ == "__main__":
    asyncio.run(main())
