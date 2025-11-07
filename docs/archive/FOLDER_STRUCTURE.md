# 📁 프로젝트 폴더 구조

**업데이트 날짜**: 2025-01-06

---

## 🗂️ 전체 구조

```
mcp_db/
├── src/                                    # 소스 코드
│   ├── mcp_server.py                      # MCP 서버 메인 (21개 Tool)
│   ├── oracle_connector.py                # Oracle DB 연결 및 스키마 추출
│   ├── credentials_manager.py             # DB 접속 정보 암호화 관리
│   ├── csv_parser.py                      # CSV 파싱 (deprecated)
│   ├── metadata_manager.py                # 메타데이터 통합 관리
│   ├── common_metadata_manager.py         # 공통 메타데이터 관리 (신규)
│   └── tnsnames_parser.py                 # tnsnames.ora 파싱
│
├── common_metadata/                        # 공통 메타데이터 (DB별)
│   ├── common_columns_template.csv        # 공통 칼럼 템플릿
│   ├── code_definitions_template.csv      # 코드 정의 템플릿
│   ├── table_info_template.csv            # 테이블 정보 템플릿
│   ├── README.md                           # 사용 가이드
│   └── {DB_SID}/                          # DB별 폴더 (자동 생성)
│       ├── common_columns.json            # 해당 DB의 공통 칼럼
│       ├── code_definitions.json          # 해당 DB의 코드 정의
│       └── {SCHEMA}/                      # 스키마별 폴더
│           └── table_info.json            # 해당 스키마의 테이블 정보
│
├── metadata/                               # 통합 메타데이터 (자동 생성)
│   └── {DB_SID}/
│       └── {SCHEMA}/
│           ├── table_summaries.json       # Stage 1용 테이블 요약
│           └── {TABLE}/
│               └── unified_metadata.json  # 통합 메타데이터
│
├── credentials/                            # DB 접속 정보 (암호화)
│   └── {DB_SID}.json.enc                  # 암호화된 접속 정보
│
├── input/                                  # (사용 안 함 - deprecated)
│   └── README.md                           # 폐기 안내
│
├── docs/                                   # 문서
│   ├── README.md                           # 메인 문서
│   ├── ARCHITECTURE_UPDATE.md             # 아키텍처 변경 이력
│   ├── COMMON_METADATA_DB_SPECIFIC_UPDATE.md  # DB별 메타데이터
│   ├── CSV_BULK_IMPORT_FEATURE.md         # CSV 일괄 등록
│   └── TABLE_INFO_CSV_IMPORT.md           # 테이블 정보 등록
│
├── .env.example                            # 환경변수 예시
├── .gitignore                              # Git 무시 파일
├── requirements.txt                        # Python 패키지
└── README.md                               # 프로젝트 메인 문서
```

---

## 📂 주요 폴더 설명

### 1. `src/` - 소스 코드

**핵심 파일**:
- `mcp_server.py`: 21개 MCP Tool 정의
- `common_metadata_manager.py`: 공통 메타데이터 관리 (DB별)
- `metadata_manager.py`: DB 스키마 + 공통 메타데이터 통합
- `tnsnames_parser.py`: tnsnames.ora 자동 파싱

---

### 2. `common_metadata/` - 공통 메타데이터 (사용자 제공)

#### 구조
```
common_metadata/
├── *.csv (템플릿 파일 - 참고용)
└── {DB_SID}/                        ← DB별로 독립적
    ├── common_columns.json          ← 공통 칼럼 정의
    ├── code_definitions.json        ← 코드 정의
    └── {SCHEMA}/
        └── table_info.json          ← 테이블 정보
```

#### 예시
```
common_metadata/
├── PROD_DB/
│   ├── common_columns.json          # PROD_DB의 칼럼 정의
│   ├── code_definitions.json        # PROD_DB의 코드 정의
│   └── SCOTT/
│       └── table_info.json          # PROD_DB.SCOTT의 테이블 정보
└── TEST_DB/
    ├── common_columns.json          # TEST_DB의 칼럼 정의
    ├── code_definitions.json        # TEST_DB의 코드 정의
    └── HR/
        └── table_info.json          # TEST_DB.HR의 테이블 정보
```

#### 생성 방법
MCP Tool로 CSV 일괄 등록:
```
import_table_info_csv(database_sid, schema_name, csv_file_path)
import_common_columns_csv(database_sid, csv_file_path)
import_code_definitions_csv(database_sid, csv_file_path)
```

---

### 3. `metadata/` - 통합 메타데이터 (자동 생성)

#### 구조
```
metadata/
└── {DB_SID}/
    └── {SCHEMA}/
        ├── table_summaries.json           # Stage 1용 (경량)
        └── {TABLE}/
            └── unified_metadata.json      # 통합 메타데이터 (상세)
```

#### 내용
- **DB 스키마 정보** (자동 추출)
  - 칼럼, 타입, PK, FK, 인덱스
