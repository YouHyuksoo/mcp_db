"""
@file vectorize_columns.py
@description
이 파일은 table_column_definitions.csv를 읽어서 컬럼 정보를 Vector DB에 벡터화합니다.
자연어로 컬럼을 검색할 수 있게 해주는 핵심 스크립트입니다.

초보자 가이드:
1. **oracle_columns 컬렉션**: 테이블 컬렉션(oracle_metadata)과 별도로 컬럼 전용 컬렉션
2. **컬럼 ID 형식**: {database_sid}:{schema_name}:{table_name}:{column_name}
3. **벡터화 텍스트**: 테이블명 + 컬럼명 + 한국어설명 + 데이터타입을 조합

사용법:
    python vectorize_columns.py

입력 파일:
    data/{db_sid}/{schema}/csv_uploads/table_column_definitions.csv

작성일: 2025-12-29
"""

import sys
import csv
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# 프로젝트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

# 로깅 설정 (최소 로그)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # 시간/레벨 제거 - 최소 로그만 출력
)
logger = logging.getLogger(__name__)

# ChromaDB, sentence-transformers 로깅 비활성화
logging.getLogger("chromadb").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

# ChromaDB telemetry 비활성화
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


class ColumnVectorizer:
    """
    컬럼 메타데이터 벡터화 처리기 (CSV 기반)

    ★ 핵심 기능:
    - table_column_definitions.csv에서 컬럼 정보 로드
    - 컬럼 설명을 벡터로 변환하여 ChromaDB에 저장
    - 자연어 검색으로 관련 컬럼 찾기 지원
    """

    # 컬렉션 이름 상수
    COLLECTION_NAME = "oracle_columns"

    def __init__(self, database_sid: str, schema_name: str):
        """
        Args:
            database_sid: 대상 데이터베이스 SID
            schema_name: 대상 스키마 이름
        """
        self.database_sid = database_sid
        self.schema_name = schema_name

        # CSV 경로
        self.csv_path = project_root / "data" / database_sid / schema_name / "csv_uploads" / "table_column_definitions.csv"

        # Vector DB 경로
        self.vector_db_path = str(project_root / "data" / "vector_db")

        # 임베딩 모델 로드 (MCP 서버, 백엔드와 동일한 모델)
        logger.info("임베딩 모델 로딩 중...")
        self.model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        logger.info("✓ 임베딩 모델 로드 완료")

        # ChromaDB 연결
        logger.info(f"Vector DB 연결: {self.vector_db_path}")
        self.client = chromadb.PersistentClient(
            path=self.vector_db_path,
            settings=Settings(anonymized_telemetry=False)
        )

        # 컬럼 컬렉션 생성/가져오기
        self.collection = self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={
                "description": "Oracle column metadata for semantic search",
                "hnsw:space": "cosine"
            }
        )
        logger.info(f"✓ 컬렉션 준비 완료: {self.COLLECTION_NAME} ({self.collection.count()}개 기존 항목)")

    def load_csv(self) -> List[Dict[str, str]]:
        """
        table_column_definitions.csv 로드

        Returns:
            컬럼 정보 딕셔너리 리스트
        """
        if not self.csv_path.exists():
            logger.error(f"CSV 파일 없음: {self.csv_path}")
            return []

        rows = []
        encodings = ['utf-8-sig', 'utf-8', 'cp949']

        for enc in encodings:
            try:
                with open(self.csv_path, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get("table_name", "").strip() and row.get("column_name", "").strip():
                            rows.append(row)
                logger.info(f"✓ CSV에서 {len(rows)}개 컬럼 로드")
                break
            except UnicodeDecodeError:
                continue

        return rows

    def create_column_summary_text(
        self,
        table_name: str,
        column_name: str,
        korean_name: str,
        description: str,
        data_type: str,
        is_pk: str,
        table_comment: str,
        column_comment: str = "",
        code_values: str = ""
    ) -> str:
        """
        ★ 강화된 컬럼 벡터 임베딩용 요약 텍스트 생성
        (테이블 메타데이터 + 컬럼 정보 통합)

        핵심: 자연어 검색에 최적화된 텍스트 구성
        """
        parts = []

        # 1. 데이터베이스 & 테이블 정보 (컨텍스트)
        parts.append(f"[{self.database_sid}.{self.schema_name}]")
        parts.append(f"테이블: {table_name}")

        # ★ 테이블 설명 강조 (여러 번 포함하여 검색 가중치 증가)
        if table_comment:
            parts.append(f"테이블설명: {table_comment}")
            # 테이블 설명을 다시 한 번 포함 (검색 가중치 증가)
            parts.append(f"용도: {table_comment}")

        # 2. 컬럼 정보 (핵심!)
        parts.append("")
        parts.append(f"컬럼명: {column_name}")
        parts.append(f"데이터타입: {data_type}")

        if is_pk == 'Y':
            parts.append("★ Primary Key (기본키)")

        # 3. 컬럼 한글 이름 & 설명 (매우 중요!)
        if korean_name:
            parts.append(f"한글명: {korean_name}")

        if description:
            parts.append(f"설명: {description}")

        # ★ 컬럼 주석도 벡터화에 포함
        if column_comment:
            parts.append(f"주석: {column_comment}")

        # 4. 코드값 정보 (코드성 컬럼인 경우)
        if code_values:
            # JSON 형식인 경우 파싱하여 가독성 있게 표시
            try:
                import json
                code_dict = json.loads(code_values)
                code_list = [f"{k}({v})" for k, v in list(code_dict.items())[:5]]
                parts.append(f"코드값: {', '.join(code_list)}")
            except:
                # JSON 파싱 실패 시 원본 사용
                code_preview = code_values[:100]
                parts.append(f"코드값: {code_preview}")

        # 5. 검색 힌트 추가 (컬럼명에서 의미 추출)
        hints = self._extract_search_hints(column_name)
        if hints:
            parts.append("")
            parts.append(f"검색키워드: {', '.join(hints)}")

        return "\n".join(parts)

    def _extract_search_hints(self, column_name: str) -> List[str]:
        """
        컬럼명에서 검색 힌트 추출

        예: LINE_CODE → ['라인', '코드', 'LINE', 'CODE']
        """
        # 일반적인 컬럼명 패턴 → 한국어 매핑
        hint_map = {
            'LINE': ['라인', '생산라인'],
            'CODE': ['코드', '번호'],
            'NAME': ['명', '이름'],
            'DATE': ['일자', '날짜', '일시'],
            'QTY': ['수량', '개수'],
            'SIZE': ['크기', '사이즈', '수량'],
            'NO': ['번호', '넘버'],
            'ID': ['아이디', '식별자'],
            'MODEL': ['모델', '제품'],
            'ITEM': ['품목', '아이템', '제품'],
            'RUN': ['런', '실행', '생산'],
            'LOT': ['롯트', '로트', '배치'],
            'STATUS': ['상태', '스테이터스'],
            'TYPE': ['유형', '타입', '종류'],
            'ORGANIZATION': ['조직', '공장'],
            'ENTER': ['등록', '입력'],
            'MODIFY': ['수정', '변경'],
            'LAST': ['최종', '마지막'],
            'FIRST': ['최초', '처음'],
            'START': ['시작', '개시'],
            'END': ['종료', '끝'],
            'TOTAL': ['합계', '총'],
            'SUM': ['합계', '총합'],
            'AVG': ['평균'],
            'COUNT': ['건수', '횟수'],
            'AMOUNT': ['금액', '수량'],
            'PRICE': ['가격', '단가'],
            'COST': ['비용', '원가'],
            'DESCRIPTION': ['설명', '비고'],
            'COMMENT': ['코멘트', '설명', '비고'],
            'REMARK': ['비고', '메모'],
            'FLAG': ['플래그', '구분'],
            'YN': ['여부', 'Y/N'],
            'ACTIVE': ['활성', '사용'],
            'DELETE': ['삭제'],
            'CREATE': ['생성', '등록'],
            'UPDATE': ['수정', '업데이트'],
            'MASTER': ['마스터', '기준'],
            'DETAIL': ['상세', '디테일'],
            'HEADER': ['헤더', '머리'],
            'SUPPLIER': ['공급사', '업체'],
            'CUSTOMER': ['고객', '거래처'],
            'PRODUCT': ['제품', '생산'],
            'MATERIAL': ['자재', '원자재'],
            'MACHINE': ['설비', '기계'],
            'PROCESS': ['공정', '프로세스'],
            'WORK': ['작업', '업무'],
            'STAGE': ['단계', '스테이지'],
            'SHIFT': ['교대', '시프트'],
            'CARRIER': ['캐리어', '운반'],
            'PCB': ['PCB', '기판'],
            'VERSION': ['버전', '버젼'],
            'REVISION': ['리비전', '개정'],
        }

        hints = []

        # 컬럼명을 언더스코어로 분리
        parts = column_name.upper().split('_')

        for part in parts:
            if part in hint_map:
                hints.extend(hint_map[part])
            # 영문 원본도 추가
            if len(part) > 1:
                hints.append(part)

        return list(set(hints))  # 중복 제거

    def _get_existing_column_ids(self) -> set:
        """
        ★ ChromaDB에 이미 저장된 컬럼 ID 조회
        (진행 상황 추적용 - 중복 벡터화 방지)

        Returns:
            저장된 컬럼 ID 세트
        """
        try:
            # 데이터베이스+스키마로 필터링된 항목만 조회
            results = self.collection.get(
                where={
                    "$and": [
                        {"database_sid": self.database_sid},
                        {"schema_name": self.schema_name}
                    ]
                }
            )
            return set(results.get("ids", []))
        except Exception as e:
            logger.warning(f"기존 컬럼 조회 실패: {e}")
            return set()

    def vectorize(self, force_rebuild: bool = False) -> tuple:
        """
        컬럼 메타데이터 벡터화 수행

        ★ 강화: 테이블 메타데이터를 포함한 향상된 벡터화
        ★ force_rebuild=True일 때 기존 벡터 모두 삭제 후 재생성

        Args:
            force_rebuild: True면 기존 데이터 삭제 후 처음부터 다시 벡터화

        Returns:
            (새로 추가된 컬럼 수, 삭제된 컬럼 수, 총 처리 수)
        """
        # CSV 로드
        rows = self.load_csv()
        if not rows:
            logger.warning("처리할 컬럼이 없습니다.")
            return 0, 0, 0

        # ★ 기존 데이터 삭제 (강화된 벡터로 재생성하기 위함)
        deleted = 0
        if force_rebuild:
            logger.info("기존 벡터 삭제 중...")
            try:
                # 현재 DB/스키마의 모든 벡터 삭제
                self.collection.delete(
                    where={
                        "$and": [
                            {"database_sid": self.database_sid},
                            {"schema_name": self.schema_name}
                        ]
                    }
                )
                deleted = self.collection.count()
                logger.info(f"✓ 기존 벡터 삭제 완료")
            except Exception as e:
                logger.warning(f"기존 벡터 삭제 시 오류: {e}")

        logger.info(f"CSV 컬럼 총 수: {len(rows):,}개")

        # 배치 처리를 위한 리스트
        batch_ids = []
        batch_embeddings = []
        batch_documents = []
        batch_metadatas = []

        # 배치 크기: 500으로 증가 (로그 양 감소)
        BATCH_SIZE = 500
        processed = 0      # 처리된 컬럼

        for row in rows:
            table_name = row.get('table_name', '').strip()
            column_name = row.get('column_name', '').strip()

            if not table_name or not column_name:
                continue

            # 컬럼 ID 생성
            column_id = f"{self.database_sid}:{self.schema_name}:{table_name}:{column_name}"

            # CSV 필드 추출
            korean_name = row.get('korean_name', '').strip()
            description = row.get('description', '').strip()
            data_type = row.get('data_type', '').strip()
            is_pk = row.get('is_pk', 'N').strip()
            table_comment = row.get('table_comment', '').strip()
            column_comment = row.get('column_comment', '').strip()
            code_values = row.get('code_values', '').strip()

            # ★ 강화된 요약 텍스트 생성 (테이블 메타데이터 포함)
            summary_text = self.create_column_summary_text(
                table_name=table_name,
                column_name=column_name,
                korean_name=korean_name,
                description=description,
                data_type=data_type,
                is_pk=is_pk,
                table_comment=table_comment,
                column_comment=column_comment,
                code_values=code_values
            )

            # 임베딩 생성 (progress bar 비활성화)
            embedding = self.model.encode(summary_text, show_progress_bar=False).tolist()

            # 메타데이터 구성
            metadata = {
                "database_sid": self.database_sid,
                "schema_name": self.schema_name,
                "table_name": table_name,
                "column_name": column_name,
                "korean_name": korean_name[:200] if korean_name else "",
                "description": description[:500] if description else "",
                "data_type": data_type,
                "is_pk": is_pk == 'Y',
                "column_comment": column_comment[:200] if column_comment else "",
                "table_comment": table_comment[:200] if table_comment else ""
            }

            # code_values가 있으면 추가 (길이 제한)
            if code_values:
                metadata["code_values"] = code_values[:500]

            # 배치에 추가
            batch_ids.append(column_id)
            batch_embeddings.append(embedding)
            batch_documents.append(summary_text)
            batch_metadatas.append(metadata)

            # 배치 크기 도달 시 upsert
            if len(batch_ids) >= BATCH_SIZE:
                try:
                    self.collection.upsert(
                        ids=batch_ids,
                        embeddings=batch_embeddings,
                        documents=batch_documents,
                        metadatas=batch_metadatas
                    )
                    processed += len(batch_ids)
                    progress_pct = (processed / len(rows)) * 100
                    logger.info(f"✓ 처리함: {processed:,}/{len(rows):,} ({progress_pct:.1f}%)")
                except Exception as e:
                    logger.error(f"배치 upsert 실패: {e}")

                # 배치 초기화
                batch_ids = []
                batch_embeddings = []
                batch_documents = []
                batch_metadatas = []

        # 남은 배치 처리
        if batch_ids:
            try:
                self.collection.upsert(
                    ids=batch_ids,
                    embeddings=batch_embeddings,
                    documents=batch_documents,
                    metadatas=batch_metadatas
                )
                processed += len(batch_ids)
                logger.info(f"✓ 처리함: {processed:,}/{len(rows):,} (100.0%)")
            except Exception as e:
                logger.error(f"마지막 배치 upsert 실패: {e}")

        logger.info(f"\n✅ 벡터화 완료:")
        logger.info(f"  - 처리함: {processed:,}개")
        if force_rebuild:
            logger.info(f"  - 삭제됨: {deleted:,}개 (이전 약한 벡터)")
        logger.info(f"  - 총 저장됨: {self.collection.count():,}개")

        return processed, deleted, self.collection.count()

    def search_columns(
        self,
        query: str,
        table_name: Optional[str] = None,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        자연어로 컬럼 검색

        Args:
            query: 자연어 검색어 (예: "라인", "일자", "수량")
            table_name: 특정 테이블로 제한 (선택)
            n_results: 반환할 결과 수

        Returns:
            관련 컬럼 정보 리스트
        """
        # 쿼리 임베딩 (progress bar 비활성화)
        query_embedding = self.model.encode(query, show_progress_bar=False).tolist()

        # 필터 조건
        where_filter = {
            "$and": [
                {"database_sid": self.database_sid},
                {"schema_name": self.schema_name}
            ]
        }

        # 특정 테이블로 제한
        if table_name:
            where_filter["$and"].append({"table_name": table_name})

        # ChromaDB 검색
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter
        )

        # 결과 포맷팅
        columns = []
        if results["ids"] and results["ids"][0]:
            for i, col_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                similarity = max(0, 1 - (distance / 2))

                columns.append({
                    "column_id": col_id,
                    "table_name": metadata.get("table_name", ""),
                    "column_name": metadata.get("column_name", ""),
                    "korean_name": metadata.get("korean_name", ""),
                    "data_type": metadata.get("data_type", ""),
                    "is_pk": metadata.get("is_pk", False),
                    "similarity": round(similarity * 100, 1)
                })

        return columns


def main():
    """메인 실행 함수"""
    database_sid = "SMVNPDBext"
    schema_name = "INFINITY21_JSMES"

    logger.info("=" * 60)
    logger.info("★ 컬럼 메타데이터 벡터화 (강화 모드)")
    logger.info("테이블 메타데이터 + 컬럼 정보 통합 벡터화")
    logger.info(f"Database: {database_sid}")
    logger.info(f"Schema: {schema_name}")
    logger.info("=" * 60)

    vectorizer = ColumnVectorizer(database_sid, schema_name)

    # ★ 강화된 벡터로 재생성 (force_rebuild=True)
    processed, deleted, total = vectorizer.vectorize(force_rebuild=True)

    logger.info("=" * 60)
    logger.info(f"✅ 벡터화 완료:")
    logger.info(f"  - 처리함: {processed:,}개")
    logger.info(f"  - 삭제됨: {deleted:,}개 (이전 벡터)")
    logger.info(f"  - 총 저장됨: {total:,}개")
    logger.info("=" * 60)

    # 테스트 검색
    if total > 0:
        logger.info("\n" + "=" * 60)
        logger.info("[테스트 검색]")
        logger.info("=" * 60)

        test_queries = ["라인", "일자", "수량", "모델명"]

        for query in test_queries:
            results = vectorizer.search_columns(query, n_results=5)
            logger.info(f"\n'{query}' 검색 결과:")
            for r in results:
                pk_mark = "[PK]" if r['is_pk'] else ""
                logger.info(f"  - {r['table_name']}.{r['column_name']} {pk_mark}")
                logger.info(f"    한글명: {r['korean_name']} | 타입: {r['data_type']} | 유사도: {r['similarity']}%")


if __name__ == "__main__":
    main()
