"""
CSV 통합 스크립트
기존 4종 CSV를 2종으로 통합

@file convert_csv.py
@description
기존 table_info_template.csv, common_columns_template.csv, code_definitions_template.csv를
새로운 table_metadata.csv, column_definitions.csv로 통합합니다.
"""

import csv
import json
import re
import sys
import traceback
from pathlib import Path


def clean_text(text: str) -> str:
    """깨진 문자 정리"""
    if not text:
        return ""
    # 물음표 제거
    text = re.sub(r'\?+', '', text)
    # 이상한 문자 정리
    text = re.sub(r'¿+', '', text)
    return text.strip()


def extract_domain(business_purpose: str) -> str:
    """비즈니스 목적에서 도메인 추출"""
    purpose = clean_text(business_purpose).lower()
    
    if 'smt' in purpose or 'mounting' in purpose or '실장' in purpose:
        return 'SMT/실장'
    elif 'item' in purpose or 'bom' in purpose or '품목' in purpose:
        return 'BOM/품목'
    elif 'inventory' in purpose or 'material' in purpose or '재고' in purpose or '자재' in purpose:
        return '재고/자재'
    elif 'machine' in purpose or 'maintenance' in purpose or '설비' in purpose or '보전' in purpose:
        return '설비/보전'
    elif 'production' in purpose or '생산' in purpose:
        return '생산관리'
    elif 'quality' in purpose or '품질' in purpose:
        return '품질관리'
    elif 'sales' in purpose or 'shipping' in purpose or '판매' in purpose or '출하' in purpose:
        return '판매/출하'
    elif 'system' in purpose or '시스템' in purpose:
        return '시스템'
    elif 'common' in purpose or 'integration' in purpose or '공통' in purpose:
        return '공통'
    elif 'interface' in purpose or '인터페이스' in purpose:
        return '인터페이스'
    else:
        return '기타'


def generate_keywords(table_name: str, business_purpose: str, usage_scenarios: list) -> str:
    """테이블명과 비즈니스 목적에서 검색 키워드 추출"""
    keywords = set()
    
    # 테이블명에서 키워드 추출
    parts = table_name.replace('_', ' ').split()
    for part in parts:
        if len(part) > 1:
            keywords.add(part.upper())
    
    # 비즈니스 목적에서 한글 키워드 추출
    purpose = clean_text(business_purpose)
    korean_words = re.findall(r'[가-힣]+', purpose)
    for word in korean_words:
        if len(word) > 1:
            keywords.add(word)
    
    # 사용 시나리오에서 한글 키워드 추출
    for scenario in usage_scenarios:
        scenario_clean = clean_text(scenario)
        korean_words = re.findall(r'[가-힣]+', scenario_clean)
        for word in korean_words:
            if len(word) > 1:
                keywords.add(word)
    
    return ' '.join(sorted(keywords)[:10])  # 최대 10개


def generate_description_ko(table_name: str, business_purpose: str) -> str:
    """한국어 설명 생성"""
    purpose = clean_text(business_purpose)
    
    # 이미 한글이 있으면 그대로 사용
    if re.search(r'[가-힣]', purpose):
        # 영어 부분도 있으면 한글만 추출
        korean_part = ' '.join(re.findall(r'[가-힣]+', purpose))
        if korean_part:
            return purpose  # 전체 목적 사용
    
    return purpose


def generate_sample_queries(table_name: str, usage_scenarios: list) -> str:
    """예상 질문 생성"""
    queries = []
    
    for scenario in usage_scenarios:
        scenario_clean = clean_text(scenario)
        if scenario_clean and len(scenario_clean) > 2:
            queries.append(scenario_clean)
    
    return '|'.join(queries[:5])  # 최대 5개


