# 🗄️ Oracle Database MCP Server

**자연어로 Oracle Database를 조회하고 탐색하는 MCP 서버**

Claude Desktop과 Oracle Database를 연결하여 자연어 질의를 SQL로 변환하고 실행하는 Model Context Protocol (MCP) 서버입니다.

---

## ✨ 핵심 기능

### Tier 1: MCP Server (Claude Desktop 통합)
**1️⃣ 메타정보 통합 관리**
- **자동 스키마 추출**: Oracle DB에서 테이블, 칼럼, PK, FK, 인덱스 자동 추출
- **비즈니스 의미 통합**: CSV를 통해 한글 칼럼명, 설명, 코드값 추가
- **통합 메타데이터 생성**: DB 기술 정보 + 비즈니스 의미를 하나로 통합

**2️⃣ 자연어 SQL 생성 (2단계 메타데이터 제공)**
- **Stage 1**: 경량 테이블 요약 제공 → Claude가 관련 테이블 선택 (최대 5개)
- **Stage 2**: 선택된 테이블의 상세 메타데이터 제공 → Claude가 정확한 SQL 생성
- **Claude Desktop이 직접 SQL 생성**: MCP 서버는 메타데이터만 제공
- **Oracle SQL 문법**: 날짜 함수, 계층 쿼리, 분석 함수 지원

**3️⃣ 데이터베이스 관리**
- 다중 Database/Schema 관리
- tnsnames.ora 파싱 및 자동 연결
- 암호화된 접속 정보 저장
- 테이블/프로시저 탐색

### Tier 2: Management Backend (선택 사항)
**4️⃣ Vector DB & Learning Engine**
- **ChromaDB**: 메타데이터 벡터 검색
- **패턴 학습**: SQL 생성 패턴 자동 학습 및 개선
- **유사 쿼리 추천**: 과거 질의 기반 추천

**5️⃣ Legacy Code 분석**
- **PowerBuilder Parser**: 레거시 코드 분석
- **데이터 흐름 추적**: 테이블-화면 연관 관계 분석
- **마이그레이션 지원**: 레거시 → 모던 전환 지원

---

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
# 저장소 클론
git clone https://github.com/YouHyuksoo/mcp_db.git
cd mcp_db

# 가상환경 생성 및 활성화
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정 (선택 사항)
copy .env.example .env
# .env 파일을 열어 ENCRYPTION_KEY 설정 (DB 접속정보 암호화용)
```

### 2단계: Claude Desktop 설정

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "oracle-nlsql": {
      "command": "D:\\Project\\mcp_db\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "D:\\Project\\mcp_db",
      "env": {
        "PYTHONPATH": "D:\\Project\\mcp_db"
      }
    }
  }
}
```

**Linux/Mac**: `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "oracle-nlsql": {
      "command": "/path/to/mcp_db/venv/bin/python",
      "args": ["-m", "src.mcp_server"],
      "cwd": "/path/to/mcp_db",
      "env": {
        "PYTHONPATH": "/path/to/mcp_db"
      }
    }
  }
}
```

### 3단계: Claude Desktop 재시작

설정 파일 저장 후 Claude Desktop을 재시작하면 MCP 서버가 자동으로 연결됩니다.

---

## 📖 사용 방법

### 1️⃣ tnsnames.ora 로드 (선택 사항)

```
tnsnames.ora 파일을 로드해줘: D:\oracle\network\admin\tnsnames.ora
```

### 2️⃣ 데이터베이스 연결

```
SMVNPDBext 데이터베이스에 연결해줘
사용자: INFINITY21_JSMES
비밀번호: ****
```

### 3️⃣ 메타데이터 추출 및 통합

```
INFINITY21_JSMES 스키마의 메타데이터를 추출하고
common_metadata/SMVNPDBext/ 폴더의 공통 메타데이터와 통합해줘
```

### 4️⃣ 자연어 질의

```
지난 1개월간 생산 실적을 라인별로 집계해서 보여줘
```

Claude가 자동으로:
1. Stage 1: 관련 테이블 식별
2. Stage 2: 상세 메타데이터 기반 SQL 생성
3. SQL 실행 및 결과 표시

---

## 📂 프로젝트 구조

