"""
최적화된 CSV를 사용한 벡터화 스크립트

이 스크립트는 table_metadata_optimized.csv 파일을 읽어서
Vector DB에 저장합니다. 기존 벡터화 데이터와 병합됩니다.

사용법:
    python vectorize_optimized_csv.py

작성일: 2024-12-29
"""

import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# 프로젝트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from sentence_transformers import SentenceTransformer
import chromadb

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizedCSVVectorizer:
    """
    최적화된 CSV 파일을 사용한 벡터화 처리기
    
    CSV 양식:
    - table_name: 테이블 물리명
    - table_description_ko: 한국어 상세 설명
    - table_description_en: 영어 설명
    - domain: 도메인/업무영역
    - keywords: 검색 키워드 (공백 구분)
    - sample_queries: 예상 질문 (파이프 구분)
    """
    
    def __init__(self, database_sid: str, schema_name: str):
        """
        Args:
            database_sid: 대상 데이터베이스 SID
            schema_name: 대상 스키마 이름
        """
        self.database_sid = database_sid
        self.schema_name = schema_name
        
        # 경로 설정
        self.csv_path = project_root / "data" / database_sid / schema_name / "csv_uploads" / "table_metadata_optimized.csv"
        self.vector_db_path = str(project_root / "data" / "vector_db")
        
        # 임베딩 모델 로드
        logger.info("임베딩 모델 로딩 중...")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        
        # ChromaDB 연결
        logger.info(f"Vector DB 연결: {self.vector_db_path}")
        self.client = chromadb.PersistentClient(path=self.vector_db_path)
        self.collection = self.client.get_or_create_collection(
            name="oracle_metadata",
            metadata={"hnsw:space": "cosine"}
        )
        
    def load_csv(self) -> List[Dict[str, str]]:
        """최적화된 CSV 파일 로드"""
        if not self.csv_path.exists():
            logger.warning(f"CSV 파일이 없습니다: {self.csv_path}")
            return []
        
        rows = []
        # BOM이 포함된 UTF-8 파일 처리를 위해 utf-8-sig 사용
        encodings = ['utf-8-sig', 'utf-8', 'cp949']
        for enc in encodings:
            try:
                with open(self.csv_path, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("table_name", "").strip():
                            rows.append(row)
                break  # 성공하면 루프 종료
            except UnicodeDecodeError:
                continue
        
        logger.info(f"CSV에서 {len(rows)}개 테이블 정보 로드")
        return rows
    
    def load_existing_oracle_columns(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        기존 벡터 DB에서 Oracle 컬럼 정보 로드
        
        Returns:
            {table_name: [column_dicts]}
        """
        columns_by_table = {}
        
        try:
            # 현재 DB/스키마의 모든 메타데이터 조회
            results = self.collection.get(
                where={
                    "$and": [
                        {"database_sid": {"$eq": self.database_sid}},
                        {"schema_name": {"$eq": self.schema_name}}
                    ]
                },
                include=["metadatas"]
            )
            
            if results and results['metadatas']:
                for meta in results['metadatas']:
                    table_name = meta.get("table_name", "")
                    columns_str = meta.get("columns", "")
                    
                    if table_name and columns_str:
                        try:
                            columns = json.loads(columns_str)
                            columns_by_table[table_name] = columns
                        except json.JSONDecodeError:
                            pass
                            
        except Exception as e:
            logger.warning(f"기존 컬럼 정보 로드 실패: {e}")
        
        logger.info(f"기존 컬럼 정보 {len(columns_by_table)}개 테이블 로드")
        return columns_by_table
    
    def create_summary_text(
        self,
        table_name: str,
        description_ko: str,
        description_en: str,
        domain: str,
        keywords: str,
        sample_queries: str,
        columns: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        벡터 임베딩용 요약 텍스트 생성
        
        ★ 핵심: 한국어 설명 + 키워드 + 샘플 질문을 통합
        """
        parts = []
        
        # 1. 헤더
        header = f"[{self.database_sid}.{self.schema_name}] 테이블: {table_name}"
        parts.append(header)
        parts.append("")
        
        # 2. 도메인
        if domain:
            parts.append(f"업무영역: {domain}")
        
        # 3. 한국어 설명 (핵심!)
        if description_ko:
            parts.append(f"설명: {description_ko}")
        elif description_en:
            parts.append(f"Description: {description_en}")
        parts.append("")
        
        # 4. 키워드 (유사어 매칭)
        if keywords:
            parts.append(f"관련 키워드: {keywords}")
        
        # 5. 샘플 질문 (의도 매칭)
        if sample_queries:
            queries = [q.strip() for q in sample_queries.split("|") if q.strip()]
            if queries:
                parts.append("관련 질문:")
                for q in queries[:5]:
                    parts.append(f"- {q}")
        parts.append("")
        
        # 6. 주요 컬럼
        if columns:
            parts.append("주요 컬럼:")
            for col in columns[:8]:
                col_name = col.get("name", col.get("COLUMN_NAME", ""))
                col_type = col.get("data_type", col.get("DATA_TYPE", ""))
                parts.append(f"- {col_name} [{col_type}]")
        
        return "\n".join(parts)
    
    def vectorize(self) -> int:
        """
        최적화된 CSV 데이터 벡터화 수행
        
        Returns:
            처리된 테이블 수
        """
        csv_rows = self.load_csv()
        if not csv_rows:
            logger.warning("처리할 CSV 데이터가 없습니다.")
            return 0
        
        # 기존 컬럼 정보 로드
        existing_columns = self.load_existing_oracle_columns()
        
        processed = 0
        for row in csv_rows:
            table_name = row.get("table_name", "").strip()
            if not table_name:
                continue
            
            # CSV 필드 추출
            description_ko = row.get("table_description_ko", "").strip()
            description_en = row.get("table_description_en", "").strip()
            domain = row.get("domain", "").strip()
            keywords = row.get("keywords", "").strip()
            sample_queries = row.get("sample_queries", "").strip()
            
            # 기존 컬럼 정보
            columns = existing_columns.get(table_name, [])
            
            # 요약 텍스트 생성
            summary_text = self.create_summary_text(
                table_name=table_name,
                description_ko=description_ko,
                description_en=description_en,
                domain=domain,
                keywords=keywords,
                sample_queries=sample_queries,
                columns=columns
            )
            
            # 임베딩 생성
            embedding = self.model.encode(summary_text).tolist()
            
            # 메타데이터 구성
            metadata = {
                "database_sid": self.database_sid,
                "schema_name": self.schema_name,
                "table_name": table_name,
                "description_ko": description_ko,
                "description_en": description_en,
                "domain": domain,
                "keywords": keywords,
                "sample_queries": sample_queries,
                "column_count": len(columns),
            }
            
            if columns:
                metadata["columns"] = json.dumps(columns[:15], ensure_ascii=False)
            
            # Vector DB에 upsert (기존 데이터 업데이트)
            table_id = f"{self.database_sid}:{self.schema_name}:{table_name}"
            
            try:
                self.collection.upsert(
                    ids=[table_id],
                    embeddings=[embedding],
                    documents=[summary_text],
                    metadatas=[metadata]
                )
                processed += 1
                
                if processed % 10 == 0:
                    logger.info(f"진행중... {processed}/{len(csv_rows)}")
                    
            except Exception as e:
                logger.error(f"벡터화 실패 ({table_name}): {e}")
        
        logger.info(f"완료: {processed}개 테이블 벡터화")
        return processed


def main():
    """메인 실행 함수"""
    # 기본 설정 (필요시 변경)
    database_sid = "SMVNPDBext"
    schema_name = "INFINITY21_JSMES"
    
    logger.info("=" * 60)
    logger.info("최적화된 CSV 벡터화 시작")
    logger.info(f"Database: {database_sid}")
    logger.info(f"Schema: {schema_name}")
    logger.info("=" * 60)
    
    vectorizer = OptimizedCSVVectorizer(database_sid, schema_name)
    count = vectorizer.vectorize()
    
    logger.info("=" * 60)
    logger.info(f"벡터화 완료: 총 {count}개 테이블")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
