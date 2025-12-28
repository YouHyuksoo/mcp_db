#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Vector DB 데이터 확인"""

import sys
import os
import logging

os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")
logging.basicConfig(level=logging.ERROR)
logging.getLogger("chromadb").setLevel(logging.ERROR)

try:
    import chromadb
    from chromadb.config import Settings
    
    client = chromadb.PersistentClient(
        path="data/vector_db",
        settings=Settings(anonymized_telemetry=False)
    )
    
    print("=" * 60)
    print("Vector DB 데이터 확인")
    print("=" * 60)
    
    # oracle_metadata 컬렉션 확인
    try:
        coll = client.get_collection("oracle_metadata")
        count = coll.count()
        print(f"\noracle_metadata 컬렉션:")
        print(f"  총 아이템 수: {count}")
        
        if count > 0:
            print(f"\n  ✅ 데이터가 있습니다!")
            # 샘플 데이터 조회
            sample = coll.get(limit=5)
            print(f"\n  샘플 데이터 (최대 5개):")
            for i, table_id in enumerate(sample["ids"], 1):
                meta = sample["metadatas"][i-1] if sample["metadatas"] else {}
                print(f"\n  {i}. {table_id}")
                print(f"     - database_sid: {meta.get('database_sid', 'N/A')}")
                print(f"     - schema_name: {meta.get('schema_name', 'N/A')}")
                print(f"     - table_name: {meta.get('table_name', 'N/A')}")
                print(f"     - korean_name: {meta.get('korean_name', 'N/A')}")
        else:
            print(f"\n  ❌ 데이터가 없습니다!")
            print(f"     → CSV 파일을 업로드하여 데이터를 학습시켜야 합니다.")
            print(f"     → Backend Web UI: http://localhost:3000/upload")
        
    except Exception as e:
        print(f"\n  ❌ 컬렉션을 찾을 수 없습니다: {e}")
    
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"❌ 오류: {e}")
    import traceback
    traceback.print_exc()

