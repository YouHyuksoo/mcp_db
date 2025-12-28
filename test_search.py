"""
생산계획 관련 테이블 검색 테스트
"""
import sys
from pathlib import Path

project_root = Path(r"d:\Project\mcp_db")
sys.path.insert(0, str(project_root))

from sentence_transformers import SentenceTransformer
import chromadb

query = "당일 생산계획조회"
database_sid = "SMVNPDBext"
schema_name = "INFINITY21_JSMES"

print(f"=" * 70)
print(f"🔍 자연어 검색 테스트: '{query}'")
print(f"=" * 70)

# Vector DB 연결
persist_directory = str(project_root / "data" / "vector_db")
client = chromadb.PersistentClient(path=persist_directory)
collection = client.get_collection("oracle_metadata")

# 먼저 PLAN 관련 테이블 목록 확인
all_data = collection.get(
    where={
        "$and": [
            {"database_sid": {"$eq": database_sid}},
            {"schema_name": {"$eq": schema_name}}
        ]
    }
)

print(f"\n📊 'PLAN' 또는 'PRODUCT' 포함 테이블:")
print("-" * 70)
plan_tables = []
for id_, meta in zip(all_data['ids'], all_data['metadatas']):
    table_name = meta.get('table_name', id_.split(':')[-1])
    if 'PLAN' in table_name.upper() or 'PRODUCT' in table_name.upper():
        plan_tables.append((table_name, meta.get('table_comment', '')))

for i, (name, desc) in enumerate(plan_tables[:20], 1):
    print(f"{i:2d}. {name}")
    if desc:
        print(f"    └─ {desc[:60]}...")

print(f"\n총 {len(plan_tables)}개 테이블 발견")

# 임베딩 모델로 검색
print(f"\n" + "=" * 70)
print(f"🔎 시맨틱 검색 결과 (상위 10개)")
print("-" * 70)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
query_embedding = model.encode(query).tolist()

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10,
    where={
        "$and": [
            {"database_sid": {"$eq": database_sid}},
            {"schema_name": {"$eq": schema_name}}
        ]
    },
    include=["documents", "metadatas", "distances"]
)

for i, (id_, meta, dist) in enumerate(zip(
    results['ids'][0],
    results['metadatas'][0],
    results['distances'][0]
), 1):
    table_name = meta.get('table_name', id_.split(':')[-1])
    # L2 거리를 유사도 점수로 변환 (더 작은 거리 = 더 유사)
    score = max(0, 1 / (1 + dist))
    print(f"{i:2d}. {table_name:45s} (점수: {score:.3f})")

print(f"\n" + "=" * 70)
