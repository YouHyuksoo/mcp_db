"""
DB 삭제 기능 테스트
"""
import sys
from pathlib import Path

# 현재 디렉토리를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

import asyncio
from src.mcp_server import delete_database, show_databases

async def test_delete():
    print("=" * 60)
    print("DB 삭제 테스트")
    print("=" * 60)

    # 삭제 전 DB 목록
    print("\n[삭제 전 DB 목록]")
    result = await show_databases()
    print(result[0]['text'])

    # TEST_DB 삭제
    print("\n[TEST_DB 삭제 실행]")
    result = await delete_database("TEST_DB")
    print(result[0]['text'])

    # 삭제 후 DB 목록
    print("\n[삭제 후 DB 목록]")
    result = await show_databases()
    print(result[0]['text'])

if __name__ == "__main__":
    asyncio.run(test_delete())