- **공통 메타데이터** (사용자 제공)
  - 칼럼 한글명, 설명, 비즈니스 규칙
  - 코드 값, 레이블, 설명
  - 테이블 목적, 시나리오, 연관 테이블

#### 생성 방법
```
extract_and_integrate_metadata(database_sid, schema_name)
```

자동으로:
1. DB 스키마 추출
2. `common_metadata/{DB_SID}/` 정보 로드
3. 통합하여 `metadata/{DB_SID}/{SCHEMA}/{TABLE}/` 생성

---

### 4. `credentials/` - 접속 정보 (암호화)

#### 구조
```
credentials/
├── PROD_DB.json.enc       # 암호화된 접속 정보
├── TEST_DB.json.enc
└── DEV_DB.json.enc
```

#### 내용 (복호화 후)
```json
{
  "host": "192.168.1.100",
  "port": 1521,
  "service_name": "ORCL",
  "user": "scott",
  "password": "tiger"
}
```

#### 등록 방법
```
# 방법 1: 수동 등록
register_database_credentials(database_sid, host, port, service_name, user, password)

# 방법 2: tnsnames.ora 파싱
load_tnsnames(tnsnames_file_path)
connect_database(database_sid, user, password)
```

---

### 5. `input/` - ❌ 더 이상 사용 안 함

**폐기 사유**: CSV 파일을 특정 폴더에 넣는 방식 대신, **파일 경로를 Tool에 전달**하는 방식으로 변경

**기존 방식** (폐기):
```
input/{DB_SID}/{SCHEMA}/table_info.csv
```

**새 방식**:
```
어디든 CSV 저장 → Tool에 경로 전달 → 자동 처리
```

---

## 🔄 데이터 흐름

### 1단계: 메타데이터 등록

```
사용자 CSV 파일 (D:/my_data/*.csv)
    ↓
MCP Tool 호출 (import_*_csv)
    ↓
common_metadata/{DB_SID}/
    ├── common_columns.json
    ├── code_definitions.json
    └── {SCHEMA}/table_info.json
```

### 2단계: DB 스키마 추출 + 통합

```
Oracle DB
    ↓
extract_and_integrate_metadata
    ↓
DB 스키마 + common_metadata 통합
    ↓
metadata/{DB_SID}/{SCHEMA}/{TABLE}/unified_metadata.json
```

### 3단계: 자연어 질의

```
사용자 질문
    ↓
Stage 1: get_table_summaries_for_query
    → metadata/{DB_SID}/{SCHEMA}/table_summaries.json 읽기
    → Claude가 관련 테이블 선택
    ↓
Stage 2: get_detailed_metadata_for_sql
    → metadata/{DB_SID}/{SCHEMA}/{TABLE}/unified_metadata.json 읽기
    → Claude가 SQL 생성
    ↓
execute_sql
    → Oracle DB 실행
```

---

## 📝 파일 생성/관리 주체

| 폴더/파일 | 생성 주체 | 관리 방법 |
|-----------|----------|----------|
| `common_metadata/{DB_SID}/*.json` | MCP Tool | CSV 일괄 등록 |
| `metadata/{DB_SID}/...` | MCP Tool | 자동 생성 |
| `credentials/*.json.enc` | MCP Tool | 등록 시 자동 암호화 |
| `input/` | ❌ 사용 안 함 | 삭제 가능 |

---

## 🚫 삭제/무시 가능한 폴더

### 안전하게 삭제 가능
- `input/` - 더 이상 사용 안 함
- `venv/` - 가상환경 (재생성 가능)
- `.claude/` - Claude Desktop 설정 (재생성 가능)

### Git 무시 (`.gitignore`)
```
venv/
credentials/
metadata/
common_metadata/*/
*.pyc
__pycache__/
.env
```

---

## 🎯 새 프로젝트 시작 시

### 1. 필수 폴더 (자동 생성됨)
```
mcp_db/
├── src/                    # 소스 코드 (있음)
├── common_metadata/        # 템플릿만 있음 (자동 생성됨)
├── metadata/               # 자동 생성
└── credentials/            # 자동 생성
```

### 2. 초기 설정
```bash
# Python 패키지 설치
pip install -r requirements.txt

# .env 파일 생성
cp .env.example .env
# ENCRYPTION_KEY 설정
```

### 3. 메타데이터 등록
```
1. CSV 파일 3종 준비
2. MCP Tool로 일괄 등록
3. 메타데이터 추출
4. 자연어 질의 시작
```

---

## 📊 폴더 크기 예상

| 폴더 | 크기 (100개 테이블 기준) |
|------|-------------------------|
| `common_metadata/` | ~1MB |
| `metadata/` | ~10MB |
| `credentials/` | ~10KB |
| `input/` | 0 (사용 안 함) |

---

**업데이트 날짜**: 2025-01-06