```
mcp_db/
├── src/                              # Tier 1: MCP Server
│   ├── mcp_server.py                 # MCP 서버 메인
│   ├── oracle_connector.py           # Oracle DB 연결
│   ├── metadata_manager.py           # 메타데이터 추출
│   ├── common_metadata_manager.py    # 공통 메타데이터 관리
│   ├── credentials_manager.py        # 접속정보 암호화
│   ├── tnsnames_parser.py           # tnsnames.ora 파싱
│   └── sql_executor.py              # SQL 실행
├── backend/                          # Tier 2: Management Backend
│   ├── app/
│   │   ├── main.py                  # FastAPI 메인
│   │   ├── api/                     # REST API 엔드포인트
│   │   │   ├── metadata.py          # 메타데이터 API
│   │   │   ├── patterns.py          # 패턴 학습 API
│   │   │   └── powerbuilder.py      # PowerBuilder 분석 API
│   │   ├── core/                    # 핵심 서비스
│   │   │   ├── vector_store.py      # ChromaDB 관리
│   │   │   ├── embedding_service.py # 임베딩 생성
│   │   │   ├── learning_engine.py   # 패턴 학습 엔진
│   │   │   ├── pattern_matcher.py   # 패턴 매칭
│   │   │   ├── powerbuilder_parser.py # PB 파서
│   │   │   └── legacy_analyzer.py   # 레거시 분석
│   │   └── models/                  # 데이터 모델
│   ├── requirements.txt             # Backend 의존성
│   └── README.md                    # Backend 문서
├── common_metadata/                  # 공통 메타데이터 (CSV)
│   ├── <DB_SID>/
│   │   ├── common_columns.json      # 공통 칼럼 정의
│   │   ├── code_definitions.json    # 코드값 정의
│   │   └── <SCHEMA>/
│   │       └── table_info.json      # 테이블별 메타정보
│   ├── common_columns_template.csv  # CSV 템플릿
│   ├── code_definitions_template.csv
│   └── table_info_template.csv
├── metadata/                         # 추출된 통합 메타데이터 (JSON)
│   └── <DB_SID>/<SCHEMA>/<TABLE>/
│       └── unified_metadata.json
├── credentials/                      # 암호화된 DB 접속정보
│   └── <DB_SID>.json.enc
├── docs/                            # 문서
│   ├── ARCHITECTURE.md              # 아키텍처 설명
│   ├── METADATA_GUIDE.md            # 메타데이터 가이드
│   └── archive/                     # 개발 히스토리
├── sql_rules.md                     # SQL 작성 규칙
├── requirements.txt                 # MCP Server 의존성
├── docker-compose.yml               # Docker 설정 (Backend)
└── README.md                        # 이 파일
```

### Backend 실행 (선택 사항)

```bash
# Backend 폴더로 이동
cd backend

# Backend 의존성 설치
pip install -r requirements.txt

# Backend 서버 실행
python -m app.main

# 또는 Docker로 실행
cd ..
docker-compose up -d
```

Backend API 문서: http://localhost:8000/api/docs

---

## 🔧 CSV 메타데이터 작성 가이드

### common_columns.csv - 공통 칼럼 정의

```csv
column_name,column_name_kr,description
CREATE_DATE,생성일시,레코드 생성 일시
CREATE_USER,생성자,레코드 생성 사용자 ID
UPDATE_DATE,수정일시,최종 수정 일시
UPDATE_USER,수정자,최종 수정 사용자 ID
```

### code_definitions.csv - 코드값 정의

```csv
column_name,code_value,code_name,description
STATUS,A,활성,활성 상태
STATUS,I,비활성,비활성 상태
GRADE,VIP,VIP고객,VIP 등급 고객
GRADE,GOLD,골드고객,골드 등급 고객
```

### table_info.csv - 테이블별 메타정보

```csv
table_name,column_name,column_name_kr,description,sample_values
CUSTOMERS,CUSTOMER_ID,고객ID,고객 고유 식별자,C001|C002|C003
CUSTOMERS,CUSTOMER_NAME,고객명,고객 이름,홍길동|김철수
ORDERS,ORDER_ID,주문ID,주문 고유 번호,ORD-2024-001
```

**작성 위치**: `common_metadata/<DB_SID>/` 또는 `common_metadata/<DB_SID>/<SCHEMA>/`

---

## 🛠️ 주요 MCP Tools

| Tool | 설명 |
|------|------|
| `load_tnsnames` | tnsnames.ora 파싱 및 DB 목록 캐싱 |
| `connect_database` | 데이터베이스 연결 |
| `show_tables` | 테이블 목록 조회 |
| `describe_table` | 테이블 구조 상세 조회 |
| `extract_and_integrate_metadata` | 메타데이터 추출 및 통합 |
| `get_table_summaries_for_query` | Stage 1: 테이블 요약 제공 |
| `get_detailed_metadata_for_sql` | Stage 2: 상세 메타데이터 제공 |
| `execute_sql` | SQL 실행 |
| `import_common_columns_csv` | 공통 칼럼 CSV 임포트 |
| `import_code_definitions_csv` | 코드 정의 CSV 임포트 |
| `import_table_info_csv` | 테이블 정보 CSV 임포트 |

---

## 📚 추가 문서

- [아키텍처 설명](docs/ARCHITECTURE.md) - 2단계 메타데이터 제공 방식
- [메타데이터 가이드](docs/METADATA_GUIDE.md) - CSV 작성 및 통합 가이드
- [SQL 작성 규칙](sql_rules.md) - Oracle SQL 생성 규칙
- [개발 히스토리](docs/archive/) - 프로젝트 개발 과정

---

## 🔐 보안

- 데이터베이스 접속 정보는 AES-256으로 암호화되어 `credentials/` 폴더에 저장됩니다
- `.env` 파일의 `ENCRYPTION_KEY`를 반드시 설정하세요
- `.gitignore`에 `.env`, `credentials/`, `metadata/` 포함

---

## ⚠️ 주의사항

1. **Python 3.12+** 필요
2. **Oracle Instant Client** 설치 필요 (cx_Oracle 사용)
3. tnsnames.ora 파일이 있으면 자동 파싱 가능
4. 대용량 스키마의 경우 메타데이터 추출에 시간이 걸릴 수 있음
5. CSV 파일은 **UTF-8 인코딩**으로 저장

---

## 📝 라이선스

MIT License

---

## 🤝 기여

이슈 및 PR 환영합니다!

- GitHub: https://github.com/YouHyuksoo/mcp_db
- Issues: https://github.com/YouHyuksoo/mcp_db/issues
