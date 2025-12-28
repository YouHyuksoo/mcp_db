#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Vector DB 컬렉션 상태 확인"""

import sys
import os

# ChromaDB telemetry 비활성화
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")

# 로깅 최소화
import logging
logging.basicConfig(level=logging.ERROR)
logging.getLogger("chromadb").setLevel(logging.ERROR)

try:
    import chromadb
    from chromadb.config import Settings
    
    print("=" * 60)
    print("Vector DB 상태 확인")
    print("=" * 60)
    sys.stdout.flush()
    
    client = chromadb.PersistentClient(
        path="data/vector_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    # 모든 컬렉션 목록
    collections = client.list_collections()
    print(f"\n총 컬렉션 수: {len(collections)}")
    sys.stdout.flush()
    
    if len(collections) == 0:
        print("\n❌ 컬렉션이 없습니다!")
        print("   Backend 서버를 실행하여 컬렉션을 생성해야 합니다.")
    else:
        print("\n컬렉션 목록:")
        for c in collections:
            count = c.count()
            print(f"  - {c.name}: {count} items")
    
    # oracle_metadata 컬렉션 확인
    print("\n" + "-" * 60)
    print("oracle_metadata 컬렉션 확인:")
    try:
        metadata_coll = client.get_collection("oracle_metadata")
        count = metadata_coll.count()
        print(f"  ✅ 존재함: {count} items")
        
        if count > 0:
            # 샘플 데이터 확인
            sample = metadata_coll.get(limit=1)
            if sample["ids"]:
                print(f"\n  샘플 ID: {sample['ids'][0]}")
                if sample["metadatas"]:
                    meta = sample["metadatas"][0]
                    print(f"  - database_sid: {meta.get('database_sid', 'N/A')}")
                    print(f"  - schema_name: {meta.get('schema_name', 'N/A')}")
                    print(f"  - table_name: {meta.get('table_name', 'N/A')}")
        else:
            print("  ⚠️ 컬렉션은 있지만 데이터가 없습니다.")
            
    except Exception as e:
        print(f"  ❌ 존재하지 않음: {type(e).__name__}: {e}")
        print("  → Backend 서버를 실행하여 컬렉션을 생성해야 합니다.")
    
    print("\n" + "=" * 60)
    sys.stdout.flush()
    
except Exception as e:
    print(f"\n❌ Vector DB 연결 실패: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()
