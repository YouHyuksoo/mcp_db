"""
get_table_summaries_for_query 함수 수정 스크립트
"""

import re

# 파일 읽기
with open('d:/Project/mcp_db/src/mcp_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 수정할 부분 찾기
old_code = '''    try:
        summaries = metadata_manager.load_table_summaries(database_sid, schema_name)

        import json
        result_text = f"📊 테이블 요약 정보 (Stage 1)\\n\\n"
        result_text += f"**질문**: {natural_query}\\n\\n"
        result_text += f"**Database**: {database_sid}\\n"
        result_text += f"**Schema**: {schema_name}\\n\\n"
        result_text += "**테이블 목록**:\\n\\n"

        for table_name, summary in summaries.items():
            result_text += f"### {table_name}\\n"
            result_text += f"- **목적**: {summary.get('business_purpose', 'N/A')}\\n"
            result_text += f"- **칼럼 수**: {summary.get('column_count', 0)}\\n"
            result_text += f"- **주요 칼럼**: {', '.join(summary.get('key_columns', []))}\\n"
            result_text += f"- **연관 테이블**: {', '.join(summary.get('related_tables', []))}\\n\\n"

        result_text += "\\n---\\n\\n"
        result_text += "**다음 단계**: 위 테이블들 중에서 질문에 답하기 위해 필요한 테이블(최대 5개)을 선택하고,\\n"
        result_text += "`get_detailed_metadata_for_sql` Tool을 호출하여 상세 메타데이터를 받아 SQL을 생성하세요.\\n"

        return [{"type": "text", "text": result_text}]'''

new_code = '''    try:
        summaries_data = metadata_manager.load_table_summaries(database_sid, schema_name)

        import json
        result_text = f"📊 테이블 요약 정보 (Stage 1)\\n\\n"
        result_text += f"**질문**: {natural_query}\\n\\n"
        result_text += f"**Database**: {database_sid}\\n"
        result_text += f"**Schema**: {schema_name}\\n"
        result_text += f"**전체 테이블 수**: {summaries_data.get('total_tables', 0)}개\\n\\n"
        result_text += "**테이블 목록**:\\n\\n"

        for summary in summaries_data.get('summaries', []):
            result_text += f"### {summary.get('table_name')}\\n"
            result_text += f"- **설명**: {summary.get('one_line_desc', 'N/A')}\\n"
            result_text += f"- **주요 용도**: {summary.get('primary_use', 'N/A')}\\n"
            result_text += f"- **키워드**: {', '.join(summary.get('keywords', []))}\\n\\n"

        result_text += "\\n---\\n\\n"
        result_text += "**다음 단계**: 위 테이블들 중에서 질문에 답하기 위해 필요한 테이블(최대 5개)을 선택하고,\\n"
        result_text += "`get_detailed_metadata_for_sql` Tool을 호출하여 상세 메타데이터를 받아 SQL을 생성하세요.\\n"

        return [{"type": "text", "text": result_text}]'''

# 교체
if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ 코드 수정됨")

    # 백업
    with open('d:/Project/mcp_db/src/mcp_server.py.backup', 'w', encoding='utf-8') as f:
        f.write(content)

    # 저장
    with open('d:/Project/mcp_db/src/mcp_server.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("✅ 파일 저장 완료")
else:
    print("❌ 수정할 코드를 찾을 수 없습니다")