def convert_tables():
    """테이블 정보 변환"""
    print("Starting convert_tables...")
    base_path = Path(r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads')
    
    # 기존 table_info 읽기
    tables = []
    try:
        with open(base_path / 'table_info_template.csv', 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get('table_name', '').strip()
                if not name:
                    continue
                    
                business_purpose = row.get('business_purpose', '')
                usage_scenarios = [
                    row.get('usage_scenario_1', ''),
                    row.get('usage_scenario_2', ''),
                    row.get('usage_scenario_3', '')
                ]
                related_tables = row.get('related_tables', '')
                
                tables.append({
                    'table_name': name,
                    'description_ko': generate_description_ko(name, business_purpose),
                    'domain': extract_domain(business_purpose),
                    'keywords': generate_keywords(name, business_purpose, usage_scenarios),
                    'sample_queries': generate_sample_queries(name, usage_scenarios),
                    'related_tables': clean_text(related_tables)
                })
        
        # 새 table_metadata.csv 저장
        out_path = base_path / 'table_metadata.csv'
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['table_name', 'description_ko', 'domain', 'keywords', 'sample_queries', 'related_tables']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(tables)
        
        print(f'Generated table_metadata.csv at {out_path} with {len(tables)} tables')
    except Exception as e:
        print(f"Error in convert_tables: {e}")
        traceback.print_exc()
    return tables


def convert_columns():
    """컬럼 정의 및 코드 정의 통합"""
    print("Starting convert_columns...")
    base_path = Path(r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads')
    
    try:
        # 기존 common_columns 읽기
        print("Reading common_columns_template.csv...")
        
        encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-8-sig']
        rows = []
        
        for enc in encodings:
            try:
                print(f"Trying encoding: {enc}")
                with open(base_path / 'common_columns_template.csv', 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                print(f"Successfully read with {enc}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error with {enc}: {e}")
                continue
        
        if not rows:
            print("Failed to read common_columns_template.csv with any encoding")
            return []

        count = 0
        for row in rows:
            col_name = row.get('column_name', '').strip()
            # ... (나머지 로직 동일)
            if not col_name:
                continue
            
            columns[col_name] = {
                'column_name': col_name,
                'korean_name': clean_text(row.get('korean_name', '')),
                'description': clean_text(row.get('description', '')),
                'is_code_column': row.get('is_code_column', 'N')
            }
            count += 1
        print(f"Read {count} columns.")

        # 기존 code_definitions 읽어서 코드값 추가
        print("Reading code_definitions_template.csv...")
        code_rows = []
        for enc in encodings:
            try:
                with open(base_path / 'code_definitions_template.csv', 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    code_rows = list(reader)
                break
            except UnicodeDecodeError:
                continue
        
        code_count = 0
        for row in code_rows:
            col_name = row.get('column_name', '').strip()
            # ...
            code_value = row.get('code_value', '').strip()
            code_label = row.get('code_label', '').strip()
            
            if not col_name or not code_value:
                continue
            
            if col_name not in code_values:
                code_values[col_name] = {}
            
            code_values[col_name][code_value] = code_label
            code_count += 1
        print(f"Read {code_count} code definitions.")
        
        # 컬럼 정보에 코드값 통합
        print("Merging column data...")
        result = []
        for col_name, col_info in columns.items():
            codes = code_values.get(col_name, {})
            result.append({
                'column_name': col_info['column_name'],
                'korean_name': col_info['korean_name'],
                'description': col_info['description'],
                'code_values': json.dumps(codes, ensure_ascii=False) if codes else ''
            })
        
        # 새 column_definitions.csv 저장
        out_path = base_path / 'column_definitions.csv'
        print(f"Writing to {out_path}...")
        with open(out_path, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ['column_name', 'korean_name', 'description', 'code_values']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(result)
        
        print(f'Generated column_definitions.csv with {len(result)} columns ({len(code_values)} with codes)')
    except Exception as e:
        print(f"Error in convert_columns: {e}")
        traceback.print_exc()
    return result


if __name__ == '__main__':
    try:
        convert_tables()
        convert_columns()
        print('CSV conversion complete!')
    except Exception as e:
        print(f"Fatal error: {e}")
        traceback.print_exc()
