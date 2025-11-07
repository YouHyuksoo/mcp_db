# Oracle NLSQL MCP Server - 리뉴얼 PRD (Product Requirements Document)

**문서 버전**: 1.0
**작성일**: 2025-01-07
**프로젝트명**: Oracle NLSQL MCP Server Renewal
**목표 완성일**: 2025-03-31

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [프로젝트 현황 분석](#2-프로젝트-현황-분석)
3. [리뉴얼 목표 및 비전](#3-리뉴얼-목표-및-비전)
4. [주요 변경 사항 (Before/After)](#4-주요-변경-사항-beforeafter)
5. [3-Tier 아키텍처 설계](#5-3-tier-아키텍처-설계)
6. [Vector DB 통합 설계](#6-vector-db-통합-설계)
7. [PowerBuilder 학습 시스템](#7-powerbuilder-학습-시스템)
8. [기능 명세 (Detailed)](#8-기능-명세-detailed)
9. [데이터 구조 설계](#9-데이터-구조-설계)
10. [UI/UX 설계](#10-uiux-설계)
11. [기술 스택](#11-기술-스택)
12. [구현 로드맵](#12-구현-로드맵)
13. [성공 지표 및 KPI](#13-성공-지표-및-kpi)
14. [리스크 관리](#14-리스크-관리)

---

## 1. Executive Summary

### 1.1 프로젝트 개요

**Oracle NLSQL MCP Server**는 Claude AI와 Oracle Database를 연결하여 자연어 질의를 SQL로 자동 변환하는 MCP(Model Context Protocol) 서버입니다. 현재 버전은 21개의 MCP Tools를 통해 완전한 기능을 제공하고 있으나, 다음과 같은 개선 필요성이 제기되었습니다.

### 1.2 리뉴얼 배경

#### 현재 시스템의 한계

1. **메타데이터 검색 비효율성**
   - 전체 JSON 파일을 순차적으로 읽어야 함
   - 100+ 테이블 환경에서 Stage 1 응답 시간 지연
   - 유사한 질의에 대한 재사용 불가

2. **학습 능력 부재**
   - 성공한 SQL 패턴이 저장되지 않음
   - 반복 질의도 매번 처음부터 생성
   - 사용자 피드백이 시스템 개선으로 이어지지 않음

3. **레거시 시스템 통합 어려움**
   - PowerBuilder 등 레거시 소스 코드의 암묵적 지식 활용 불가
   - 수동으로 CSV 작성 필요 (초기 셋업 2-3일 소요)

4. **관리 기능의 UX 부족**
   - MCP Tools만으로 파일 업로드/학습 관리 어려움
   - 학습 진행 상황 모니터링 불가
   - 패턴 관리 및 수정 불편

### 1.3 리뉴얼 목표

#### 핵심 목표 (Primary Goals)

1. **Vector DB 기반 지능형 검색 시스템 구축**
   - ChromaDB를 활용한 의미론적 검색
   - 기존 메타데이터의 완전한 Vector화
   - 검색 응답 시간 80% 단축 (목표: Stage 1 < 1초)

2. **자동 학습 시스템 구현**
   - 성공한 SQL 패턴 자동 저장 및 재사용
   - 사용할수록 똑똑해지는 점진적 학습
   - PowerBuilder 소스코드 자동 분석 및 지식 추출

3. **3-Tier 아키텍처로 관심사 분리**
   - MCP Server: SQL 생성/실행 (Claude Code 전용)
   - Management Backend: 학습/관리 (FastAPI)
   - Web UI: 사용자 인터페이스 (React)

4. **사용자 경험 개선**
   - 직관적인 Web UI 제공
   - 실시간 학습 진행 상황 모니터링
   - 드래그 앤 드롭 파일 업로드

#### 부가 목표 (Secondary Goals)

5. **초기 셋업 시간 90% 단축**
   - 레거시 SQL → 자동 학습: 2-3일 → 2-3시간
   - PowerBuilder 소스 분석 자동화

6. **비용 최적화**
   - 유사 질의 재사용으로 LLM API 호출 최소화
   - 패턴 매칭으로 토큰 사용량 60% 절감

7. **확장성 확보**
   - 다중 DB 지원 (현재 1개 → 10+ 개)
   - 멀티 스키마 동시 관리

### 1.4 예상 효과

| 지표 | 현재 | 목표 | 개선율 |
|------|------|------|--------|
| **Stage 1 응답 시간** | 5-10초 | < 1초 | 80-90% ↓ |
| **초기 셋업 시간** | 2-3일 | 2-3시간 | 90% ↓ |
| **LLM API 비용** | 100% | 40% | 60% ↓ |
| **SQL 정확도** | 70-80% | 90-95% | 15-20% ↑ |
| **유사 질의 재사용률** | 0% | 70% | - |

### 1.5 주요 이해관계자

| 역할 | 관심사 | 기대 효과 |
|------|--------|-----------|
| **개발자** | 빠른 데이터 조회, 학습 용이성 | SQL 작성 시간 80% 단축 |
| **DBA** | 시스템 안정성, 관리 편의성 | 메타데이터 관리 UI 제공 |
| **비즈니스 사용자** | 자연어로 데이터 조회 | 기술 지식 없이 DB 조회 가능 |
| **시스템 관리자** | 보안, 성능 모니터링 | 대시보드를 통한 실시간 모니터링 |

---

## 2. 프로젝트 현황 분석

### 2.1 현재 시스템 구조

#### 2.1.1 아키텍처

```
현재 (Monolithic MCP Server)
┌─────────────────────────────────────────┐
│ MCP Server (21 Tools)                   │
│  - DB 연결 관리                          │
│  - 메타데이터 관리                       │
│  - CSV 임포트                            │
│  - SQL 생성 (2-Stage LLM)               │
│  - SQL 실행                              │
└─────────────────────────────────────────┘
                ↓ ↑
┌─────────────────────────────────────────┐
│ Claude Desktop (사용자)                  │
└─────────────────────────────────────────┘
                ↓ ↑
┌─────────────────────────────────────────┐
│ 로컬 파일 시스템                         │
│  - metadata/ (JSON)                     │
│  - common_metadata/ (JSON)              │
│  - credentials/ (암호화)                │
└─────────────────────────────────────────┘
```

#### 2.1.2 데이터 흐름

```
자연어 질의
    ↓
[Stage 1] table_summaries.json 전체 로드 (5-10초)
    ↓
LLM이 관련 테이블 선택 (최대 5개)
    ↓
[Stage 2] 선택된 테이블의 unified_metadata.json 로드
    ↓
LLM이 SQL 생성
    ↓
SQL 실행 및 결과 반환
```

### 2.2 현재 기능 목록

#### 2.2.1 MCP Tools (21개)

**DB 연결 관리 (5개)**
- `register_database_credentials`: DB 접속정보 등록 + 암호화
- `delete_database`: DB 삭제
- `load_tnsnames`: tnsnames.ora 파싱
- `list_available_databases`: tnsnames DB 목록
- `connect_database`: DB 연결

**DB 탐색 (6개)**
- `show_databases`: 등록 DB 목록
- `show_schemas`: 스키마 목록
- `show_tables`: 테이블 목록
- `describe_table`: 테이블 상세
- `show_procedures`: 프로시저 목록
- `show_procedure_source`: 프로시저 소스

**자연어 SQL 생성 (2개 - 핵심)**
- `get_table_summaries_for_query`: Stage 1 메타데이터
- `get_detailed_metadata_for_sql`: Stage 2 메타데이터

**SQL 실행 (1개)**
- `execute_sql`: SQL 실행

**메타데이터 관리 (7개)**
- `get_table_metadata`: 통합 메타데이터 조회
- `register_common_columns`: 공통 칼럼 등록
- `register_code_values`: 코드 정의 등록
- `view_common_metadata`: 공통 메타데이터 조회
- `extract_and_integrate_metadata`: 스키마 추출 + 통합
- `import_common_columns_csv`: CSV 일괄 등록
- `import_code_definitions_csv`: CSV 일괄 등록
- `import_table_info_csv`: CSV 일괄 등록
- `generate_csv_from_schema`: CSV 템플릿 생성

### 2.3 강점 (Strengths)

1. **완전한 기능 구현**
   - 21개 Tool로 모든 워크플로우 커버
   - tnsnames.ora 자동 파싱
   - Fernet 암호화로 안전한 접속정보 관리

2. **2-Stage LLM 전략**
   - 대용량 메타데이터 효율적 처리
   - 토큰 사용량 최적화

3. **포괄적인 메타데이터**
   - DB 스키마 자동 추출
   - CSV 기반 사용자 정의 메타데이터
   - 통합 메타데이터 생성 (unified_metadata.json)

4. **SQL 최적화 검증**
   - 8가지 규칙 기반 인덱스 최적화 체크
   - sql_rules.md로 명문화

5. **완전한 문서화**
   - README, USAGE_GUIDE, FOLDER_STRUCTURE 등

### 2.4 약점 (Weaknesses)

1. **검색 성능 이슈**
   - JSON 파일 순차 읽기 (I/O 병목)
   - 100+ 테이블 환경에서 5-10초 소요
   - 의미론적 검색 불가

2. **학습 불가**
   - 성공한 SQL 저장 안 됨
   - 반복 질의 최적화 불가
   - 사용자 피드백 미반영

3. **UX 부족**
   - CLI 기반 파일 업로드
   - 진행 상황 모니터링 불가
   - 학습 데이터 관리 어려움

4. **레거시 통합 어려움**
   - PowerBuilder 소스 수동 분석 필요
   - 초기 셋업 2-3일 소요

5. **확장성 제약**
   - Monolithic 구조
   - 다중 DB 관리 복잡도 증가

### 2.5 기회 (Opportunities)

1. **Vector DB 기술 성숙**
   - ChromaDB 등 로컬 Vector DB 안정화
   - 의미론적 검색 정확도 향상

2. **LLM 성능 개선**
   - Claude Sonnet 4 출시 (정확도 ↑, 비용 ↓)
   - 구조화된 출력 지원 강화

3. **레거시 마이그레이션 수요**
   - 많은 기업이 PowerBuilder → 모던 시스템 전환
   - 암묵적 지식 추출 자동화 수요 증가

4. **No-Code/Low-Code 트렌드**
   - 비개발자의 데이터 접근성 향상 요구
   - 자연어 인터페이스 수요 증가

### 2.6 위협 (Threats)

1. **경쟁 솔루션 출현**
   - GitHub Copilot DB, Cursor 등 AI 기반 SQL 생성 도구
   - 클라우드 통합 솔루션 (BigQuery, Snowflake의 자연어 기능)

2. **Oracle 생태계 축소**
   - PostgreSQL, MySQL로의 이전 트렌드
   - Oracle 라이선스 비용 부담

3. **LLM API 비용**
   - 대량 사용 시 비용 급증 가능
   - 토큰 최적화 필수

---

## 3. 리뉴얼 목표 및 비전

### 3.1 비전 (Vision)

> **"모든 사람이 자연어로 Oracle 데이터에 접근할 수 있는 세상"**

사용자가 SQL을 몰라도, 메타데이터를 정리하지 않아도, 레거시 시스템의 암묵적 지식을 자동으로 학습하여 정확한 SQL을 생성하는 지능형 시스템

### 3.2 미션 (Mission)

1. **접근성**: 기술 지식 없이 누구나 데이터 조회 가능
2. **학습성**: 사용할수록 똑똑해지는 자동 학습 시스템
3. **효율성**: 초기 셋업 시간 90% 단축, LLM 비용 60% 절감
4. **신뢰성**: SQL 정확도 90% 이상 달성

### 3.3 핵심 가치 제안 (Value Propositions)

#### 3.3.1 개발자를 위한 가치

- **시간 절약**: SQL 작성 시간 80% 단축
- **학습 곡선 완화**: Oracle 문법 몰라도 데이터 조회 가능
- **레거시 이해**: PowerBuilder 소스 자동 분석으로 비즈니스 로직 파악

#### 3.3.2 DBA를 위한 가치

- **메타데이터 관리**: Web UI로 직관적 관리
- **성능 모니터링**: 대시보드로 실시간 모니터링
- **자동 최적화**: 인덱스 활용 여부 자동 검증

#### 3.3.3 비즈니스 사용자를 위한 가치

- **자연어 인터페이스**: "지난달 VIP 고객 주문 내역" → SQL 자동 생성
- **즉시 결과**: 1초 이내 응답
- **학습 재사용**: 반복 질의 0.1초 이내 처리

### 3.4 목표 지표 (OKRs)

#### Objective 1: Vector DB 기반 검색 성능 혁신

**Key Results**:
- KR1: Stage 1 응답 시간 < 1초 달성 (현재 5-10초)
- KR2: 유사 질의 재사용률 70% 달성
- KR3: 의미론적 검색 정확도 90% 달성

#### Objective 2: 자동 학습 시스템 구축

**Key Results**:
- KR1: 성공 SQL 패턴 자동 저장률 100%
- KR2: 학습 패턴 재사용으로 LLM 호출 60% 감소
- KR3: 사용자 피드백 반영률 100%

#### Objective 3: PowerBuilder 자동 학습

**Key Results**:
- KR1: PB 소스 → SQL 추출 정확도 85% 달성
- KR2: 초기 셋업 시간 2-3일 → 2-3시간 단축
- KR3: 관계 추론 정확도 80% 달성

#### Objective 4: 사용자 경험 개선

**Key Results**:
- KR1: Web UI 완성도 90% 달성
- KR2: 파일 업로드 성공률 95% 달성
- KR3: 사용자 만족도 4.5/5.0 달성

---

## 4. 주요 변경 사항 (Before/After)

### 4.1 아키텍처 변경

#### Before: Monolithic MCP Server

```
┌───────────────────────────────────────────────┐
│ MCP Server (Single Process)                  │
│                                               │
│  ┌─────────────────────────────────────┐     │
│  │ 21 MCP Tools                        │     │
│  │  - DB 연결/조회                      │     │
│  │  - 메타데이터 관리                   │     │
│  │  - CSV 임포트 (파일 처리)           │     │
│  │  - SQL 생성 (2-Stage LLM)          │     │
│  │  - SQL 실행                         │     │
│  └─────────────────────────────────────┘     │
│                                               │
└───────────────────────────────────────────────┘
                    ↓ ↑
        (Claude Desktop - stdio)
                    ↓ ↑
┌───────────────────────────────────────────────┐
│ 로컬 파일 시스템 (JSON)                       │
│  - metadata/                                  │
│  - common_metadata/                           │
│  - credentials/                               │
└───────────────────────────────────────────────┘
```

**문제점**:
- 모든 기능이 하나의 프로세스에 집중
- 파일 처리 같은 무거운 작업이 MCP 서버 블로킹
- 관리 UI 부재

#### After: 3-Tier 분리 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│ 로컬 머신 (사용자 PC)                                        │
│                                                             │
│  ┌───────────────────────────────────────┐                 │
│  │ Tier 1: MCP Server (stdio)            │                 │
│  │  - SQL 생성/실행 (핵심만)             │                 │
│  │  - DB 연결/조회                        │                 │
│  │  - 메타데이터 조회 (읽기 전용)        │                 │
│  │  ↕ Claude Desktop                     │                 │
│  └───────────────────────────────────────┘                 │
│                    ↓ ↑                                      │
│           (Shared Core - 공통 로직)                         │
│                    ↓ ↑                                      │
│  ┌───────────────────────────────────────┐                 │
│  │ Tier 2: Management Backend (FastAPI)  │                 │
│  │  - 학습 관리 (PowerBuilder, 패턴)     │                 │
│  │  - 파일 처리 (CSV 업로드)             │                 │
│  │  - Vector DB 관리                      │                 │
│  │  - REST API (localhost:8000)          │                 │
│  └───────────────────────────────────────┘                 │
│                    ↓ ↑                                      │
│  ┌───────────────────────────────────────┐                 │
│  │ Tier 3: Web UI (React)                │                 │
│  │  - 대시보드                            │                 │
│  │  - 학습 데이터 관리                    │                 │
│  │  - 패턴 관리                           │                 │
│  │  - 브라우저 (localhost:3000)          │                 │
│  └───────────────────────────────────────┘                 │
│                                                             │
│  ┌───────────────────────────────────────┐                 │
│  │ 공유 데이터 저장소 (로컬)              │                 │
│  │  - D:\Project\mcp_db\data\            │                 │
│  │    ├── vector_db/ (ChromaDB)          │                 │
│  │    ├── metadata/ (JSON - 기존 유지)   │                 │
│  │    └── credentials/ (암호화)          │                 │
│  └───────────────────────────────────────┘                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**장점**:
- ✅ 관심사 분리 (MCP: SQL 생성, Management: 관리)
- ✅ 무거운 작업 분리 (PB 학습, CSV 처리)
- ✅ Web UI로 관리 편의성 향상
- ✅ 모두 로컬 실행 (서버 불필요)
- ✅ 동일한 Vector DB/메타데이터 공유

### 4.2 데이터 흐름 변경

#### Before: JSON 기반 순차 검색

```
자연어 질의
    ↓
[Stage 1]
  ├─ table_summaries.json 파일 읽기 (I/O)
  ├─ 전체 100+ 테이블 정보 로드
  └─ LLM에게 전달 (5-10초 소요)
    ↓
LLM이 관련 테이블 5개 선택
    ↓
[Stage 2]
  ├─ 선택된 5개 테이블의 unified_metadata.json 읽기
  └─ LLM에게 전달
    ↓
SQL 생성 및 실행
```

**문제**:
- 파일 I/O 병목
- 반복 질의도 매번 파일 읽기
- 유사 질의 재사용 불가

#### After: Vector DB 기반 의미론적 검색

```
자연어 질의
    ↓
[Vector 검색 - 병렬 처리]
  ├─ schema_metadata 컬렉션 검색 (테이블/컬럼)
  ├─ business_knowledge 컬렉션 검색 (관계/규칙)
  ├─ query_patterns 컬렉션 검색 (성공 사례)
  └─ (< 1초, 메모리 기반)
    ↓
재사용 가능한 패턴 발견?
    ├─ YES → SQL 템플릿 재사용 (LLM 호출 불필요)
    └─ NO  → LLM에게 Context 제공 → SQL 생성
    ↓
SQL 실행
    ↓
성공 시 자동 학습 (Vector DB에 저장)
```

**장점**:
- ✅ 검색 속도 80-90% 향상
- ✅ 유사 질의 70% 재사용
- ✅ LLM 비용 60% 절감

### 4.3 메타데이터 구조 변경

#### Before: JSON 파일 기반

```
metadata/
└── {DB_SID}/
    └── {SCHEMA}/
        ├── table_summaries.json
        └── {TABLE}/
            └── unified_metadata.json

common_metadata/
└── {DB_SID}/
    ├── common_columns.json
    └── code_definitions.json
```

**문제**:
- 검색 시 모든 파일 순차 읽기
- 의미론적 검색 불가
- 유사도 계산 불가

#### After: Vector DB + JSON 하이브리드

```
data/
├── vector_db/ (ChromaDB - 신규)
│   ├── {DB_SID}_{SCHEMA}_schema/      (테이블/컬럼 Vector화)
│   ├── {DB_SID}_{SCHEMA}_knowledge/   (관계/규칙 Vector화)
│   ├── {DB_SID}_{SCHEMA}_patterns/    (성공 SQL 패턴)
│   └── {DB_SID}_{SCHEMA}_business/    (비즈니스 규칙)
│
├── metadata/ (기존 JSON 유지 - 백업용)
│   └── {DB_SID}/{SCHEMA}/...
│
└── common_metadata/ (기존 JSON 유지)
    └── {DB_SID}/...
```

**장점**:
- ✅ Vector 검색으로 빠른 응답
- ✅ 기존 JSON 호환성 유지
- ✅ 의미론적 유사도 계산
- ✅ 점진적 학습 가능

### 4.4 MCP Tools 변경

#### Before: 21개 Tools (모든 기능 포함)

```python
# DB 관리 (5개)
register_database_credentials
delete_database
load_tnsnames
list_available_databases
connect_database

# DB 탐색 (6개)
show_databases
show_schemas
show_tables
describe_table
show_procedures
show_procedure_source

# SQL 생성 (2개)
get_table_summaries_for_query
get_detailed_metadata_for_sql

# SQL 실행 (1개)
execute_sql

# 메타데이터 관리 (7개) ← 일부 Management로 이동
get_table_metadata
register_common_columns
register_code_values
view_common_metadata
extract_and_integrate_metadata
import_common_columns_csv      ← Management로 이동
import_code_definitions_csv    ← Management로 이동
import_table_info_csv          ← Management로 이동
generate_csv_from_schema       ← Management로 이동
```

#### After: MCP Tools (핵심만) + Management API

**MCP Tools (유지 - 17개)**:
```python
# DB 관리 (5개) - 모두 유지
register_database_credentials
delete_database
load_tnsnames
list_available_databases
connect_database

# DB 탐색 (6개) - 모두 유지
show_databases
show_schemas
show_tables
describe_table
show_procedures
show_procedure_source

# SQL 생성 (3개 - 개선)
generate_sql_from_question      ← 신규 (Vector 검색 통합)
execute_sql
provide_sql_feedback            ← 신규 (학습)

# 메타데이터 조회 (3개) - 읽기 전용만
get_table_metadata
view_common_metadata
get_learning_stats              ← 신규 (통계)
```

**Management API (신규 - REST API)**:
```python
# 파일 처리 (MCP에서 이동)
POST /api/metadata/{sid}/{schema}/import-csv
POST /api/metadata/{sid}/{schema}/generate-template
GET  /api/metadata/{sid}/{schema}/export-csv/{type}

# PowerBuilder 학습 (신규)
POST /api/learning/{sid}/{schema}/powerbuilder/upload
POST /api/learning/{sid}/{schema}/powerbuilder/analyze

# 패턴 관리 (신규)
GET    /api/learning/{sid}/{schema}/patterns
PUT    /api/learning/{sid}/{schema}/patterns/{id}
DELETE /api/learning/{sid}/{schema}/patterns/{id}

# 설정 관리 (신규)
GET /api/settings/{sid}/{schema}/sql-rules
PUT /api/settings/{sid}/{schema}/sql-rules

# 대시보드 (신규)
GET /api/dashboard/{sid}/{schema}/stats
GET /api/dashboard/{sid}/{schema}/recent-queries
```

### 4.5 사용자 워크플로우 변경

#### Before: CLI 중심

```
1. Claude Desktop 실행
2. MCP Tool로 tnsnames 로드
3. MCP Tool로 DB 연결
4. CSV 파일을 수동으로 특정 경로에 배치
5. MCP Tool로 CSV 임포트
6. MCP Tool로 스키마 추출
7. 자연어 질의 (5-10초 대기)
8. 결과 확인
```

**문제**:
- 파일 업로드 불편
- 진행 상황 모니터링 불가
- 학습 데이터 관리 어려움

#### After: Web UI + MCP 하이브리드

```
[초기 셋업 - Web UI 사용]
1. 브라우저에서 localhost:3000 접속
2. "DB 등록" 버튼 → DB 정보 입력
3. "CSV 업로드" → 드래그 앤 드롭
4. "PowerBuilder 학습" → .srw 파일 업로드
   → 진행률 실시간 표시 (10분 → 완료)
5. 대시보드에서 학습 결과 확인

[일상 사용 - Claude Code 사용]
1. Claude Code 실행
2. 자연어 질의: "지난달 VIP 고객 주문 내역"
3. 즉시 응답 (< 1초, Vector 검색)
4. SQL 자동 생성 및 실행
5. 결과 확인
```

**장점**:
- ✅ 직관적인 초기 셋업
- ✅ 실시간 모니터링
- ✅ 빠른 SQL 생성

### 4.6 성능 비교

| 항목 | Before | After | 개선 |
|------|--------|-------|------|
| **Stage 1 응답** | 5-10초 (JSON 파일 읽기) | < 1초 (Vector 검색) | 80-90% ↓ |
| **유사 질의** | 5-10초 (매번 동일) | 0.1초 (패턴 재사용) | 98% ↓ |
| **초기 셋업** | 2-3일 (수동 CSV 작성) | 2-3시간 (PB 자동 학습) | 90% ↓ |
| **LLM 호출** | 100% (매번 호출) | 40% (60% 재사용) | 60% ↓ |
| **메모리 사용** | 낮음 (파일 기반) | 중간 (Vector DB 로드) | +200MB |
| **디스크 사용** | 적음 (JSON만) | 많음 (Vector + JSON) | +500MB |

### 4.7 비용 비교 (월 1000회 질의 기준)

| 항목 | Before | After | 절감 |
|------|--------|-------|------|
| **LLM API 비용** | $50 (1000회 × $0.05) | $20 (400회 × $0.05) | $30 (60%) |
| **개발 시간** | 40시간 (초기 셋업) | 4시간 (PB 학습) | 36시간 (90%) |
| **서버 비용** | $0 (로컬) | $0 (로컬) | - |
| **총 비용** | $50/월 + 40시간 | $20/월 + 4시간 | 60% 절감 |

---

## 5. 3-Tier 아키텍처 설계

### 5.1 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────────┐
│ 로컬 머신 (Windows PC: D:\Project\mcp_db)                            │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Tier 1: MCP Server (stdio)                                 │    │
│  │                                                            │    │
│  │  Port: stdio (Claude Desktop 전용)                        │    │
│  │  Process: python src/mcp_server.py                        │    │
│  │                                                            │    │
│  │  [Tools - 17개]                                            │    │
│  │   - generate_sql_from_question() ⭐ (Vector 검색 통합)     │    │
│  │   - execute_sql()                                         │    │
│  │   - provide_sql_feedback() (학습)                         │    │
│  │   - show_databases/schemas/tables...                      │    │
│  │                                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓ ↑                                   │
│                    [Shared Core - 공통 로직]                        │
│           ┌──────────────────────────────────────────┐             │
│           │ OracleNLSQLCore                          │             │
│           │  - DatabaseManager                       │             │
│           │  - VectorDBManager ⭐ (ChromaDB)         │             │
│           │  - MetadataManager                       │             │
│           │  - LearningEngine ⭐ (PB 학습, 패턴)     │             │
│           └──────────────────────────────────────────┘             │
│                              ↓ ↑                                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Tier 2: Management Backend (FastAPI)                       │    │
│  │                                                            │    │
│  │  Port: 8000 (localhost:8000)                              │    │
│  │  Process: python src/management_api.py                    │    │
│  │                                                            │    │
│  │  [REST APIs]                                               │    │
│  │   - POST /api/learning/.../powerbuilder/upload            │    │
│  │   - POST /api/learning/.../powerbuilder/analyze ⭐        │    │
│  │   - POST /api/metadata/.../import-csv                     │    │
│  │   - GET  /api/learning/.../patterns                       │    │
│  │   - GET  /api/dashboard/.../stats                         │    │
│  │                                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓ ↑                                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Tier 3: Web UI (React)                                     │    │
│  │                                                            │    │
│  │  Port: 3000 (localhost:3000)                              │    │
│  │  Dev Server: npm start                                    │    │
│  │                                                            │    │
│  │  [Pages]                                                   │    │
│  │   - Dashboard (통계, 최근 쿼리)                            │    │
│  │   - Database Management (DB 등록/삭제)                    │    │
│  │   - Metadata Upload (CSV 업로드)                          │    │
│  │   - PowerBuilder Learning (PB 파일 업로드)                │    │
│  │   - Pattern Management (패턴 수정/삭제)                   │    │
│  │                                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ 공유 데이터 저장소 (로컬 파일 시스템)                       │    │
│  │                                                            │    │
│  │  D:\Project\mcp_db\data\                                  │    │
│  │   ├── vector_db/ ⭐ (ChromaDB Persistent)                 │    │
│  │   │   ├── {DB_SID}_{SCHEMA}_schema/                       │    │
│  │   │   ├── {DB_SID}_{SCHEMA}_knowledge/                    │    │
│  │   │   ├── {DB_SID}_{SCHEMA}_patterns/                     │    │
│  │   │   └── {DB_SID}_{SCHEMA}_business/                     │    │
│  │   │                                                        │    │
│  │   ├── metadata/ (기존 JSON - 백업/호환)                   │    │
│  │   │   └── {DB_SID}/{SCHEMA}/...                           │    │
│  │   │                                                        │    │
│  │   ├── common_metadata/ (기존 JSON 유지)                   │    │
│  │   │   └── {DB_SID}/...                                    │    │
│  │   │                                                        │    │
│  │   ├── credentials/ (Fernet 암호화)                        │    │
│  │   │   └── {DB_SID}.json.enc                               │    │
│  │   │                                                        │    │
│  │   └── powerbuilder/ (PB 소스 임시 저장)                   │    │
│  │       └── {DB_SID}/{SCHEMA}/...                           │    │
│  │                                                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5.2 Tier 1: MCP Server

#### 5.2.1 역할 (Responsibilities)

**핵심 역할**: Claude Desktop을 통한 SQL 생성 및 실행

1. **자연어 → SQL 변환**
   - Vector DB에서 Context 검색
   - LLM에게 최적 Context 제공
   - SQL 생성 및 검증

2. **DB 연결 및 조회**
   - Oracle DB 연결 관리
   - 스키마/테이블 탐색
   - SQL 실행

3. **실시간 학습**
   - SQL 실행 성공 시 자동 저장
   - 사용자 피드백 수집

#### 5.2.2 주요 Tools (17개)

**SQL 생성 관련 (3개 - 핵심)**:
```python
@server.call_tool()
async def generate_sql_from_question(
    database_sid: str,
    schema_name: str,
    user_question: str,
    auto_execute: bool = False,
    max_rows: int = 100
) -> dict:
    """
    자연어 질의 → SQL 생성 (Vector 검색 통합)

    내부 동작:
    1. Vector DB에서 Context 검색 (< 1초)
       - schema_metadata: 테이블/컬럼
       - knowledge: 관계/규칙
       - patterns: 유사 성공 사례

    2. 재사용 가능한 패턴 발견?
       - YES: SQL 템플릿 재사용 (LLM 호출 불필요)
       - NO: LLM에게 Context 제공 → SQL 생성

    3. auto_execute=True면 즉시 실행

    Returns:
        {
            "generated_sql": "SELECT ...",
            "execution_result": {...},
            "metadata": {
                "method": "pattern_reuse" or "llm_generation",
                "confidence": 0.95,
                "tables_used": ["ORDERS", "CUSTOMERS"]
            }
        }
    """
```

**DB 연결/조회 (11개 - 기존 유지)**:
```python
# DB 관리
register_database_credentials()
delete_database()
load_tnsnames()
list_available_databases()
connect_database()

# DB 탐색
show_databases()
show_schemas()
show_tables()
describe_table()
show_procedures()
show_procedure_source()
```

**SQL 실행 및 피드백 (2개)**:
```python
execute_sql()
provide_sql_feedback()  # 학습용
```

**통계 조회 (1개)**:
```python
get_learning_stats()
```

#### 5.2.3 실행 방식

```bash
# MCP 서버 실행 (Claude Desktop이 자동 실행)
cd D:\Project\mcp_db
venv\Scripts\python.exe -m src.mcp_server
```

**Claude Desktop 설정**:
```json
{
  "mcpServers": {
    "oracle-nlsql": {
      "command": "D:\\Project\\mcp_db\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server"],
      "cwd": "D:\\Project\\mcp_db",
      "env": {
        "PYTHONPATH": "D:\\Project\\mcp_db"
      }
    }
  }
}
```

### 5.3 Tier 2: Management Backend

#### 5.3.1 역할 (Responsibilities)

**핵심 역할**: 학습 및 관리 기능 전담

1. **PowerBuilder 학습**
   - PB 파일 업로드 및 저장
   - LLM을 이용한 자동 분석
   - SQL/관계/비즈니스 로직 추출
   - Vector DB에 저장

2. **메타데이터 관리**
   - CSV 파일 업로드 및 처리
   - Vector화 (임베딩 생성)
   - 메타데이터 CRUD

3. **패턴 관리**
   - 학습된 패턴 조회/수정/삭제
   - 신뢰도 기반 필터링
   - 일괄 관리

4. **모니터링 및 통계**
   - 대시보드 데이터 제공
   - 최근 쿼리 기록
   - 학습 진행 상황

#### 5.3.2 주요 REST API

**PowerBuilder 학습**:
```python
POST /api/learning/{db_sid}/{schema}/powerbuilder/upload
  - Request: multipart/form-data (파일들)
  - Response: { files: [...], task_id: "..." }

POST /api/learning/{db_sid}/{schema}/powerbuilder/analyze
  - Request: {}
  - Response: { task_id: "...", status: "processing" }
  - 백그라운드 작업 시작 (LLM 분석)

GET /api/tasks/{task_id}
  - Response: { status: "processing", progress: 45, ... }
```

**메타데이터 관리**:
```python
POST /api/metadata/{db_sid}/{schema}/import-csv
  - Request: { csv_type: "tables", file: File }
  - Response: { rows_imported: 100, vectorized: true }

GET /api/metadata/{db_sid}/{schema}/export-csv/{type}
  - Response: CSV 파일 다운로드
```

**패턴 관리**:
```python
GET /api/learning/{db_sid}/{schema}/patterns
  - Query: ?page=1&per_page=20&sort_by=confidence
  - Response: { items: [...], total: 150 }

DELETE /api/learning/{db_sid}/{schema}/patterns/{pattern_id}
  - Response: { success: true }
```

#### 5.3.3 실행 방식

```bash
# Management API 실행
cd D:\Project\mcp_db
venv\Scripts\python.exe src\management_api.py

# 또는 start_management.bat 실행
start_management.bat
```

### 5.4 Tier 3: Web UI

#### 5.4.1 역할 (Responsibilities)

**핵심 역할**: 사용자 친화적 관리 인터페이스

1. **대시보드**
   - 학습 통계 시각화
   - 최근 쿼리 목록
   - Vector DB 상태

2. **DB 관리**
   - DB 등록/삭제
   - 연결 테스트
   - 스키마 선택

3. **메타데이터 업로드**
   - CSV 드래그 앤 드롭
   - 업로드 진행률 표시
   - 검증 및 미리보기

4. **PowerBuilder 학습**
   - PB 파일 업로드
   - 실시간 진행 상황 (WebSocket)
   - 학습 결과 확인

5. **패턴 관리**
   - 테이블 형태로 패턴 목록
   - 검색/필터링/정렬
   - 패턴 수정/삭제

#### 5.4.2 주요 페이지

**1. Dashboard (/)**:
```tsx
<Dashboard>
  <StatsCards>
    - 총 학습 패턴 수
    - Vector DB 크기
    - 최근 7일 질의 수
    - 평균 응답 시간
  </StatsCards>

  <Charts>
    - 일별 질의 수 (Line Chart)
    - SQL 생성 방법 분포 (Pie Chart)
  </Charts>

  <RecentQueries>
    - 최근 10개 쿼리
    - 질문, SQL, 실행 시간, 결과
  </RecentQueries>
</Dashboard>
```

**2. Database Management (/databases)**:
```tsx
<DatabaseManagement>
  <DatabaseList>
    - 등록된 DB 목록
    - 연결 상태 표시
    - 삭제 버튼
  </DatabaseList>

  <AddDatabaseForm>
    - DB SID, Host, Port, Service
    - User, Password
    - "연결 테스트" 버튼
    - "등록" 버튼
  </AddDatabaseForm>
</DatabaseManagement>
```

**3. PowerBuilder Learning (/learning/powerbuilder)**:
```tsx
<PowerBuilderLearning>
  <FileUpload>
    - 드래그 앤 드롭 영역
    - .srw, .srd, .sru 파일
    - 업로드된 파일 목록
  </FileUpload>

  <AnalysisProgress>
    - 진행률 바 (WebSocket 실시간)
    - 현재 처리 중인 파일
    - 추출된 SQL/관계 수
  </AnalysisProgress>

  <Results>
    - 분석 완료 후 요약
    - 학습된 패턴 미리보기
  </Results>
</PowerBuilderLearning>
```

#### 5.4.3 기술 스택

```
Framework: React 18+
State: React Query (서버 상태 관리)
UI Library: Material-UI or Ant Design
Charts: Recharts or Chart.js
File Upload: react-dropzone
WebSocket: Socket.io-client
```

#### 5.4.3 실행 방식

```bash
# 개발 모드
cd D:\Project\mcp_db\web
npm start
# → http://localhost:3000

# 프로덕션 빌드
npm run build
# → build/ 폴더 생성
# → Management API가 정적 파일 서빙
```

### 5.5 Shared Core (공통 로직)

#### 5.5.1 OracleNLSQLCore 클래스

```python
# src/shared/core.py

class OracleNLSQLCore:
    """
    MCP Server와 Management Backend가 공유하는 핵심 로직

    역할:
    - DB 연결 관리
    - Vector DB 관리
    - 메타데이터 관리
    - 학습 엔진
    """

    def __init__(self, config_path: str = None):
        # 설정 로드
        self.config = self.load_config(config_path)

        # 로컬 디렉토리 설정
        self.data_dir = Path(self.config['data_dir'])
        self.vector_db_dir = self.data_dir / 'vector_db'
        self.metadata_dir = self.data_dir / 'metadata'
        self.credentials_dir = self.data_dir / 'credentials'

        # 매니저 초기화 (동일한 디렉토리 사용)
        self.db_manager = DatabaseManager(self.credentials_dir)
        self.vector_manager = VectorDBManager(self.vector_db_dir)
        self.metadata_manager = MetadataManager(self.metadata_dir)
        self.learning_engine = LearningEngine(
            vector_manager=self.vector_manager,
            metadata_manager=self.metadata_manager
        )
```

#### 5.5.2 공유 데이터 접근

```
MCP Server 실행
  ↓
OracleNLSQLCore 초기화
  ↓
vector_db_dir = D:\Project\mcp_db\data\vector_db
  ↓
ChromaDB 클라이언트 생성 (Persistent)
  ↓
데이터 읽기/쓰기

Management API 실행
  ↓
OracleNLSQLCore 초기화 (동일)
  ↓
vector_db_dir = D:\Project\mcp_db\data\vector_db (동일!)
  ↓
ChromaDB 클라이언트 생성 (Persistent)
  ↓
데이터 읽기/쓰기

→ 두 프로세스가 동일한 Vector DB 파일 접근
→ 자동 동기화 (파일 기반)
```

---

## 6. Vector DB 통합 설계

### 6.1 ChromaDB 선택 이유

| 기준 | ChromaDB | Pinecone | Weaviate | Milvus |
|------|----------|----------|----------|--------|
| **로컬 실행** | ✅ Persistent | ❌ 클라우드만 | ⚠️ 복잡 | ⚠️ 복잡 |
| **Python 통합** | ✅ 간단 | ✅ 간단 | ✅ 간단 | ⚠️ 중간 |
| **파일 기반 저장** | ✅ SQLite | ❌ | ❌ | ❌ |
| **임베딩 자동화** | ✅ 내장 | ⚠️ 수동 | ✅ 내장 | ⚠️ 수동 |
| **비용** | ✅ 무료 | ❌ 유료 | ✅ 무료 | ✅ 무료 |
| **학습 곡선** | ✅ 낮음 | ✅ 낮음 | ⚠️ 중간 | ❌ 높음 |

**결론**: ChromaDB가 로컬 실행, 파일 기반 저장, 간단한 사용성에서 최적

### 6.2 컬렉션 설계 (4개)

#### 6.2.1 schema_metadata (스키마 메타데이터)

**목적**: 테이블/컬럼 구조 정보 Vector화

**데이터 소스**:
- DB 스키마 자동 추출
- CSV 메타데이터 (table_info.csv, column_info.csv)

**Document 구조**:
```python
# 테이블 Document
{
    "document": """
    테이블: ORDERS
    한글명: 주문 정보
    설명: 고객 주문 내역을 저장하는 마스터 테이블
    용도: 주문 조회, 매출 분석, 배송 관리
    주요 컬럼: ORDER_ID(주문번호), CUST_ID(고객코드), AMOUNT(주문금액), ORDER_DATE(주문일자)
    연관 테이블: CUSTOMERS(고객), ORDER_DETAIL(주문상세), ORDER_STATUS(주문상태)
    """,

    "metadata": {
        "type": "table",
        "database_sid": "ORCL",
        "schema_name": "SCOTT",
        "table_name": "ORDERS",
        "table_comment": "주문 정보",
        "row_count": 15000,
        "source": "db_extraction"
    },

    "id": "ORCL_SCOTT_table_ORDERS"
}

# 컬럼 Document
{
    "document": """
    컬럼: ORDERS.ORDER_DATE
    한글명: 주문일자
    데이터 타입: DATE
    설명: 고객이 주문을 생성한 날짜
    비즈니스 규칙:
    - 오늘 날짜 이전이어야 함
    - 고객 생성일 이후여야 함
    사용 예시: WHERE ORDER_DATE >= TRUNC(SYSDATE, 'MM') (이번 달 주문)
    인덱스: IDX_ORDERS_DATE (단일 인덱스)
    """,

    "metadata": {
        "type": "column",
        "database_sid": "ORCL",
        "schema_name": "SCOTT",
        "table_name": "ORDERS",
        "column_name": "ORDER_DATE",
        "data_type": "DATE",
        "nullable": "N",
        "is_indexed": True,
        "source": "db_extraction + csv"
    },

    "id": "ORCL_SCOTT_column_ORDERS_ORDER_DATE"
}
```

**검색 예시**:
```python
# 사용자 질의: "주문 정보 조회"
results = schema_collection.query(
    query_texts=["주문 정보 조회"],
    n_results=5
)
# → ORDERS 테이블 및 관련 컬럼 반환
```

#### 6.2.2 business_knowledge (비즈니스 지식)

**목적**: 테이블 간 관계, 코드 정의, SQL 규칙 저장

**데이터 소스**:
- FK 관계 (DB 추출 또는 추론)
- CSV (code_definitions.csv)
- sql_rules.md

**Document 구조**:
```python
# 관계 Document
{
    "document": """
    관계: ORDERS.CUST_ID → CUSTOMERS.CUST_ID
    타입: N:1 (여러 주문 → 한 고객)
    설명: 주문은 반드시 고객과 연결되어야 함
    JOIN 예시:
    SELECT O.*, C.CUST_NAME
    FROM ORDERS O
    INNER JOIN CUSTOMERS C ON O.CUST_ID = C.CUST_ID

    신뢰도: 0.95
    사용 횟수: 147회
    """,

    "metadata": {
        "type": "relationship",
        "from_table": "ORDERS",
        "from_column": "CUST_ID",
        "to_table": "CUSTOMERS",
        "to_column": "CUST_ID",
        "cardinality": "N:1",
        "confidence": 0.95,
        "usage_count": 147,
        "source": "fk_constraint"
    },

    "id": "ORCL_SCOTT_rel_ORDERS_CUSTOMERS_CUST_ID"
}

# 코드 정의 Document
{
    "document": """
    코드 타입: 고객 등급
    컬럼: CUSTOMERS.GRADE
    코드값: VIP
    코드명: VIP 고객
    설명: 연간 구매액 1억원 이상의 우수 고객
    동의어: 프리미엄 고객, 우수 고객, 특별 회원
    사용 예시: WHERE CUSTOMERS.GRADE = 'VIP'
    """,

    "metadata": {
        "type": "code_definition",
        "code_type": "CUSTOMER_GRADE",
        "code_value": "VIP",
        "code_name": "VIP 고객",
        "column_name": "CUSTOMERS.GRADE",
        "synonyms": ["프리미엄 고객", "우수 고객", "특별 회원"],
        "source": "csv_import"
    },

    "id": "ORCL_SCOTT_code_CUSTOMER_GRADE_VIP"
}
```

#### 6.2.3 query_patterns (쿼리 패턴)

**목적**: 성공한 SQL 패턴 저장 및 재사용

**데이터 소스**:
- 실시간 학습 (사용자 질의 → SQL 생성 → 성공)
- PowerBuilder 소스 학습

**Document 구조**:
```python
{
    "document": """
    사용자 질문: 지난달 VIP 고객의 평균 주문액은?

    관련 테이블: ORDERS, CUSTOMERS

    생성된 SQL:
    SELECT AVG(O.AMOUNT) AS 평균주문액
    FROM ORDERS O
    INNER JOIN CUSTOMERS C ON O.CUST_ID = C.CUST_ID
    WHERE C.GRADE = 'VIP'
      AND O.ORDER_DATE >= TRUNC(ADD_MONTHS(SYSDATE, -1), 'MM')
      AND O.ORDER_DATE < TRUNC(SYSDATE, 'MM')

    실행 시간: 0.35초
    결과 행수: 1
    """,

    "metadata": {
        "type": "query_pattern",
        "user_question": "지난달 VIP 고객의 평균 주문액은?",
        "sql": "SELECT AVG(O.AMOUNT) ...",
        "tables_used": ["ORDERS", "CUSTOMERS"],
        "confidence": 0.92,
        "usage_count": 5,
        "success_rate": 1.0,
        "avg_execution_time_ms": 350,
        "created_at": "2025-01-07T10:30:00",
        "last_used_at": "2025-01-07T15:20:00",
        "source": "runtime_learning"
    },

    "id": "pattern_1704614400_abc123"
}
```

**재사용 로직**:
```python
# 새 질의: "이번달 VIP 고객의 평균 주문액은?"
results = patterns_collection.query(
    query_texts=["이번달 VIP 고객의 평균 주문액은?"],
    n_results=1
)

if results['distances'][0][0] < 0.1:  # 유사도 90% 이상
    # 기존 SQL 템플릿 재사용
    base_sql = results['metadatas'][0]['sql']

    # 날짜 부분만 수정 (경량 LLM 호출)
    modified_sql = await modify_date_condition(base_sql, "이번달")

    # LLM 호출 1회로 완료 (기존: 2회)
```

#### 6.2.4 business_rules (비즈니스 규칙)

**목적**: PowerBuilder에서 추출한 비즈니스 로직 저장

**데이터 소스**:
- PowerBuilder 소스 분석 (Computed Column, Validation Rule)

**Document 구조**:
```python
{
    "document": """
    비즈니스 규칙: 주문 금액 검증

    규칙 타입: Validation
    적용 대상: ORDERS.AMOUNT

    규칙 내용:
    - 주문 금액은 0보다 커야 함
    - 100만원 초과 주문은 관리자 승인 필요
    - 할인 적용 시 할인율은 50%를 초과할 수 없음

    SQL 표현:
    CHECK (AMOUNT > 0)

    비즈니스 로직:
    IF amount > 1000000 THEN
        requires_approval = TRUE
    END IF

    발견 위치: w_order_entry.srw (ue_validate 이벤트)
    """,

    "metadata": {
        "type": "business_rule",
        "rule_category": "validation",
        "target_column": "ORDERS.AMOUNT",
        "rule_description": "주문 금액 검증",
        "source": "powerbuilder_learning",
        "source_file": "w_order_entry.srw"
    },

    "id": "rule_order_amount_validation"
}
```

### 6.3 Vector화 프로세스

#### 6.3.1 초기 Vector화 (기존 메타데이터)

```python
@server.call_tool()
async def vectorize_existing_metadata(
    database_sid: str,
    schema_name: str
) -> dict:
    """
    기존 JSON 메타데이터를 Vector DB에 임베딩

    처리 순서:
    1. metadata/ 폴더의 JSON 파일 읽기
    2. common_metadata/ 폴더의 JSON 파일 읽기
    3. 각 항목을 Document로 변환
    4. ChromaDB에 임베딩 및 저장
    """

    # 1. 테이블 요약 Vector화
    summaries_path = metadata_dir / database_sid / schema_name / "table_summaries.json"
    with open(summaries_path) as f:
        summaries = json.load(f)

    schema_collection = chroma_client.get_or_create_collection(
        name=f"{database_sid}_{schema_name}_schema"
    )

    for table in summaries['summaries']:
        doc = f"""
        테이블: {table['table_name']}
        설명: {table.get('one_line_desc', '')}
        """

        schema_collection.add(
            documents=[doc],
            metadatas=[{
                'type': 'table',
                'table_name': table['table_name'],
                'source': 'existing_metadata'
            }],
            ids=[f"table_{table['table_name']}"]
        )

    # 2. 통합 메타데이터 Vector화 (각 테이블)
    for table_name in get_all_tables(database_sid, schema_name):
        unified_path = metadata_dir / database_sid / schema_name / table_name / "unified_metadata.json"

        if not unified_path.exists():
            continue

        with open(unified_path) as f:
            unified = json.load(f)

        # 컬럼별로 Vector화
        for column in unified['columns']:
            doc = f"""
            컬럼: {table_name}.{column['column_name']}
            한글명: {column.get('column_comment', '')}
            데이터 타입: {column['data_type']}
            """

            schema_collection.add(
                documents=[doc],
                metadatas=[{
                    'type': 'column',
                    'table_name': table_name,
                    'column_name': column['column_name'],
                    'data_type': column['data_type']
                }],
                ids=[f"column_{table_name}_{column['column_name']}"]
            )

    # 3. 공통 메타데이터 Vector화
    common_path = common_metadata_dir / database_sid

    # 코드 정의
    codes_path = common_path / "code_definitions.json"
    if codes_path.exists():
        with open(codes_path) as f:
            codes = json.load(f)

        knowledge_collection = chroma_client.get_or_create_collection(
            name=f"{database_sid}_{schema_name}_knowledge"
        )

        for code in codes:
            doc = f"""
            코드 타입: {code['code_type']}
            코드값: {code['code_value']}
            코드명: {code['code_name']}
            설명: {code.get('description', '')}
            """

            knowledge_collection.add(
                documents=[doc],
                metadatas=[{
                    'type': 'code_definition',
                    'code_type': code['code_type'],
                    'code_value': code['code_value']
                }],
                ids=[f"code_{code['code_type']}_{code['code_value']}"]
            )

    return {
        "tables_vectorized": len(summaries['summaries']),
        "columns_vectorized": count_columns,
        "codes_vectorized": len(codes) if codes_path.exists() else 0
    }
```

#### 6.3.2 실시간 Vector화 (학습)

```python
async def learn_from_successful_query(
    database_sid: str,
    schema_name: str,
    user_question: str,
    generated_sql: str,
    execution_result: dict
):
    """
    성공한 쿼리를 Vector DB에 자동 저장
    """

    patterns_collection = chroma_client.get_collection(
        name=f"{database_sid}_{schema_name}_patterns"
    )

    # 1. 유사 패턴 검색
    similar = patterns_collection.query(
        query_texts=[user_question],
        n_results=1
    )

    # 2. 유사도 90% 이상이면 기존 패턴 강화
    if similar and similar['distances'][0][0] < 0.1:
        existing_id = similar['ids'][0][0]
        existing_meta = similar['metadatas'][0][0]

        patterns_collection.update(
            ids=[existing_id],
            metadatas=[{
                **existing_meta,
                'usage_count': existing_meta.get('usage_count', 0) + 1,
                'confidence': min(1.0, existing_meta.get('confidence', 0.5) + 0.05)
            }]
        )

    # 3. 신규 패턴 저장
    else:
        doc = f"""
        사용자 질문: {user_question}
        관련 테이블: {', '.join(extract_tables(generated_sql))}
        생성된 SQL: {generated_sql}
        실행 시간: {execution_result['execution_time_ms']}ms
        """

        patterns_collection.add(
            documents=[doc],
            metadatas=[{
                'type': 'query_pattern',
                'user_question': user_question,
                'sql': generated_sql,
                'confidence': 0.7,
                'usage_count': 1,
                'source': 'runtime_learning'
            }],
            ids=[f"pattern_{int(time.time())}_{hash(user_question)}"]
        )
```

### 6.4 검색 최적화 전략

#### 6.4.1 통합 검색 (Integrated Search)

```python
async def search_integrated_context(
    database_sid: str,
    schema_name: str,
    user_question: str
) -> dict:
    """
    4개 컬렉션에서 병렬 검색하여 최적 Context 구성
    """

    # 4개 컬렉션
    schema_coll = get_collection(f"{database_sid}_{schema_name}_schema")
    knowledge_coll = get_collection(f"{database_sid}_{schema_name}_knowledge")
    patterns_coll = get_collection(f"{database_sid}_{schema_name}_patterns")
    rules_coll = get_collection(f"{database_sid}_{schema_name}_business_rules")

    # 병렬 검색
    schema_results = schema_coll.query(query_texts=[user_question], n_results=10)
    knowledge_results = knowledge_coll.query(query_texts=[user_question], n_results=5)
    pattern_results = patterns_coll.query(query_texts=[user_question], n_results=3)
    rules_results = rules_coll.query(query_texts=[user_question], n_results=5)

    # Context 구성
    context = {
        'tables': format_tables(schema_results, type='table'),
        'columns': format_columns(schema_results, type='column'),
        'relationships': format_relationships(knowledge_results, type='relationship'),
        'codes': format_codes(knowledge_results, type='code_definition'),
        'similar_patterns': format_patterns(pattern_results),
        'business_rules': format_rules(rules_results)
    }

    # 재사용 가능한 패턴 발견?
    reusable_pattern = None
    if pattern_results['distances'][0][0] < 0.1:  # 90% 이상 유사
        reusable_pattern = {
            'sql': pattern_results['metadatas'][0][0]['sql'],
            'confidence': pattern_results['metadatas'][0][0]['confidence'],
            'similarity': 1 - pattern_results['distances'][0][0]
        }

    return {
        'context': context,
        'reusable_pattern': reusable_pattern
    }
```

#### 6.4.2 캐싱 전략

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_table_context(database_sid: str, schema_name: str, table_name: str):
    """
    자주 조회되는 테이블 Context 캐싱

    효과: 동일 테이블 반복 조회 시 Vector 검색 생략
    """
    # Vector 검색 결과 캐싱
    pass
```

### 6.5 성능 벤치마크 목표

| 작업 | 현재 (JSON) | 목표 (Vector DB) | 개선 |
|------|-------------|------------------|------|
| **테이블 검색** | 5-10초 | < 0.5초 | 90% ↓ |
| **유사 패턴 검색** | 불가능 | < 0.1초 | - |
| **전체 Context 구성** | 5-10초 | < 1초 | 80% ↓ |
| **100개 테이블 환경** | 10-15초 | < 1초 | 90% ↓ |

---

## 7. PowerBuilder 학습 시스템

### 7.1 PowerBuilder 소스 분석 개요

#### 7.1.1 지원 파일 타입

| 파일 타입 | 확장자 | 내용 | 우선순위 |
|----------|--------|------|----------|
| **Window** | .srw | 화면 정의, Embedded SQL | 높음 |
| **DataWindow** | .srd | 데이터 조회 쿼리 | 매우 높음 |
| **UserObject** | .sru | 공통 로직, SQL | 중간 |
| **Function** | .srf | 함수 정의 | 낮음 |
| **SQL** | .sql | 순수 SQL | 높음 |

#### 7.1.2 추출 대상 지식

1. **SQL 쿼리**
   - SELECT, INSERT, UPDATE, DELETE 문
   - Cursor 기반 처리
   - Dynamic SQL 재구성

2. **테이블 관계**
   - JOIN 구문에서 관계 추론
   - FK가 없어도 실제 사용 패턴으로 관계 파악

3. **비즈니스 로직**
   - Validation Rule
   - Computed Column
   - IF/CASE 조건문

4. **자연어 매핑**
   - 한글 주석
   - 변수명 (ls_cust_name → 고객명)
   - DataWindow 컬럼 Display Name

### 7.2 LLM 기반 분석 프로세스

#### 7.2.1 전체 워크플로우

```
사용자: PB 파일 업로드 (Web UI)
    ↓
1. 파일 저장 (data/powerbuilder/)
    ↓
2. 파일 타입 감지 (.srw, .srd 등)
    ↓
3. 배치 그룹화 (작은 파일 5개씩)
    ↓
4. LLM 분석 요청 (Sonnet 모델)
   - DataWindow: SQL 추출
   - Window: Embedded SQL + 비즈니스 로직
   - UserObject: 공통 함수
    ↓
5. JSON 결과 파싱
    ↓
6. Vector DB에 저장
   - SQL → query_patterns
   - 관계 → business_knowledge
   - 규칙 → business_rules
    ↓
7. 진행 상황 실시간 업데이트 (WebSocket)
    ↓
완료: 학습 결과 요약 표시
```

#### 7.2.2 DataWindow 분석 프롬프트

```python
def create_datawindow_analysis_prompt(content: str, description: str) -> str:
    prompt = f"""
당신은 PowerBuilder DataWindow 전문가입니다.
다음 DataWindow 소스를 분석하여 SQL과 비즈니스 로직을 추출하세요.

[DataWindow 소스]
{content[:10000]}

[설명]
{description}

**추출 항목**:

1. **SQL 쿼리** (retrieve, select 구문)
2. **테이블 관계** (JOIN 구문 분석)
3. **컬럼 매핑** (DataWindow 컬럼명 → DB 컬럼명)
4. **필터 조건** (WHERE 절, Argument 조건)
5. **비즈니스 로직** (Computed Column, Validation Rule)

**출력 형식** (JSON):
```json
{{
  "sqls": [
    {{
      "type": "retrieve",
      "sql": "SELECT C.CUST_NAME, O.AMOUNT FROM ORDERS O JOIN CUSTOMERS C ...",
      "description": "고객별 주문 조회",
      "tables_used": ["CUSTOMERS", "ORDERS"],
      "arguments": ["as_cust_id", "ad_from_date"],
      "filters": [
        {{
          "column": "CUSTOMERS.GRADE",
          "condition": "= :as_grade",
          "natural_meaning": "고객 등급 필터"
        }}
      ]
    }}
  ],
  "relationships": [
    {{
      "from_table": "ORDERS",
      "from_column": "CUST_ID",
      "to_table": "CUSTOMERS",
      "to_column": "CUST_ID",
      "join_type": "INNER JOIN"
    }}
  ],
  "column_mappings": [
    {{
      "dw_column": "cust_name",
      "db_column": "CUSTOMERS.CUST_NAME",
      "display_name": "고객명"
    }}
  ],
  "business_logic": [
    {{
      "type": "computed_column",
      "name": "total_price",
      "expression": "quantity * unit_price",
      "description": "총 금액 계산"
    }}
  ]
}}
```

**중요**:
- Dynamic SQL도 최대한 재구성
- Argument(:as_cust_id)의 의미 파악
- 한글 주석 적극 활용
"""
    return prompt
```

#### 7.2.3 배치 처리 최적화

```python
async def analyze_pb_batch(pb_files: list[Path]) -> dict:
    """
    여러 PB 파일을 배치로 처리 (비용 절감)

    전략:
    - 작은 파일 (< 5KB): 5개씩 배치
    - 중간 파일 (5-20KB): 2개씩 배치
    - 큰 파일 (> 20KB): 개별 처리
    """

    results = {'sqls': [], 'relationships': [], 'business_logic': []}

    # 크기별 분류
    small = [f for f in pb_files if f.stat().st_size < 5000]
    medium = [f for f in pb_files if 5000 <= f.stat().st_size < 20000]
    large = [f for f in pb_files if f.stat().st_size >= 20000]

    # 작은 파일 배치 처리
    for i in range(0, len(small), 5):
        batch = small[i:i+5]
        batch_result = await llm_analyze_batch(batch, batch_size=5)
        results['sqls'].extend(batch_result['sqls'])
        results['relationships'].extend(batch_result['relationships'])
        # 진행률 업데이트
        progress = (i + 5) / len(pb_files) * 100
        await update_progress(progress)

    # 중간 파일 처리
    for i in range(0, len(medium), 2):
        batch = medium[i:i+2]
        batch_result = await llm_analyze_batch(batch, batch_size=2)
        results['sqls'].extend(batch_result['sqls'])
        # ...

    # 큰 파일 개별 처리
    for file in large:
        individual_result = await llm_analyze_individual(file)
        results['sqls'].extend(individual_result['sqls'])
        # ...

    return results
```

### 7.3 관계 추론 (FK 없는 환경)

#### 7.3.1 JOIN 패턴 분석

```python
def extract_relationships_from_sql(parsed_sql: dict) -> list[dict]:
    """
    SQL의 JOIN 구문에서 관계 추출

    예: SELECT ... FROM ORDERS O JOIN CUSTOMERS C ON O.CUST_ID = C.CUST_ID
    → ORDERS.CUST_ID ↔ CUSTOMERS.CUST_ID 관계 발견
    """

    relationships = []

    for join in parsed_sql.get('joins', []):
        # "O.CUST_ID = C.CUST_ID" 파싱
        on_condition = join['on_condition']
        match = re.match(r'(\w+)\.(\w+)\s*=\s*(\w+)\.(\w+)', on_condition)

        if match:
            left_alias, left_col, right_alias, right_col = match.groups()

            # 별칭 → 실제 테이블명
            left_table = resolve_alias(left_alias, parsed_sql)
            right_table = resolve_alias(right_alias, parsed_sql)

            relationships.append({
                'from_table': left_table,
                'from_column': left_col,
                'to_table': right_table,
                'to_column': right_col,
                'join_type': join['type'],
                'confidence': 0.85,
                'source': 'powerbuilder_sql'
            })

    return relationships
```

#### 7.3.2 데이터 샘플링 검증 (선택적)

```python
async def validate_relationship_by_sampling(
    database_sid: str,
    relationship: dict
) -> dict:
    """
    추론된 관계를 실제 데이터로 검증

    방법:
    1. 1000건 샘플링
    2. 매칭률 계산
    3. 80% 이상이면 유효한 관계로 판단
    """

    sql = f"""
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN b.{relationship['to_column']} IS NOT NULL THEN 1 ELSE 0 END) as matched
    FROM {relationship['from_table']} a
    LEFT JOIN {relationship['to_table']} b
        ON a.{relationship['from_column']} = b.{relationship['to_column']}
    WHERE ROWNUM <= 1000
    """

    result = await execute_sql(database_sid, sql)
    match_ratio = result['matched'] / result['total']

    relationship['validated'] = match_ratio > 0.8
    relationship['match_ratio'] = match_ratio

    return relationship
```

### 7.4 학습 결과 활용

#### 7.4.1 Vector DB 저장

```python
async def save_pb_learning_results(
    database_sid: str,
    schema_name: str,
    learning_results: dict
):
    """
    PowerBuilder 학습 결과를 Vector DB에 저장
    """

    # 1. SQL 패턴 저장
    patterns_coll = get_collection(f"{database_sid}_{schema_name}_patterns")

    for sql_info in learning_results['sqls']:
        doc = f"""
        {sql_info.get('description', 'SQL 쿼리')}
        소스: {sql_info.get('source_file', '')} (PowerBuilder)
        SQL: {sql_info['sql']}
        """

        patterns_coll.add(
            documents=[doc],
            metadatas=[{
                'type': 'query_pattern',
                'sql': sql_info['sql'],
                'description': sql_info.get('description', ''),
                'confidence': 0.8,
                'source': 'powerbuilder_learning'
            }],
            ids=[f"pb_pattern_{hash(sql_info['sql'])}"]
        )

    # 2. 관계 저장
    knowledge_coll = get_collection(f"{database_sid}_{schema_name}_knowledge")

    for rel in learning_results['relationships']:
        doc = f"""
        {rel['from_table']}.{rel['from_column']}는
        {rel['to_table']}.{rel['to_column']}와 연결됩니다.
        (PowerBuilder 소스에서 발견됨)
        """

        knowledge_coll.add(
            documents=[doc],
            metadatas=[{
                'type': 'relationship',
                'from_table': rel['from_table'],
                'from_column': rel['from_column'],
                'to_table': rel['to_table'],
                'to_column': rel['to_column'],
                'confidence': rel.get('confidence', 0.85),
                'source': 'powerbuilder_learning'
            }],
            ids=[f"pb_rel_{rel['from_table']}_{rel['to_table']}"]
        )

    # 3. 비즈니스 규칙 저장
    rules_coll = get_collection(f"{database_sid}_{schema_name}_business_rules")

    for logic in learning_results['business_logic']:
        doc = f"""
        비즈니스 규칙: {logic.get('description', '')}
        타입: {logic['type']}
        내용: {logic.get('expression', logic.get('rule', ''))}
        """

        rules_coll.add(
            documents=[doc],
            metadatas=[{
                'type': 'business_rule',
                'rule_type': logic['type'],
                'description': logic.get('description', ''),
                'source': 'powerbuilder_learning'
            }],
            ids=[f"pb_rule_{hash(doc)}"]
        )
```

#### 7.4.2 초기 셋업 시간 단축 효과

**Before (수동)**:
```
1. PowerBuilder 소스 검토: 8시간
2. SQL 추출 및 정리: 8시간
3. 관계 파악 및 문서화: 8시간
4. CSV 작성: 8시간
5. CSV 임포트 및 검증: 4시간
---
총: 36시간 (4.5일)
```

**After (자동)**:
```
1. PB 파일 업로드: 5분
2. LLM 분석 (100개 파일): 15-20분
3. Vector DB 저장: 2-3분
4. 결과 검증: 30분
---
총: 40분 (90% 단축!)
```

### 7.5 제약사항 및 한계

| 항목 | 제약사항 | 해결 방안 |
|------|----------|-----------|
| **LLM 정확도** | 85-90% (완벽하지 않음) | 사용자 검증 UI 제공 |
| **복잡한 Dynamic SQL** | 재구성 실패 가능 | 수동 보정 기능 |
| **한글 인코딩** | EUC-KR → UTF-8 변환 오류 | 자동 인코딩 감지 |
| **비용** | 100개 파일 → $2-3 | 배치 처리로 최적화 |

---

**(Part 3 완료 - 다음 Part에서 계속됩니다)**

---

## **Part 4: 기능 명세 & 데이터 구조**

---

## **8. 기능 명세 (Detailed Feature Specifications)**

### 8.1 MCP Server 기능 (21개 Tools 유지)

#### 8.1.1 연결 관리 (Connection Management)

##### **Tool: `register_database_credentials`**
```python
{
    "name": "register_database_credentials",
    "description": "DB 접속 정보를 암호화하여 저장",
    "inputSchema": {
        "type": "object",
        "properties": {
            "database_sid": {"type": "string", "description": "Database SID"},
            "host": {"type": "string", "description": "호스트 주소"},
            "port": {"type": "integer", "description": "포트 번호"},
            "service_name": {"type": "string", "description": "서비스 이름"},
            "user": {"type": "string", "description": "사용자 이름"},
            "password": {"type": "string", "description": "비밀번호"}
        },
        "required": ["database_sid", "host", "port", "service_name", "user", "password"]
    }
}
```

**동작 흐름**:
1. 입력 받은 password를 Fernet으로 암호화
2. `~/.oracle-nlsql/connections/{database_sid}.json`에 저장
3. Vector DB 디렉토리 자동 생성: `~/.oracle-nlsql/vectordb/{database_sid}/`
4. 성공 메시지 반환

**내부 구현**:
```python
from cryptography.fernet import Fernet
import json
from pathlib import Path

def register_database_credentials(database_sid, host, port, service_name, user, password):
    # 1. 암호화
    key = load_or_create_encryption_key()
    fernet = Fernet(key)
    encrypted_pw = fernet.encrypt(password.encode()).decode()

    # 2. 저장
    conn_data = {
        "host": host,
        "port": port,
        "service_name": service_name,
        "user": user,
        "encrypted_password": encrypted_pw,
        "created_at": datetime.now().isoformat()
    }

    conn_path = Path.home() / '.oracle-nlsql' / 'connections' / f'{database_sid}.json'
    conn_path.parent.mkdir(parents=True, exist_ok=True)

    with open(conn_path, 'w', encoding='utf-8') as f:
        json.dump(conn_data, f, indent=2)

    # 3. Vector DB 디렉토리 생성
    vectordb_path = Path.home() / '.oracle-nlsql' / 'vectordb' / database_sid
    vectordb_path.mkdir(parents=True, exist_ok=True)

    return f"✅ Database '{database_sid}' registered successfully"
```

##### **Tool: `connect_database`**
```python
{
    "name": "connect_database",
    "description": "특정 DB에 연결 (tnsnames에서 호스트/포트/서비스명 자동 로드)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "database_sid": {"type": "string"},
            "user": {"type": "string"},
            "password": {"type": "string"}
        },
        "required": ["database_sid", "user", "password"]
    }
}
```

**동작 흐름**:
1. `tnsnames.ora` 캐시에서 연결 정보 조회
2. oracledb 연결 풀 생성 (min=2, max=10, increment=1)
3. 연결 테스트 쿼리 실행: `SELECT 1 FROM DUAL`
4. 성공 시 현재 세션에 연결 저장

---

#### 8.1.2 메타데이터 관리

##### **Tool: `extract_and_integrate_metadata`**
```python
{
    "name": "extract_and_integrate_metadata",
    "description": "DB 스키마 추출 및 공통 메타데이터 통합",
    "inputSchema": {
        "type": "object",
        "properties": {
            "database_sid": {"type": "string"},
            "schema_name": {"type": "string"},
            "table_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "테이블 이름 목록 (선택)"
            },
            "table_info_csv_path": {
                "type": "string",
                "description": "테이블 정보 CSV 경로 (선택)"
            }
        },
        "required": ["database_sid", "schema_name"]
    }
}
```

**동작 흐름**:
1. **DB에서 메타데이터 추출**:
   ```sql
   -- 테이블 정보
   SELECT
       table_name,
       comments AS table_description
   FROM all_tab_comments
   WHERE owner = :schema_name
   AND table_name IN (:table_names)

   -- 컬럼 정보
   SELECT
       c.table_name,
       c.column_name,
       c.data_type,
       c.data_length,
       c.nullable,
       cc.comments AS column_description
   FROM all_tab_columns c
   LEFT JOIN all_col_comments cc
       ON c.owner = cc.owner
       AND c.table_name = cc.table_name
       AND c.column_name = cc.column_name
   WHERE c.owner = :schema_name
   ORDER BY c.table_name, c.column_id
   ```

2. **공통 메타데이터 병합**:
   - `common_columns.json`에서 컬럼 한글명, 설명 로드
   - `code_definitions.json`에서 코드값 매핑 로드
   - DB 메타데이터와 병합

3. **Vector DB에 저장**:
   ```python
   # ChromaDB schema collection에 저장
   for table in tables:
       doc = f"""
       테이블: {table['name']}
       한글명: {table['korean_name']}
       설명: {table['description']}

       컬럼:
       {format_columns(table['columns'])}
       """

       schema_coll.add(
           documents=[doc],
           metadatas=[{
               'type': 'table',
               'table_name': table['name'],
               'schema': schema_name,
               'source': 'db_extraction'
           }],
           ids=[f"{database_sid}_{schema_name}_table_{table['name']}"]
       )
   ```

4. **로컬 파일 저장** (백업용):
   - `~/.oracle-nlsql/metadata/{database_sid}/{schema_name}/tables.json`

**결과 예시**:
```json
{
    "extracted_tables": 25,
    "integrated_columns": 180,
    "code_mappings": 15,
    "vectordb_documents": 25,
    "extraction_time": "2.3s",
    "status": "success"
}
```

##### **Tool: `get_table_summaries_for_query`** (Stage 1)
```python
{
    "name": "get_table_summaries_for_query",
    "description": "자연어 질의를 위한 테이블 요약 조회 (Vector 검색)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "database_sid": {"type": "string"},
            "schema_name": {"type": "string"}
        },
        "required": ["database_sid", "schema_name"]
    }
}
```

**동작 흐름**:
1. **Vector DB에서 테이블 요약 검색**:
   ```python
   # ChromaDB에서 모든 테이블 요약 로드
   schema_coll = chroma_client.get_collection(
       name=f"{database_sid}_{schema_name}_schema"
   )

   results = schema_coll.get(
       where={"type": "table"},
       include=["documents", "metadatas"]
   )

   summaries = []
   for doc, meta in zip(results['documents'], results['metadatas']):
       summaries.append({
           'table_name': meta['table_name'],
           'summary': doc.split('\n\n')[0],  # 첫 단락만 (테이블명, 한글명, 설명)
           'column_count': doc.count('컬럼명:')
       })

   return summaries
   ```

2. **결과 포맷**:
   ```json
   [
       {
           "table_name": "ORDERS",
           "korean_name": "주문 정보",
           "description": "고객 주문 내역을 저장하는 마스터 테이블",
           "column_count": 12,
           "key_columns": ["ORDER_ID", "CUSTOMER_ID", "ORDER_DATE"]
       },
       {
           "table_name": "CUSTOMERS",
           "korean_name": "고객 정보",
           "description": "고객 기본 정보 관리",
           "column_count": 8,
           "key_columns": ["CUSTOMER_ID", "CUSTOMER_NAME"]
       }
   ]
   ```

**사용 예시**:
```
User: "최근 1주일간 주문 현황을 보여줘"

Claude:
1. get_table_summaries_for_query로 전체 테이블 요약 로드
2. LLM이 "주문"과 관련된 테이블 식별: ORDERS, ORDER_ITEMS
3. get_detailed_metadata_for_sql(table_names=['ORDERS', 'ORDER_ITEMS'])로 상세 정보 로드
4. SQL 생성
```

##### **Tool: `get_detailed_metadata_for_sql`** (Stage 2)
```python
{
    "name": "get_detailed_metadata_for_sql",
    "description": "SQL 생성을 위한 상세 메타데이터 조회 (Vector 검색)",
    "inputSchema": {
        "type": "object",
        "properties": {
            "database_sid": {"type": "string"},
            "schema_name": {"type": "string"},
            "table_names": {
                "type": "array",
                "items": {"type": "string"},
                "description": "상세 정보가 필요한 테이블 목록"
            }
        },
        "required": ["database_sid", "schema_name", "table_names"]
    }
}
```

**동작 흐름**:
1. **Vector DB에서 상세 메타데이터 검색**:
   ```python
   detailed_metadata = []

   for table_name in table_names:
       # 1. 테이블 기본 정보
       table_doc = schema_coll.get(
           ids=[f"{database_sid}_{schema_name}_table_{table_name}"]
       )

       # 2. 관련 패턴 검색 (Vector 검색)
       pattern_results = patterns_coll.query(
           query_texts=[f"테이블: {table_name}"],
           n_results=5,
           where={"table_name": table_name}
       )

       # 3. 비즈니스 규칙 검색
       rules_results = rules_coll.query(
           query_texts=[f"테이블: {table_name}"],
           n_results=3
       )

       detailed_metadata.append({
           'table': parse_table_doc(table_doc),
           'common_patterns': pattern_results['documents'],
           'business_rules': rules_results['documents']
       })

   return detailed_metadata
   ```

2. **결과 예시**:
   ```json
   {
       "table_name": "ORDERS",
       "korean_name": "주문 정보",
       "columns": [
           {
               "name": "ORDER_ID",
               "korean_name": "주문번호",
               "type": "VARCHAR2(20)",
               "nullable": false,
               "description": "주문 고유 식별자"
           },
           {
               "name": "ORDER_STATUS",
               "korean_name": "주문상태",
               "type": "VARCHAR2(2)",
               "nullable": false,
               "code_values": {
                   "01": "주문접수",
                   "02": "결제완료",
                   "03": "배송중",
                   "04": "배송완료"
               }
           }
       ],
       "common_patterns": [
           "최근 주문: WHERE ORDER_DATE >= SYSDATE - 7",
           "완료된 주문: WHERE ORDER_STATUS = '04'"
       ],
       "business_rules": [
           "주문 총액 = SUM(주문상세.수량 * 주문상세.단가)",
           "유효한 주문: ORDER_STATUS IN ('01','02','03','04')"
       ]
   }
   ```

---

#### 8.1.3 SQL 실행 및 학습

##### **Tool: `execute_sql`**
```python
{
    "name": "execute_sql",
    "description": "SQL 쿼리 실행",
    "inputSchema": {
        "type": "object",
        "properties": {
            "database_sid": {"type": "string"},
            "sql": {"type": "string", "description": "실행할 SQL"},
            "max_rows": {
                "type": "integer",
                "description": "최대 조회 행 수",
                "default": 100
            }
        },
        "required": ["database_sid", "sql"]
    }
}
```

**동작 흐름**:
1. **SQL 실행**:
   ```python
   import oracledb

   def execute_sql(database_sid, sql, max_rows=100):
       conn = get_connection(database_sid)
       cursor = conn.cursor()

       # 1. SQL 실행
       start_time = time.time()
       cursor.execute(sql)

       # 2. 결과 페치
       if sql.strip().upper().startswith('SELECT'):
           columns = [desc[0] for desc in cursor.description]
           rows = cursor.fetchmany(max_rows)

           execution_time = time.time() - start_time

           result = {
               'columns': columns,
               'rows': [dict(zip(columns, row)) for row in rows],
               'row_count': len(rows),
               'execution_time': f"{execution_time:.2f}s",
               'has_more': cursor.rowcount > max_rows
           }
       else:
           conn.commit()
           result = {
               'affected_rows': cursor.rowcount,
               'status': 'success'
           }

       cursor.close()
       return result
   ```

2. **쿼리 패턴 학습** (자동):
   ```python
   # execute_sql 성공 시 자동으로 패턴 저장
   if result['status'] == 'success' and is_select_query(sql):
       save_query_pattern(database_sid, schema_name, sql, context)
   ```

**쿼리 패턴 저장 함수**:
```python
def save_query_pattern(database_sid, schema_name, sql, context):
    """
    성공한 쿼리를 Vector DB에 패턴으로 저장
    """
    patterns_coll = chroma_client.get_collection(
        name=f"{database_sid}_{schema_name}_patterns"
    )

    # SQL 파싱
    tables = extract_tables_from_sql(sql)
    conditions = extract_where_conditions(sql)

    # 자연어 설명 생성
    description = f"""
    질의: {context.get('user_query', '')}
    테이블: {', '.join(tables)}
    조건: {', '.join(conditions)}
    """

    patterns_coll.add(
        documents=[description],
        metadatas=[{
            'type': 'query_pattern',
            'sql': sql,
            'tables': tables,
            'timestamp': datetime.now().isoformat()
        }],
        ids=[f"pattern_{hash(sql)}"]
    )
```

---

#### 8.1.4 기타 필수 Tools (간략 명세)

| Tool | 설명 | 주요 기능 |
|------|------|----------|
| **`delete_database`** | 등록된 DB 삭제 | 접속 정보 + Vector DB 전체 삭제 |
| **`load_tnsnames`** | tnsnames.ora 파싱 | DB 목록 추출 및 캐싱 |
| **`list_available_databases`** | DB 목록 조회 | tnsnames 파싱 결과 반환 |
| **`show_databases`** | 등록된 DB 목록 | `~/.oracle-nlsql/connections/` 스캔 |
| **`show_connection_status`** | 연결 상태 보고 | 접속 가능 여부 체크 |
| **`show_schemas`** | 스키마 목록 조회 | `SELECT username FROM all_users` |
| **`show_tables`** | 테이블 목록 조회 | `SELECT table_name FROM all_tables WHERE owner = :schema` |
| **`describe_table`** | 테이블 구조 조회 | 컬럼, 타입, Nullable, 코멘트 |
| **`show_procedures`** | 프로시저 목록 | `SELECT object_name FROM all_procedures` |
| **`show_procedure_source`** | 프로시저 소스 조회 | `SELECT text FROM all_source` |
| **`view_common_metadata`** | 공통 메타데이터 조회 | `common_columns.json` + `code_definitions.json` |
| **`view_sql_rules`** | SQL 작성 규칙 조회 | `sql_rules.md` 파일 반환 |
| **`update_sql_rules`** | SQL 규칙 업데이트 | Markdown 형식으로 저장 |

---

### 8.2 Management Backend 기능 (FastAPI REST API)

#### 8.2.1 PowerBuilder 분석 API

##### **POST /api/powerbuilder/analyze**

**요청**:
```json
{
    "database_sid": "ORCL",
    "schema_name": "SCOTT",
    "files": [
        {
            "filename": "order_list.srd",
            "content": "release 9;\ndatawindow(...)",
            "file_type": "datawindow"
        }
    ],
    "options": {
        "extract_sql": true,
        "extract_relationships": true,
        "extract_business_logic": true,
        "save_to_vectordb": true
    }
}
```

**응답**:
```json
{
    "job_id": "pb_analysis_20250307_123456",
    "status": "processing",
    "total_files": 1,
    "estimated_time": "2 minutes",
    "progress_url": "/api/powerbuilder/analyze/pb_analysis_20250307_123456"
}
```

**내부 처리 흐름**:
```python
from fastapi import FastAPI, BackgroundTasks
import asyncio

app = FastAPI()

@app.post("/api/powerbuilder/analyze")
async def analyze_powerbuilder(
    request: PBAnalysisRequest,
    background_tasks: BackgroundTasks
):
    # 1. Job 생성
    job_id = create_job_id()

    # 2. 백그라운드 작업 등록
    background_tasks.add_task(
        process_powerbuilder_files,
        job_id,
        request.database_sid,
        request.schema_name,
        request.files,
        request.options
    )

    return {
        "job_id": job_id,
        "status": "processing",
        "total_files": len(request.files)
    }

async def process_powerbuilder_files(job_id, database_sid, schema_name, files, options):
    """
    PowerBuilder 파일 분석 (비동기 백그라운드 작업)
    """
    total = len(files)
    results = []

    # 배치 크기 결정
    batches = create_batches(files)  # 파일 크기별로 배치 생성

    for batch_idx, batch in enumerate(batches):
        # LLM 호출 (Claude Sonnet)
        analysis_results = await analyze_batch_with_llm(batch, options)

        # Vector DB 저장
        if options.save_to_vectordb:
            await save_to_vectordb(
                database_sid,
                schema_name,
                analysis_results
            )

        # 진행 상황 업데이트
        update_job_progress(
            job_id,
            processed=len(results) + len(batch),
            total=total,
            status='processing'
        )

        results.extend(analysis_results)

    # 작업 완료
    update_job_progress(job_id, total, total, status='completed', results=results)
```

##### **GET /api/powerbuilder/analyze/{job_id}**

**응답 (진행 중)**:
```json
{
    "job_id": "pb_analysis_20250307_123456",
    "status": "processing",
    "progress": {
        "processed": 15,
        "total": 50,
        "percentage": 30,
        "current_file": "customer_detail.srd"
    },
    "elapsed_time": "1m 23s"
}
```

**응답 (완료)**:
```json
{
    "job_id": "pb_analysis_20250307_123456",
    "status": "completed",
    "progress": {
        "processed": 50,
        "total": 50,
        "percentage": 100
    },
    "elapsed_time": "3m 45s",
    "results": {
        "extracted_sqls": 82,
        "identified_tables": 35,
        "relationships": 48,
        "business_rules": 23,
        "vectordb_documents": 153
    },
    "download_url": "/api/powerbuilder/download/pb_analysis_20250307_123456"
}
```

---

#### 8.2.2 CSV 업로드 API

##### **POST /api/metadata/upload-csv**

**요청** (multipart/form-data):
```
database_sid: ORCL
schema_name: SCOTT
csv_type: common_columns | code_definitions | table_info
file: <binary CSV data>
```

**응답**:
```json
{
    "status": "success",
    "csv_type": "common_columns",
    "rows_imported": 120,
    "validation": {
        "valid_rows": 118,
        "invalid_rows": 2,
        "errors": [
            {
                "row": 45,
                "error": "Missing required field: korean_name"
            },
            {
                "row": 67,
                "error": "Invalid data_type: VARCHAR3"
            }
        ]
    },
    "vectordb_updated": true
}
```

**내부 처리**:
```python
from fastapi import UploadFile
import pandas as pd

@app.post("/api/metadata/upload-csv")
async def upload_csv(
    database_sid: str,
    schema_name: str,
    csv_type: str,
    file: UploadFile
):
    # 1. CSV 파싱
    df = pd.read_csv(file.file, encoding='utf-8-sig')

    # 2. 검증
    validation = validate_csv(df, csv_type)

    if validation['invalid_rows'] > 0:
        return {
            "status": "partial_success",
            "validation": validation
        }

    # 3. 저장
    if csv_type == 'common_columns':
        save_common_columns(database_sid, df)
    elif csv_type == 'code_definitions':
        save_code_definitions(database_sid, df)
    elif csv_type == 'table_info':
        save_table_info(database_sid, schema_name, df)

    # 4. Vector DB 업데이트
    update_vectordb_from_csv(database_sid, schema_name, df, csv_type)

    return {
        "status": "success",
        "rows_imported": len(df),
        "validation": validation,
        "vectordb_updated": True
    }
```

---

#### 8.2.3 Vector DB 관리 API

##### **GET /api/vectordb/stats**

**요청**:
```
GET /api/vectordb/stats?database_sid=ORCL&schema_name=SCOTT
```

**응답**:
```json
{
    "database_sid": "ORCL",
    "schema_name": "SCOTT",
    "collections": {
        "schema_metadata": {
            "document_count": 125,
            "last_updated": "2025-03-07T14:23:15",
            "size_mb": 2.3
        },
        "business_knowledge": {
            "document_count": 48,
            "last_updated": "2025-03-07T12:10:30",
            "size_mb": 0.8
        },
        "query_patterns": {
            "document_count": 312,
            "last_updated": "2025-03-07T15:45:22",
            "size_mb": 1.2
        },
        "business_rules": {
            "document_count": 67,
            "last_updated": "2025-03-06T09:15:00",
            "size_mb": 0.5
        }
    },
    "total_documents": 552,
    "total_size_mb": 4.8
}
```

##### **POST /api/vectordb/search**

**요청**:
```json
{
    "database_sid": "ORCL",
    "schema_name": "SCOTT",
    "query": "고객별 주문 총액을 조회하는 방법",
    "collection": "query_patterns",
    "top_k": 5
}
```

**응답**:
```json
{
    "results": [
        {
            "document": "질의: 고객별 주문 통계\n테이블: CUSTOMERS, ORDERS\n조건: GROUP BY CUSTOMER_ID",
            "metadata": {
                "type": "query_pattern",
                "sql": "SELECT c.customer_name, SUM(o.order_amount) FROM customers c JOIN orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.customer_name",
                "tables": ["CUSTOMERS", "ORDERS"]
            },
            "distance": 0.23,
            "similarity": 0.77
        }
    ]
}
```

##### **DELETE /api/vectordb/clear**

**요청**:
```json
{
    "database_sid": "ORCL",
    "schema_name": "SCOTT",
    "collection": "query_patterns"  // 선택사항 (없으면 전체 삭제)
}
```

**응답**:
```json
{
    "status": "success",
    "deleted_collections": ["query_patterns"],
    "deleted_documents": 312
}
```

---

### 8.3 Web UI 기능 (React + TypeScript)

#### 8.3.1 대시보드 화면

**화면 구성**:
```
+----------------------------------------------------------+
|  [Oracle NLSQL MCP Management]           [User Profile]  |
+----------------------------------------------------------+
|  Dashboard  |  Databases  |  Metadata  |  PowerBuilder  |
+----------------------------------------------------------+
|                                                          |
|  📊 시스템 현황                                          |
|  +----------------------------------------------------+  |
|  | 등록된 DB: 3개     | Vector DB 크기: 12.5 MB      |  |
|  | 메타데이터: 450개  | 학습된 패턴: 1,245개         |  |
|  +----------------------------------------------------+  |
|                                                          |
|  🗄️ 데이터베이스 목록                                   |
|  +----------------------------------------------------+  |
|  | ORCL (운영)        | ✅ Connected | Manage | Delete |  |
|  | DEV  (개발)        | ⚠️ Not Connected | Connect    |  |
|  | TEST (테스트)      | ✅ Connected | Manage | Delete |  |
|  +----------------------------------------------------+  |
|                                                          |
|  📈 최근 활동                                            |
|  +----------------------------------------------------+  |
|  | 2025-03-07 15:45 | ORCL.SCOTT | SQL 실행 성공      |  |
|  | 2025-03-07 14:23 | ORCL.SCOTT | 메타데이터 추출    |  |
|  | 2025-03-07 12:10 | DEV.HR     | PB 분석 완료       |  |
|  +----------------------------------------------------+  |
+----------------------------------------------------------+
```

**주요 기능**:
- 등록된 데이터베이스 연결 상태 실시간 모니터링
- Vector DB 통계 (문서 수, 크기, 최근 업데이트)
- 최근 작업 이력 (SQL 실행, 메타데이터 추출, PB 분석)

---

#### 8.3.2 메타데이터 관리 화면

**화면 구성**:
```
+----------------------------------------------------------+
|  Metadata Management - ORCL.SCOTT                        |
+----------------------------------------------------------+
|  [공통 컬럼] [코드 정의] [테이블 정보]                   |
+----------------------------------------------------------+
|                                                          |
|  📤 CSV 업로드                                           |
|  +----------------------------------------------------+  |
|  | 파일 선택: [Browse...] common_columns.csv          |  |
|  | CSV 타입: [Common Columns ▼]                       |  |
|  |                                    [Upload & Apply] |  |
|  +----------------------------------------------------+  |
|                                                          |
|  📋 현재 공통 컬럼 (120개)              [Download CSV]   |
|  +----------------------------------------------------+  |
|  | 컬럼명        | 한글명   | 타입      | 설명         |  |
|  |--------------|----------|-----------|---------------|  |
|  | CUSTOMER_ID  | 고객번호 | VARCHAR2  | 고객 고유 ID  |  |
|  | ORDER_DATE   | 주문일자 | DATE      | 주문 등록 일자|  |
|  | STATUS       | 상태     | VARCHAR2  | 처리 상태     |  |
|  +----------------------------------------------------+  |
|  [1] [2] [3] ... [12]                Page 1 of 12      |  |
+----------------------------------------------------------+
```

**CSV 업로드 플로우**:
1. 파일 선택 → 2. CSV 타입 선택 → 3. 업로드 → 4. 검증 결과 표시 → 5. 적용

**검증 결과 모달**:
```
+------------------------------------------+
|  ✅ CSV 검증 완료                        |
+------------------------------------------+
|  유효한 행: 118개                        |
|  오류 발생: 2개                          |
|                                          |
|  ❌ Row 45: Missing field 'korean_name'  |
|  ❌ Row 67: Invalid data_type 'VARCHAR3' |
|                                          |
|  [오류 수정 후 재업로드] [무시하고 계속] |
+------------------------------------------+
```

---

#### 8.3.3 PowerBuilder 분석 화면

**화면 구성**:
```
+----------------------------------------------------------+
|  PowerBuilder Source Analysis                            |
+----------------------------------------------------------+
|  Database: [ORCL ▼]  Schema: [SCOTT ▼]                  |
+----------------------------------------------------------+
|                                                          |
|  📁 파일 업로드                                          |
|  +----------------------------------------------------+  |
|  | Drag & Drop PowerBuilder files here                |  |
|  | or click to browse (.srd, .srw, .sru, .srf)        |  |
|  |                                                    |  |
|  | 📄 order_list.srd (25 KB)               [Remove]  |  |
|  | 📄 customer_detail.srd (18 KB)          [Remove]  |  |
|  | 📄 product_master.srw (42 KB)           [Remove]  |  |
|  +----------------------------------------------------+  |
|                                                          |
|  ⚙️ 분석 옵션                                            |
|  +----------------------------------------------------+  |
|  | ☑ SQL 추출                                         |  |
|  | ☑ 테이블 관계 추론                                 |  |
|  | ☑ 비즈니스 로직 추출                               |  |
|  | ☑ Vector DB에 자동 저장                            |  |
|  +----------------------------------------------------+  |
|                                                          |
|                              [Start Analysis]            |
+----------------------------------------------------------+
```

**분석 진행 중 화면**:
```
+----------------------------------------------------------+
|  🔄 분석 진행 중...                                      |
+----------------------------------------------------------+
|  [████████████████░░░░░░░░░░░] 67% (2 / 3 files)        |
|                                                          |
|  현재 파일: product_master.srw                           |
|  경과 시간: 1m 23s                                       |
|  예상 남은 시간: 42s                                     |
|                                                          |
|  ✅ order_list.srd - SQL 12개 추출                       |
|  ✅ customer_detail.srd - SQL 8개 추출                   |
|  🔄 product_master.srw - 분석 중...                      |
+----------------------------------------------------------+
```

**분석 완료 화면**:
```
+----------------------------------------------------------+
|  ✅ 분석 완료!                          [Download Report] |
+----------------------------------------------------------+
|  처리 시간: 3m 45s                                       |
|  처리 파일: 3개                                          |
|                                                          |
|  📊 추출 결과                                            |
|  +----------------------------------------------------+  |
|  | 추출된 SQL:        28개                            |  |
|  | 식별된 테이블:     15개                            |  |
|  | 테이블 관계:       22개                            |  |
|  | 비즈니스 규칙:     11개                            |  |
|  | Vector DB 문서:    61개                            |  |
|  +----------------------------------------------------+  |
|                                                          |
|  📋 추출된 테이블 목록                                   |
|  +----------------------------------------------------+  |
|  | ORDERS (주문 정보)           - 12개 SQL 패턴       |  |
|  | CUSTOMERS (고객 정보)        - 8개 SQL 패턴        |  |
|  | PRODUCTS (제품 정보)         - 5개 SQL 패턴        |  |
|  | ORDER_ITEMS (주문 상세)      - 3개 SQL 패턴        |  |
|  +----------------------------------------------------+  |
|                                                          |
|  [View Details] [Analyze More Files] [Back to Dashboard] |
+----------------------------------------------------------+
```

---

## **9. 데이터 구조 설계**

### 9.1 로컬 파일 시스템 구조

```
~/.oracle-nlsql/
├── config/
│   ├── encryption.key              # Fernet 암호화 키
│   └── settings.json                # 전역 설정
│
├── connections/                     # DB 연결 정보
│   ├── ORCL.json                   # 암호화된 접속 정보
│   ├── DEV.json
│   └── TEST.json
│
├── tnsnames/
│   └── tnsnames_cache.json         # 파싱된 tnsnames.ora 캐시
│
├── metadata/                        # 메타데이터 백업 (JSON)
│   └── {database_sid}/
│       └── {schema_name}/
│           ├── common_columns.json
│           ├── code_definitions.json
│           └── tables.json
│
├── vectordb/                        # ChromaDB 영구 저장소
│   └── {database_sid}/
│       ├── chroma.sqlite3          # ChromaDB 메타데이터
│       └── {schema_name}_schema/   # Collection 데이터
│           ├── data_level0.bin
│           └── index/
│
├── powerbuilder/                    # PowerBuilder 분석 결과
│   └── {database_sid}/
│       └── {schema_name}/
│           ├── analysis_results.json
│           └── extracted_sqls.sql
│
└── logs/
    ├── mcp_server.log              # MCP Server 로그
    └── management_backend.log      # Management Backend 로그
```

---

### 9.2 데이터베이스 연결 정보 구조

**파일**: `~/.oracle-nlsql/connections/{database_sid}.json`

```json
{
    "database_sid": "ORCL",
    "host": "localhost",
    "port": 1521,
    "service_name": "ORCL",
    "user": "system",
    "encrypted_password": "gAAAAABl8K3x...encrypted_data...",
    "created_at": "2025-03-01T10:15:30",
    "last_connected": "2025-03-07T14:23:15",
    "connection_pool": {
        "min": 2,
        "max": 10,
        "increment": 1
    }
}
```

---

### 9.3 공통 메타데이터 구조

#### 9.3.1 공통 컬럼 정의

**파일**: `~/.oracle-nlsql/metadata/{database_sid}/common_columns.json`

```json
{
    "version": "1.0",
    "last_updated": "2025-03-07T12:30:00",
    "columns": [
        {
            "column_name": "CUSTOMER_ID",
            "korean_name": "고객번호",
            "data_type": "VARCHAR2",
            "description": "고객 고유 식별자",
            "common_usage": "고객 테이블의 Primary Key 또는 다른 테이블의 Foreign Key",
            "examples": ["CUST001", "CUST002"]
        },
        {
            "column_name": "ORDER_DATE",
            "korean_name": "주문일자",
            "data_type": "DATE",
            "description": "주문이 접수된 날짜",
            "common_usage": "주문 관련 테이블의 필수 컬럼",
            "format": "YYYY-MM-DD"
        },
        {
            "column_name": "STATUS",
            "korean_name": "상태",
            "data_type": "VARCHAR2",
            "description": "처리 상태 코드",
            "common_usage": "코드 테이블과 매핑 필요",
            "code_table": "STATUS_CODES"
        }
    ]
}
```

#### 9.3.2 코드 정의

**파일**: `~/.oracle-nlsql/metadata/{database_sid}/code_definitions.json`

```json
{
    "version": "1.0",
    "last_updated": "2025-03-07T12:30:00",
    "code_definitions": [
        {
            "code_column": "ORDER_STATUS",
            "table_name": "ORDERS",
            "description": "주문 처리 상태",
            "values": [
                {"code": "01", "name": "주문접수", "description": "고객 주문 접수 완료"},
                {"code": "02", "name": "결제완료", "description": "결제 처리 완료"},
                {"code": "03", "name": "배송중", "description": "상품 배송 진행 중"},
                {"code": "04", "name": "배송완료", "description": "배송 완료 및 주문 종료"},
                {"code": "99", "name": "취소", "description": "주문 취소"}
            ]
        },
        {
            "code_column": "CUSTOMER_GRADE",
            "table_name": "CUSTOMERS",
            "description": "고객 등급",
            "values": [
                {"code": "VIP", "name": "VIP 고객", "description": "연 구매액 1천만원 이상"},
                {"code": "GOLD", "name": "골드 고객", "description": "연 구매액 500만원 이상"},
                {"code": "SILVER", "name": "실버 고객", "description": "연 구매액 100만원 이상"},
                {"code": "NORMAL", "name": "일반 고객", "description": "기본 고객"}
            ]
        }
    ]
}
```

---

### 9.4 Vector DB 데이터 구조

#### 9.4.1 Collection: `{database_sid}_{schema_name}_schema`

**목적**: 테이블 및 컬럼 메타데이터 저장

**Document 예시**:
```python
{
    "id": "ORCL_SCOTT_table_ORDERS",
    "document": """
테이블: ORDERS
한글명: 주문 정보
설명: 고객 주문 내역을 저장하는 마스터 테이블

컬럼:
- ORDER_ID (주문번호, VARCHAR2(20), NOT NULL): 주문 고유 식별자
- CUSTOMER_ID (고객번호, VARCHAR2(20), NOT NULL): 고객 FK
- ORDER_DATE (주문일자, DATE, NOT NULL): 주문 접수 일시
- ORDER_AMOUNT (주문금액, NUMBER(15,2)): 총 주문 금액
- ORDER_STATUS (주문상태, VARCHAR2(2)): 01=주문접수, 02=결제완료, 03=배송중, 04=배송완료

관계:
- CUSTOMERS (CUSTOMER_ID → CUSTOMER_ID)
- ORDER_ITEMS (ORDER_ID → ORDER_ID)
    """,
    "metadata": {
        "type": "table",
        "table_name": "ORDERS",
        "schema": "SCOTT",
        "database_sid": "ORCL",
        "column_count": 5,
        "has_pk": true,
        "has_fk": true,
        "source": "db_extraction",
        "last_updated": "2025-03-07T14:23:15"
    },
    "embedding": [0.023, -0.145, 0.089, ...]  # ChromaDB가 자동 생성
}
```

#### 9.4.2 Collection: `{database_sid}_{schema_name}_patterns`

**목적**: 성공한 SQL 패턴 학습 저장

**Document 예시**:
```python
{
    "id": "pattern_a3f8c2d1",
    "document": """
질의: 최근 1주일간 고객별 주문 통계
테이블: CUSTOMERS, ORDERS
조건: ORDER_DATE >= SYSDATE - 7, GROUP BY CUSTOMER_ID
집계: SUM(ORDER_AMOUNT), COUNT(ORDER_ID)
    """,
    "metadata": {
        "type": "query_pattern",
        "sql": "SELECT c.customer_name, SUM(o.order_amount) AS total_amount, COUNT(o.order_id) AS order_count FROM customers c JOIN orders o ON c.customer_id = o.customer_id WHERE o.order_date >= SYSDATE - 7 GROUP BY c.customer_id, c.customer_name ORDER BY total_amount DESC",
        "tables": ["CUSTOMERS", "ORDERS"],
        "conditions": ["ORDER_DATE >= SYSDATE - 7"],
        "aggregations": ["SUM", "COUNT"],
        "timestamp": "2025-03-07T15:45:22",
        "execution_time": 0.35,
        "row_count": 125
    },
    "embedding": [0.012, -0.078, 0.156, ...]
}
```

#### 9.4.3 Collection: `{database_sid}_{schema_name}_business`

**목적**: 비즈니스 지식 및 용어 저장

**Document 예시**:
```python
{
    "id": "business_order_lifecycle",
    "document": """
비즈니스 프로세스: 주문 처리 생명주기

1. 주문 접수 (ORDER_STATUS = '01')
   - 고객이 온라인/오프라인으로 주문 생성
   - ORDERS 테이블에 신규 레코드 INSERT

2. 결제 완료 (ORDER_STATUS = '02')
   - 결제 처리 완료 시 상태 업데이트
   - PAYMENT 테이블에 결제 정보 INSERT

3. 배송 중 (ORDER_STATUS = '03')
   - 상품 출고 및 배송 시작
   - DELIVERY 테이블에 배송 정보 INSERT

4. 배송 완료 (ORDER_STATUS = '04')
   - 고객 수령 확인
   - 주문 완료 처리

취소: ORDER_STATUS = '99', 환불 처리 필요
    """,
    "metadata": {
        "type": "business_process",
        "domain": "order_management",
        "related_tables": ["ORDERS", "PAYMENT", "DELIVERY"],
        "keywords": ["주문", "결제", "배송", "취소"],
        "source": "powerbuilder_learning",
        "created_at": "2025-03-06T09:15:00"
    },
    "embedding": [0.045, -0.023, 0.112, ...]
}
```

#### 9.4.4 Collection: `{database_sid}_{schema_name}_rules`

**목적**: 비즈니스 규칙 및 계산 로직 저장

**Document 예시**:
```python
{
    "id": "rule_order_total_calculation",
    "document": """
비즈니스 규칙: 주문 총액 계산

규칙 타입: 계산 로직
적용 테이블: ORDERS, ORDER_ITEMS

계산식:
ORDER_TOTAL_AMOUNT = SUM(ORDER_ITEMS.QUANTITY * ORDER_ITEMS.UNIT_PRICE)

조건:
- 할인이 있는 경우: ORDER_TOTAL_AMOUNT - DISCOUNT_AMOUNT
- 배송비 포함: ORDER_TOTAL_AMOUNT + DELIVERY_FEE
- 최종 결제액: ORDER_TOTAL_AMOUNT - DISCOUNT_AMOUNT + DELIVERY_FEE

검증 규칙:
- ORDER_TOTAL_AMOUNT >= 0
- DISCOUNT_AMOUNT <= ORDER_TOTAL_AMOUNT
    """,
    "metadata": {
        "type": "business_rule",
        "rule_type": "calculation",
        "tables": ["ORDERS", "ORDER_ITEMS"],
        "columns": ["ORDER_TOTAL_AMOUNT", "QUANTITY", "UNIT_PRICE", "DISCOUNT_AMOUNT", "DELIVERY_FEE"],
        "source": "powerbuilder_learning",
        "validated": true,
        "created_at": "2025-03-06T10:30:00"
    },
    "embedding": [0.067, -0.091, 0.134, ...]
}
```

---

### 9.5 PowerBuilder 분석 결과 구조

**파일**: `~/.oracle-nlsql/powerbuilder/{database_sid}/{schema_name}/analysis_results.json`

```json
{
    "job_id": "pb_analysis_20250307_123456",
    "database_sid": "ORCL",
    "schema_name": "SCOTT",
    "analysis_date": "2025-03-07T15:30:00",
    "total_files": 50,
    "processed_files": 50,
    "failed_files": 0,
    "elapsed_time": "3m 45s",

    "summary": {
        "extracted_sqls": 82,
        "identified_tables": 35,
        "relationships": 48,
        "business_rules": 23,
        "vectordb_documents": 153
    },

    "files": [
        {
            "filename": "order_list.srd",
            "file_type": "datawindow",
            "file_size": 25600,
            "analysis_status": "success",
            "extracted_data": {
                "sqls": [
                    {
                        "type": "retrieve",
                        "query": "SELECT o.order_id, o.order_date, c.customer_name, o.order_amount FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE o.order_date >= :start_date",
                        "tables": ["ORDERS", "CUSTOMERS"],
                        "parameters": ["start_date"]
                    }
                ],
                "relationships": [
                    {
                        "from_table": "ORDERS",
                        "to_table": "CUSTOMERS",
                        "join_type": "INNER JOIN",
                        "condition": "o.customer_id = c.customer_id"
                    }
                ],
                "business_logic": [
                    {
                        "type": "filter",
                        "description": "최근 주문 조회",
                        "expression": "order_date >= :start_date"
                    }
                ]
            }
        }
    ]
}
```

---

### 9.6 Management Backend 작업 상태 관리

**인메모리 저장소** (Redis 또는 Python dict):

```python
job_status = {
    "pb_analysis_20250307_123456": {
        "job_id": "pb_analysis_20250307_123456",
        "job_type": "powerbuilder_analysis",
        "status": "processing",  # pending | processing | completed | failed
        "progress": {
            "processed": 35,
            "total": 50,
            "percentage": 70,
            "current_file": "product_master.srw"
        },
        "start_time": "2025-03-07T15:30:00",
        "elapsed_time": "2m 15s",
        "estimated_remaining": "58s",
        "results": None  # 완료 시 결과 저장
    }
}
```

---

**(Part 4 완료 - 다음 Part에서 계속됩니다)**

---

## **Part 5: UI/UX, 기술 스택 & 로드맵**

---

## **10. UI/UX 설계**

### 10.1 디자인 원칙

| 원칙 | 설명 | 구현 방법 |
|------|------|----------|
| **단순성** | 기술적 복잡도를 감추고 직관적인 인터페이스 제공 | 3-Click 원칙: 모든 작업을 3번 클릭 내에 완료 |
| **즉시성** | 실시간 피드백 제공 | Progress bar, Toast 알림, WebSocket 업데이트 |
| **투명성** | 내부 동작을 사용자에게 명확히 전달 | 로그 표시, 상태 메시지, 에러 상세 정보 |
| **일관성** | 통일된 UI 패턴 사용 | Material-UI 기반 디자인 시스템 |
| **접근성** | 다양한 사용자 지원 | 키보드 네비게이션, 고대비 모드 |

---

### 10.2 컴포넌트 계층 구조

```
App
├── Layout
│   ├── Header (로고, 네비게이션, 사용자 프로필)
│   ├── Sidebar (메뉴)
│   └── Footer (버전 정보, 링크)
│
├── Pages
│   ├── Dashboard
│   │   ├── SystemStatsCard
│   │   ├── DatabaseListCard
│   │   └── RecentActivityCard
│   │
│   ├── DatabaseManagement
│   │   ├── DatabaseConnectionForm
│   │   ├── DatabaseListTable
│   │   └── ConnectionStatusIndicator
│   │
│   ├── MetadataManagement
│   │   ├── CSVUploadZone
│   │   ├── MetadataTable (공통 컬럼, 코드 정의, 테이블 정보)
│   │   └── ValidationResultModal
│   │
│   ├── PowerBuilderAnalysis
│   │   ├── FileUploadZone (Drag & Drop)
│   │   ├── AnalysisOptionsPanel
│   │   ├── ProgressTracker
│   │   └── ResultsViewer
│   │
│   └── VectorDBMonitoring
│       ├── CollectionStatsCard
│       ├── SearchInterface
│       └── DocumentViewer
│
└── Common Components
    ├── Button
    ├── Modal
    ├── Table
    ├── FileUploader
    ├── ProgressBar
    ├── Toast (알림)
    └── LoadingSpinner
```

---

### 10.3 주요 사용자 시나리오 (User Journey)

#### 시나리오 1: 신규 데이터베이스 등록 및 메타데이터 추출

```
1. [Dashboard] → "Add Database" 버튼 클릭
   ↓
2. [Modal] DB 접속 정보 입력 (SID, Host, Port, User, Password)
   ↓
3. "Test Connection" 클릭 → ✅ 연결 성공 메시지
   ↓
4. "Register & Extract Metadata" 클릭
   ↓
5. [Progress Modal]
   - DB 등록 중... ✅
   - 스키마 목록 조회 중... ✅
   - 메타데이터 추출 중... (진행률 표시)
   - Vector DB 저장 중... ✅
   ↓
6. [Dashboard] "✅ ORCL 데이터베이스가 등록되었습니다. (125개 테이블, 850개 컬럼)"
```

**소요 시간**: 2-3분

---

#### 시나리오 2: PowerBuilder 소스 분석

```
1. [Dashboard] → "PowerBuilder Analysis" 메뉴 클릭
   ↓
2. [PowerBuilder Analysis 페이지]
   - Database: ORCL 선택
   - Schema: SCOTT 선택
   ↓
3. [파일 업로드 영역]
   - Drag & Drop으로 50개 .srd 파일 업로드
   - 자동으로 파일 목록 표시 (파일명, 크기, 타입)
   ↓
4. [분석 옵션] 체크박스 선택
   ☑ SQL 추출
   ☑ 테이블 관계 추론
   ☑ 비즈니스 로직 추출
   ☑ Vector DB에 자동 저장
   ↓
5. "Start Analysis" 클릭
   ↓
6. [진행 상황 화면]
   [████████░░░░░░] 60% (30 / 50 files)
   현재 파일: customer_detail.srd
   경과 시간: 2m 15s
   예상 남은 시간: 1m 30s

   ✅ order_list.srd - SQL 12개 추출
   ✅ product_master.srd - SQL 8개 추출
   🔄 customer_detail.srd - 분석 중...
   ↓
7. [분석 완료]
   ✅ 분석 완료! (3m 45s)

   📊 추출 결과
   - 추출된 SQL: 82개
   - 식별된 테이블: 35개
   - 테이블 관계: 48개
   - 비즈니스 규칙: 23개
   - Vector DB 문서: 153개

   [Download Report] [Analyze More Files] [Back to Dashboard]
```

**소요 시간**: 3-5분 (50개 파일 기준)

---

#### 시나리오 3: Claude에서 자연어 SQL 생성 (MCP)

```
[Claude Desktop 또는 Claude.ai]

User: "최근 1주일간 고객별 주문 금액 합계를 보여줘. ORCL.SCOTT 스키마야."

Claude (내부 동작):
1. get_table_summaries_for_query(database_sid="ORCL", schema_name="SCOTT")
   → Vector DB에서 전체 테이블 요약 로드

2. LLM이 관련 테이블 식별: CUSTOMERS, ORDERS

3. get_detailed_metadata_for_sql(
      database_sid="ORCL",
      schema_name="SCOTT",
      table_names=["CUSTOMERS", "ORDERS"]
   )
   → 상세 메타데이터 + 과거 패턴 + 비즈니스 규칙 로드

4. SQL 생성:
   SELECT
       c.customer_name AS 고객명,
       SUM(o.order_amount) AS 주문금액합계,
       COUNT(o.order_id) AS 주문건수
   FROM customers c
   JOIN orders o ON c.customer_id = o.customer_id
   WHERE o.order_date >= SYSDATE - 7
   GROUP BY c.customer_id, c.customer_name
   ORDER BY 주문금액합계 DESC

5. execute_sql(database_sid="ORCL", sql="...", max_rows=100)
   → 실행 결과 반환

6. 자동으로 쿼리 패턴 학습 (Vector DB에 저장)

Claude:
"최근 1주일간 고객별 주문 현황입니다:

| 고객명      | 주문금액합계 | 주문건수 |
|-------------|--------------|----------|
| 김철수      | 2,350,000원  | 8건      |
| 이영희      | 1,890,000원  | 5건      |
| 박민수      | 1,450,000원  | 3건      |
...

총 125명의 고객이 주문하였으며, 총 주문 금액은 45,230,000원입니다."
```

**소요 시간**: 2-5초

---

### 10.4 반응형 디자인

#### 브레이크포인트

```css
/* Desktop (1200px 이상) */
.container {
  max-width: 1200px;
  grid-template-columns: 250px 1fr;
}

/* Tablet (768px - 1199px) */
@media (max-width: 1199px) {
  .container {
    grid-template-columns: 200px 1fr;
  }
  .sidebar {
    width: 200px;
  }
}

/* Mobile (767px 이하) */
@media (max-width: 767px) {
  .container {
    grid-template-columns: 1fr;
  }
  .sidebar {
    display: none; /* 햄버거 메뉴로 대체 */
  }
}
```

---

### 10.5 다크 모드 지원

```typescript
// Theme Provider
const lightTheme = {
  colors: {
    primary: '#1976d2',
    background: '#ffffff',
    surface: '#f5f5f5',
    text: '#212121',
    border: '#e0e0e0'
  }
};

const darkTheme = {
  colors: {
    primary: '#90caf9',
    background: '#121212',
    surface: '#1e1e1e',
    text: '#ffffff',
    border: '#333333'
  }
};
```

---

## **11. 기술 스택**

### 11.1 MCP Server (Python)

| 구성 요소 | 기술 | 버전 | 용도 |
|----------|------|------|------|
| **MCP Framework** | `mcp` | 1.1.2 | MCP Protocol 구현 |
| **DB 드라이버** | `oracledb` | 2.4.1 | Oracle 연결 (python-oracledb thin mode) |
| **암호화** | `cryptography` | 44.0.0 | Fernet 대칭키 암호화 |
| **Vector DB** | `chromadb` | 0.5.23 | 로컬 벡터 데이터베이스 |
| **Embedding** | ChromaDB 기본 embedding | - | sentence-transformers 기반 |
| **파일 처리** | `pathlib`, `json` | stdlib | 파일 시스템 관리 |
| **로깅** | `logging` | stdlib | 디버깅 및 모니터링 |

**설치**:
```bash
pip install mcp oracledb cryptography chromadb
```

---

### 11.2 Management Backend (Python + FastAPI)

| 구성 요소 | 기술 | 버전 | 용도 |
|----------|------|------|------|
| **웹 프레임워크** | `fastapi` | 0.115.12 | REST API 서버 |
| **비동기 런타임** | `uvicorn` | 0.34.0 | ASGI 서버 |
| **LLM 클라이언트** | `anthropic` | 0.42.0 | Claude Sonnet API 호출 |
| **CSV 처리** | `pandas` | 2.2.3 | CSV 파싱 및 검증 |
| **파일 업로드** | `python-multipart` | 0.0.20 | Multipart form-data |
| **인코딩 감지** | `chardet` | 5.2.0 | 한글 인코딩 자동 감지 |
| **코어 공유** | OracleNLSQLCore | - | MCP Server와 로직 공유 |
| **CORS** | `fastapi.middleware.cors` | - | 웹 UI 연동 |

**설치**:
```bash
pip install fastapi uvicorn anthropic pandas python-multipart chardet
```

**실행**:
```bash
uvicorn management_backend.main:app --reload --port 8000
```

---

### 11.3 Web UI (React + TypeScript)

| 구성 요소 | 기술 | 버전 | 용도 |
|----------|------|------|------|
| **프레임워크** | `react` | 18.3.1 | UI 라이브러리 |
| **타입 체크** | `typescript` | 5.7.3 | 정적 타입 검사 |
| **빌드 도구** | `vite` | 6.0.11 | 번들러 및 개발 서버 |
| **라우팅** | `react-router-dom` | 7.1.4 | SPA 라우팅 |
| **상태 관리** | `zustand` | 5.0.3 | 전역 상태 관리 (경량) |
| **UI 컴포넌트** | `@mui/material` | 6.3.1 | Material-UI 디자인 시스템 |
| **HTTP 클라이언트** | `axios` | 1.7.9 | REST API 호출 |
| **폼 검증** | `react-hook-form` | 7.54.2 | 폼 유효성 검사 |
| **파일 업로드** | `react-dropzone` | 14.3.5 | Drag & Drop 파일 업로드 |
| **테이블** | `@tanstack/react-table` | 8.20.6 | 고성능 테이블 |
| **차트** | `recharts` | 2.15.0 | 데이터 시각화 |
| **알림** | `react-toastify` | 10.0.6 | Toast 알림 |
| **실시간 통신** | `socket.io-client` | 4.8.1 | WebSocket (선택 사항) |

**설치**:
```bash
npm create vite@latest web-ui -- --template react-ts
cd web-ui
npm install @mui/material @emotion/react @emotion/styled axios react-router-dom zustand react-hook-form react-dropzone @tanstack/react-table recharts react-toastify
```

**실행**:
```bash
npm run dev  # 개발 서버: http://localhost:5173
npm run build  # 프로덕션 빌드
```

---

### 11.4 개발 환경

| 도구 | 용도 |
|------|------|
| **IDE** | VS Code (Python, TypeScript) |
| **Python 버전** | 3.11 이상 |
| **Node.js 버전** | 20.x LTS |
| **패키지 관리** | pip (Python), npm (Node.js) |
| **버전 관리** | Git |
| **API 테스트** | Postman, Thunder Client |
| **DB 클라이언트** | DBeaver, SQL Developer |

---

### 11.5 배포 환경

| 구성 요소 | 배포 방식 | 실행 위치 |
|----------|----------|----------|
| **MCP Server** | Python 패키지 설치 | 사용자 로컬 PC |
| **Management Backend** | Python 프로세스 (백그라운드) | 사용자 로컬 PC (localhost:8000) |
| **Web UI** | 정적 파일 (SPA) | 로컬 웹 서버 또는 파일 시스템 |
| **Vector DB** | ChromaDB 파일 기반 저장소 | `~/.oracle-nlsql/vectordb/` |

**로컬 실행 구조**:
```
사용자 PC
├── MCP Server (Claude Desktop에서 자동 시작)
│   └── stdio 통신 (Claude ↔ MCP Server)
│
├── Management Backend (수동 시작 또는 시스템 서비스)
│   └── http://localhost:8000 (REST API)
│
├── Web UI (브라우저)
│   └── http://localhost:5173 (개발) 또는 file:///path/to/index.html (프로덕션)
│
└── Vector DB (ChromaDB)
    └── ~/.oracle-nlsql/vectordb/ (파일 시스템)
```

---

## **12. 구현 로드맵**

### 12.1 Phase 1: 기반 구축 (4주)

#### Week 1: 프로젝트 셋업 및 코어 모듈
- [x] 프로젝트 구조 설계
- [ ] OracleNLSQLCore 클래스 리팩토링
  - DB 연결 관리
  - 메타데이터 추출
  - 암호화 모듈
- [ ] ChromaDB 통합
  - Collection 생성 로직
  - Document 저장/조회 API
- [ ] 파일 시스템 구조 설정
  - `~/.oracle-nlsql/` 디렉토리 자동 생성
  - 설정 파일 관리

**Deliverable**: 코어 모듈 완성, 단위 테스트 작성

---

#### Week 2: MCP Server 21개 Tools 구현
- [ ] 연결 관리 Tools (5개)
  - register_database_credentials
  - connect_database
  - delete_database
  - load_tnsnames
  - list_available_databases
- [ ] 메타데이터 관리 Tools (6개)
  - extract_and_integrate_metadata
  - get_table_summaries_for_query
  - get_detailed_metadata_for_sql
  - view_common_metadata
  - register_common_columns
  - register_code_values
- [ ] 조회 Tools (7개)
  - show_databases, show_schemas, show_tables
  - describe_table, show_procedures, show_procedure_source
  - show_connection_status
- [ ] 실행 Tools (3개)
  - execute_sql
  - view_sql_rules
  - update_sql_rules

**Deliverable**: 21개 MCP Tools 완성, Claude Desktop 연동 테스트

---

#### Week 3: Management Backend - Core API
- [ ] FastAPI 프로젝트 셋업
- [ ] OracleNLSQLCore 통합
- [ ] CSV 업로드 API
  - /api/metadata/upload-csv
  - 검증 로직 (pandas)
  - Vector DB 자동 업데이트
- [ ] Vector DB 관리 API
  - /api/vectordb/stats
  - /api/vectordb/search
  - /api/vectordb/clear
- [ ] CORS 설정

**Deliverable**: Management Backend 기본 API 완성

---

#### Week 4: PowerBuilder 분석 - LLM 통합
- [ ] PowerBuilder 파일 파서
  - .srd, .srw, .sru 파일 읽기
  - 인코딩 자동 감지 (EUC-KR, UTF-8)
- [ ] LLM 분석 프롬프트 설계
  - DataWindow 분석 프롬프트
  - Window 분석 프롬프트
- [ ] Claude Sonnet API 통합
  - Batch 처리 로직
  - 비용 최적화 (파일 크기별 배치)
- [ ] /api/powerbuilder/analyze API
  - 비동기 백그라운드 작업
  - 진행 상황 추적
  - 결과 저장

**Deliverable**: PowerBuilder 분석 기능 완성 (End-to-End)

---

### 12.2 Phase 2: Web UI 개발 (4주)

#### Week 5: 프로젝트 셋업 및 공통 컴포넌트
- [ ] Vite + React + TypeScript 셋업
- [ ] Material-UI 설정
- [ ] 라우팅 구조 설계
- [ ] 공통 컴포넌트 개발
  - Button, Modal, Table, FileUploader
  - ProgressBar, Toast, LoadingSpinner
- [ ] 전역 상태 관리 (Zustand)
- [ ] API 클라이언트 (axios)

**Deliverable**: UI 기반 구조 완성

---

#### Week 6: 대시보드 & 데이터베이스 관리
- [ ] 대시보드 페이지
  - SystemStatsCard
  - DatabaseListCard
  - RecentActivityCard
- [ ] 데이터베이스 관리 페이지
  - DatabaseConnectionForm
  - DatabaseListTable
  - ConnectionStatusIndicator

**Deliverable**: 대시보드 및 DB 관리 UI 완성

---

#### Week 7: 메타데이터 관리
- [ ] 메타데이터 관리 페이지
  - CSV 업로드 영역
  - MetadataTable (공통 컬럼, 코드 정의, 테이블 정보)
  - ValidationResultModal
- [ ] CSV 다운로드 기능
- [ ] 검색 및 필터링

**Deliverable**: 메타데이터 관리 UI 완성

---

#### Week 8: PowerBuilder 분석 & Vector DB 모니터링
- [ ] PowerBuilder 분석 페이지
  - Drag & Drop 파일 업로드
  - 분석 옵션 패널
  - 실시간 진행 상황 표시
  - 결과 뷰어
- [ ] Vector DB 모니터링 페이지
  - Collection 통계 카드
  - 검색 인터페이스
  - Document 뷰어
- [ ] 다크 모드 구현

**Deliverable**: 전체 Web UI 완성

---

### 12.3 Phase 3: 통합 테스트 & 최적화 (2주)

#### Week 9: 통합 테스트
- [ ] End-to-End 테스트 시나리오
  - 신규 DB 등록 → 메타데이터 추출 → SQL 생성
  - PowerBuilder 분석 → Vector DB 저장 → 자연어 쿼리
- [ ] 성능 테스트
  - Vector DB 검색 속도 (< 1초 목표)
  - PowerBuilder 대용량 파일 처리 (100개 파일)
  - SQL 생성 속도 (< 5초 목표)
- [ ] 에러 핸들링 테스트
  - DB 연결 실패
  - LLM API 오류
  - 잘못된 CSV 파일

**Deliverable**: 테스트 보고서, 버그 수정

---

#### Week 10: 최적화 & 문서화
- [ ] 성능 최적화
  - Vector DB 인덱싱 튜닝
  - LLM 프롬프트 최적화
  - 웹 UI 로딩 속도 개선
- [ ] 문서 작성
  - 사용자 매뉴얼
  - API 문서 (OpenAPI/Swagger)
  - 개발자 가이드
- [ ] 설치 패키지 준비
  - pip 패키지 (MCP Server)
  - 독립 실행형 번들 (Management Backend + Web UI)

**Deliverable**: 프로덕션 준비 완료

---

### 12.4 Phase 4: 릴리스 & 확장 (지속)

#### Week 11-12: 베타 테스트 & 피드백
- [ ] 내부 베타 테스트
- [ ] 사용자 피드백 수집
- [ ] 버그 수정 및 UI 개선
- [ ] 공식 릴리스 (v2.0.0)

**Deliverable**: 공식 릴리스

---

#### 향후 확장 계획 (Phase 5+)

| 기능 | 우선순위 | 예상 기간 |
|------|---------|----------|
| **다국어 지원** (영어) | P1 | 2주 |
| **MySQL/PostgreSQL 지원** | P1 | 4주 |
| **Vector DB 크기 최적화** | P2 | 2주 |
| **SQL 실행 히스토리** | P2 | 1주 |
| **사용자 권한 관리** | P3 | 3주 |
| **클라우드 배포 옵션** | P3 | 4주 |

---

## **13. 성공 지표 (Success Metrics)**

### 13.1 정량적 지표 (KPI)

| 지표 | 현재 (Before) | 목표 (After) | 측정 방법 |
|------|---------------|--------------|-----------|
| **SQL 생성 속도** | 5-10초 | **< 3초** | 자연어 입력 → SQL 반환 시간 |
| **Vector 검색 속도** | N/A | **< 1초** | ChromaDB query() 응답 시간 |
| **초기 셋업 시간** | 36시간 (수동) | **< 1시간** | DB 등록 + PB 분석 완료 시간 |
| **SQL 생성 정확도** | 70% | **90%** | 생성된 SQL의 문법 오류 없이 실행 성공률 |
| **메타데이터 커버리지** | 30% | **80%** | 전체 컬럼 중 한글명/설명이 있는 비율 |
| **PowerBuilder 분석 정확도** | N/A | **85-90%** | LLM 추출 SQL의 수동 검증 대비 정확도 |
| **시스템 응답 시간** | N/A | **< 2초** | Web UI 페이지 로딩 시간 |
| **동시 사용자 지원** | 1명 | **5명** | Management Backend 동시 요청 처리 |

---

### 13.2 정성적 지표

| 지표 | 측정 방법 | 목표 |
|------|-----------|------|
| **사용 편의성** | 사용자 만족도 설문 (5점 척도) | 평균 4.5점 이상 |
| **학습 곡선** | 신규 사용자가 첫 SQL 생성까지 걸리는 시간 | 10분 이내 |
| **에러 복구** | 에러 발생 시 사용자가 자체 해결 가능한 비율 | 80% 이상 |
| **문서 완성도** | 문서 커버리지 (기능 대비 문서화 비율) | 100% |

---

### 13.3 비즈니스 임팩트

| 항목 | Before | After | 개선율 |
|------|--------|-------|--------|
| **신규 DB 온보딩 시간** | 2-3일 | 1-2시간 | **95% 단축** |
| **SQL 생성 오류율** | 30% | 10% | **66% 감소** |
| **메타데이터 유지보수 비용** | 월 8시간 | 월 2시간 | **75% 감소** |
| **PowerBuilder 레거시 분석** | 4.5일 (수동) | 40분 (자동) | **90% 단축** |

---

## **14. 리스크 관리 (Risk Management)**

### 14.1 기술적 리스크

| 리스크 | 발생 가능성 | 영향도 | 완화 전략 |
|--------|-------------|--------|-----------|
| **ChromaDB 성능 저하** (대용량 데이터) | 중 | 높음 | - Collection당 5,000개 문서 제한<br>- 주기적 인덱스 리빌드<br>- Fallback: Qdrant 또는 Weaviate 전환 |
| **LLM API 비용 초과** (PowerBuilder 분석) | 중 | 중 | - 배치 처리로 API 호출 최소화<br>- 파일 크기 제한 (5MB)<br>- 캐싱: 동일 파일 재분석 방지 |
| **Oracle 연결 불안정** | 낮 | 높음 | - Connection Pool 관리<br>- 자동 재연결 로직<br>- Timeout 설정 (30초) |
| **PowerBuilder 파싱 실패** (복잡한 Dynamic SQL) | 높음 | 중 | - LLM 정확도 85-90% 명시<br>- 수동 보정 UI 제공<br>- 실패 시 원본 소스 보존 |
| **한글 인코딩 문제** (EUC-KR ↔ UTF-8) | 중 | 중 | - chardet 자동 인코딩 감지<br>- 사용자 수동 인코딩 선택 옵션 |
| **Vector DB 동기화 문제** (MCP ↔ Management) | 낮 | 중 | - 파일 기반 공유로 자동 동기화<br>- 파일 락 처리 |

---

### 14.2 운영 리스크

| 리스크 | 발생 가능성 | 영향도 | 완화 전략 |
|--------|-------------|--------|-----------|
| **사용자 학습 곡선** | 중 | 중 | - 직관적 UI 설계<br>- 상세 튜토리얼 제공<br>- 샘플 데이터 제공 |
| **데이터 유실** (Vector DB) | 낮 | 높음 | - 로컬 JSON 백업 자동 생성<br>- Vector DB 주기적 백업<br>- Git 저장소 활용 권장 |
| **보안 이슈** (DB 접속 정보 노출) | 낮 | 높음 | - Fernet 암호화 적용<br>- 암호화 키 파일 권한 제한 (chmod 600)<br>- 메모리에서만 복호화 |
| **Management Backend 다운** | 중 | 중 | - 자동 재시작 스크립트<br>- Health Check API (/api/health)<br>- 로그 모니터링 |

---

### 14.3 비즈니스 리스크

| 리스크 | 발생 가능성 | 영향도 | 완화 전략 |
|--------|-------------|--------|-----------|
| **사용자 채택률 저조** | 중 | 높음 | - 베타 테스트로 사전 피드백 수집<br>- ROI 명확히 제시 (90% 시간 절약)<br>- 점진적 도입 (기존 시스템 병행) |
| **경쟁 제품 출현** | 낮 | 중 | - PowerBuilder 학습 기능 (차별화 포인트)<br>- 오픈소스화 고려 |
| **유지보수 부담** | 중 | 중 | - 모듈화 설계로 유지보수성 향상<br>- 자동 테스트 커버리지 80% 이상<br>- 명확한 문서화 |

---

## **15. 결론 (Conclusion)**

### 15.1 프로젝트 요약

**Oracle NLSQL MCP Server Renewal**은 기존 모놀리식 아키텍처를 **3-Tier 구조**(MCP Server + Management Backend + Web UI)로 전환하고, **Vector DB**(ChromaDB)와 **PowerBuilder 학습** 기능을 추가하여 **자연어 SQL 생성의 정확도와 속도를 획기적으로 개선**하는 프로젝트입니다.

---

### 15.2 핵심 가치 제안

1. **생산성 90% 향상**
   - 신규 DB 온보딩: 36시간 → 40분
   - SQL 생성 속도: 5-10초 → < 3초

2. **레거시 시스템 현대화**
   - PowerBuilder 소스 자동 분석 및 지식 추출
   - 30년 된 레거시 코드를 Claude가 이해 가능한 형태로 변환

3. **사용자 경험 혁신**
   - CLI → Web UI로 접근성 향상
   - 실시간 진행 상황 표시
   - 직관적인 Drag & Drop 인터페이스

4. **지속적인 학습**
   - 성공한 SQL 패턴 자동 저장
   - 사용할수록 정확도가 향상되는 시스템

---

### 15.3 기대 효과

#### 단기 효과 (3개월 내)
- 신규 프로젝트 DB 셋업 시간 **95% 단축**
- SQL 생성 정확도 **70% → 90%** 향상
- PowerBuilder 레거시 분석 자동화

#### 중기 효과 (6개월 내)
- 메타데이터 커버리지 **30% → 80%** 향상
- Vector DB 기반 패턴 학습으로 지속적 품질 개선
- 사용자 만족도 **4.5점/5점** 달성

#### 장기 효과 (1년 내)
- 다른 DB (MySQL, PostgreSQL) 지원 확장
- 오픈소스 커뮤니티 구축
- 업계 표준 NLSQL 솔루션으로 자리매김

---

### 15.4 다음 단계 (Next Steps)

1. **즉시 실행** (이번 주):
   - [ ] Phase 1 착수: OracleNLSQLCore 리팩토링
   - [ ] 개발 환경 셋업 (Python 3.11, Node.js 20)
   - [ ] Git 저장소 초기화

2. **1개월 내**:
   - [ ] Phase 1 완료 (코어 모듈 + MCP Tools 21개)
   - [ ] Claude Desktop 연동 테스트

3. **2개월 내**:
   - [ ] Phase 2 완료 (Management Backend + PowerBuilder 분석)
   - [ ] 내부 알파 테스트

4. **3개월 내**:
   - [ ] Phase 3 완료 (Web UI)
   - [ ] 통합 테스트 및 베타 릴리스

---

### 15.5 성공을 위한 핵심 요소

✅ **기술적 우수성**
- 검증된 기술 스택 (FastAPI, React, ChromaDB)
- 모듈화 설계로 유지보수 용이
- 철저한 에러 핸들링

✅ **사용자 중심 설계**
- 직관적인 UI/UX
- 실시간 피드백
- 상세한 문서

✅ **점진적 도입**
- 기존 시스템과 병행 사용 가능
- 단계별 마이그레이션
- 롤백 가능한 구조

✅ **지속 가능성**
- 오픈소스 라이브러리 기반
- 명확한 아키텍처 문서
- 자동화된 테스트

---

### 15.6 마무리

이 프로젝트는 단순한 기술적 개선이 아닌, **자연어 인터페이스와 AI의 힘으로 데이터베이스 접근성을 민주화**하는 혁신입니다.

**"모든 사용자가 SQL을 몰라도 데이터를 조회할 수 있는 세상"**을 만들기 위한 첫 걸음입니다.

---

**문서 버전**: 1.0
**작성일**: 2025-03-07
**작성자**: Oracle NLSQL MCP Team
**승인자**: (승인 필요 시 기입)

---

## **부록 (Appendix)**

### A. 용어 사전 (Glossary)

| 용어 | 설명 |
|------|------|
| **MCP** | Model Context Protocol - Claude와 외부 도구를 연결하는 프로토콜 |
| **NLSQL** | Natural Language to SQL - 자연어를 SQL로 변환 |
| **Vector DB** | 벡터 데이터베이스 - 임베딩 기반 의미론적 검색 |
| **Embedding** | 텍스트를 고차원 벡터로 변환한 표현 |
| **ChromaDB** | 로컬 파일 기반 Vector DB 엔진 |
| **PowerBuilder** | 1990년대 레거시 애플리케이션 개발 프레임워크 |
| **DataWindow** | PowerBuilder의 데이터 표현 객체 (.srd 파일) |
| **Fernet** | 대칭키 암호화 방식 (cryptography 라이브러리) |
| **3-Tier Architecture** | MCP Server (Logic) + Management Backend (Heavy Tasks) + Web UI (Presentation) |

---

### B. 참고 문서

1. **MCP Protocol Specification**
   - https://spec.modelcontextprotocol.io/

2. **ChromaDB Documentation**
   - https://docs.trychroma.com/

3. **FastAPI Documentation**
   - https://fastapi.tiangolo.com/

4. **React + TypeScript Best Practices**
   - https://react.dev/learn

5. **Oracle Python Driver (oracledb)**
   - https://python-oracledb.readthedocs.io/

---

### C. 연락처 (Contact)

- **프로젝트 리드**: (이름)
- **기술 문의**: (이메일)
- **GitHub**: (저장소 URL)
- **이슈 트래커**: (GitHub Issues URL)

---

**(PRD 문서 완료 - Total 5 Parts)**
