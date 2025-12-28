# 🗄️ Oracle NL-SQL MCP Server

**자연어로 Oracle Database를 조회하는 MCP 서버**

Claude Desktop과 Oracle Database를 연결하여 자연어 질의를 SQL로 변환하고 실행하는 Model Context Protocol (MCP) 서버입니다.

---

## ✨ 핵심 특징

### 🎯 MCP Server: Backend 없이 완전 독립 동작
- **Vector DB 의미 검색**: 자연어 질문으로 관련 테이블 자동 발견
- **SQL 자동 생성**: LLM이 정확한 Oracle SQL 생성
- **SQL 실행**: DB 직접 접속하여 결과 반환
- **완전 독립**: `data/` 폴더만 읽어서 동작, Backend 불필요

### 🖥️ Backend Server: 선택적 관리 도구
- **Database 관리**: Web UI로 DB 등록/삭제 → `data/credentials/` 저장
- **Vector DB 학습**: CSV 업로드 → 임베딩 생성 → `data/vector_db/` 저장
- **학습 후 종료**: 학습 완료 후 Backend 끄면 MCP는 계속 동작

### 💾 공유 디렉토리: `data/`
```
data/
├── credentials/        # Backend 쓰기, MCP 읽기
└── vector_db/          # Backend 쓰기, MCP 읽기
```

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/YouHyuksoo/mcp_db.git
cd mcp_db

# Python 가상환경 (MCP Server)
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# MCP 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
copy .env.example .env
# .env 파일 열어서 ENCRYPTION_KEY 설정:
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Claude Desktop 설정

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "oracle-nlsql": {
      "command": "D:\\Project\\mcp_db\\venv\\Scripts\\python.exe",
      "args": ["-m", "mcp.mcp_server"],
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
      "args": ["-m", "mcp.mcp_server"],
      "cwd": "/path/to/mcp_db"
    }
  }
}
```

### 3. Claude Desktop 재시작

설정 저장 후 Claude Desktop을 재시작하면 MCP 서버가 자동 연결됩니다.

---

## 🛠️ MCP Tools - Claude에서 바로 사용하기

### 📋 주요 도구 목록

#### 1️⃣ Database 관리 도구

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| **register_database_credentials** | DB 등록 | "DB 등록해줘 - SID: MYDB, Host: 192.168.1.100, Port: 1521, Service: ORCL, User: scott, Password: tiger" |
| **list_registered_databases** | 등록된 DB 목록 | "등록된 데이터베이스 목록 보여줘" |
| **get_database_info** | DB 접속 정보 조회 | "MYDB 데이터베이스 정보 확인해줘" |
| **load_tnsnames** | tnsnames.ora 파싱 | "tnsnames.ora 파일 읽어서 DB 목록 보여줘: C:/oracle/tnsnames.ora" |

#### 2️⃣ 메타데이터 학습 도구

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| **import_table_info_csv** | 테이블 정보 CSV 임포트 | "테이블 정보 CSV 임포트해줘: D:/metadata/table_info.csv" |
| **import_common_columns_csv** | 공통 칼럼 CSV 임포트 | "공통 칼럼 CSV 임포트해줘: D:/metadata/common_columns.csv" |
| **import_code_definitions_csv** | 코드 정의 CSV 임포트 | "코드 정의 CSV 임포트해줘: D:/metadata/codes.csv" |
| **check_vector_db_status** | Vector DB 상태 확인 | "Vector DB 상태 확인해줘" |

#### 3️⃣ SQL 생성 및 실행 도구

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| **get_table_summaries_for_query** | 질문에 관련된 테이블 검색 | "고객 주문 관련 테이블 찾아줘" |
| **get_detailed_metadata_for_sql** | SQL 생성용 상세 메타데이터 | "CUSTOMERS, ORDERS 테이블 상세 정보 보여줘" |
| **execute_sql** | SQL 실행 | "SELECT * FROM CUSTOMERS 실행해줘" |

#### 4️⃣ DB 직접 조회 도구

| 도구 | 설명 | 사용 예시 |
|------|------|----------|
| **show_schemas** | 스키마 목록 | "스키마 목록 보여줘" |
| **show_tables** | 테이블 목록 | "HR 스키마의 테이블 목록 보여줘" |
| **describe_table** | 테이블 구조 | "EMPLOYEES 테이블 구조 설명해줘" |

---

## 📖 사용 방법

### Step 1: Database 등록 ⭐ **MCP 도구 사용 권장**

#### 방법 1: MCP 도구로 직접 등록 (추천) ✅

**Claude Desktop에서 바로 사용 - Backend 불필요!**

Claude에게 이렇게 요청:
```
"데이터베이스 등록해줘
- SID: MYDB
- Host: 192.168.1.100
- Port: 1521
- Service: ORCL
- User: scott
- Password: tiger"
```

**또는 tnsnames.ora 파일이 있다면:**
```
"tnsnames.ora 파일 읽어서 DB 등록해줘: C:/oracle/network/admin/tnsnames.ora"
```

**결과:**
- `data/credentials/MYDB.json.enc` 파일 자동 생성 (AES-256 암호화)
- 즉시 사용 가능

---

#### 방법 2: Backend Web UI 사용 (대량 DB 관리 시)

Backend 서버를 실행하면 Web UI로 여러 DB를 편리하게 관리할 수 있습니다.

**Backend 설치 및 실행:**
```bash
# Backend 의존성 설치 (최초 1회)
cd backend
pip install -r requirements.txt

# Backend 시작
python -m uvicorn app.main:app --reload

# Web UI 접속: http://localhost:3000
# API 문서: http://localhost:8000/api/docs
```

**Web UI에서:**
1. tnsnames.ora 파일 업로드하여 자동 파싱
2. 또는 수동으로 DB 정보 입력
3. `data/credentials/{sid}.json.enc` 자동 생성
4. 작업 완료 후 Backend 종료 가능 (Ctrl+C)

---

### Step 2: 메타데이터 학습 (최초 1회)
#### 방법 1: MCP 도구로 CSV 임포트 (추천) ✅

**CSV 파일 준비:**
```csv
# table_info.csv
table_name,column_name,column_name_kr,description
CUSTOMERS,CUSTOMER_ID,고객ID,고객 고유 번호
CUSTOMERS,CUSTOMER_NAME,고객명,고객 이름
ORDERS,ORDER_ID,주문ID,주문 번호
ORDERS,CUSTOMER_ID,고객ID,주문한 고객
```

**Claude에게 요청:**
```
"테이블 정보 CSV 임포트해줘: D:/metadata/table_info.csv"
```

**결과:**
- Vector DB에 테이블 메타데이터 학습 완료
- `data/vector_db/` 디렉토리에 임베딩 저장
- 즉시 자연어 쿼리 가능

**추가 CSV 파일:**
```
"공통 칼럼 CSV 임포트해줘: D:/metadata/common_columns.csv"
"코드 정의 CSV 임포트해줘: D:/metadata/code_master.csv"
```

---

#### 방법 2: Backend Web UI로 CSV 업로드 (대량 처리 시)

```bash
# Backend 시작
cd backend
python -m uvicorn app.main:app --reload

# Web UI 접속: http://localhost:3000/upload
# CSV 파일 선택 → 업로드 → 학습 완료

# Backend 종료 (Ctrl+C)
# MCP는 계속 동작!
```

---

### Step 3: 자연어로 SQL 생성 및 실행

**이제 Claude에게 자연어로 질문하면 됩니다!**

#### 예시 1: 간단한 조회
```
Claude에게: "고객 목록 보여줘"

→ MCP가 자동으로:
  1. Vector DB에서 CUSTOMERS 테이블 검색
  2. 테이블 구조 확인
  3. SQL 생성: SELECT * FROM CUSTOMERS
  4. Oracle DB 실행
  5. 결과 반환
```

#### 예시 2: 복잡한 집계
```
Claude에게: "지난 1개월간 고객별 주문 금액을 집계해줘"

→ MCP가 자동으로:
  1. Vector DB에서 CUSTOMERS, ORDERS 테이블 검색
  2. 조인 관계 파악
  3. SQL 생성:
     SELECT c.customer_name, SUM(o.amount) as total
     FROM customers c
     JOIN orders o ON c.customer_id = o.customer_id
     WHERE o.order_date >= ADD_MONTHS(SYSDATE, -1)
     GROUP BY c.customer_name
  4. 실행 및 결과 반환
```

#### 예시 3: 테이블 탐색
```
Claude에게: "어떤 테이블들이 있는지 보여줘"
→ show_tables 도구 사용

Claude에게: "EMPLOYEES 테이블 구조 설명해줘"
→ describe_table 도구 사용
```

**💡 핵심: Backend는 꺼져있어도 MCP가 모든 기능 제공!**

---

## 🏗️ 아키텍처

```
사용자 질문
    ↓
MCP Server (Backend 없이 독립 동작)
    ├─ data/credentials/ → DB 접속 정보 읽기
    ├─ data/vector_db/ → 테이블 검색 (의미 기반)
    ├─ LLM → SQL 생성
    ├─ Oracle DB → SQL 실행
    └─ 결과 반환

Backend Server (선택적 학습 도구)
    ├─ Web UI → DB 등록 → data/credentials/
    ├─ Web UI → CSV 업로드 → data/vector_db/
    └─ 학습 후 종료 가능
```

**상세 아키텍처**: [ARCHITECTURE.md](ARCHITECTURE.md)

---

## 📂 프로젝트 구조

```
mcp_db/
├── mcp/                    # MCP Server (독립 동작)
│   ├── mcp_server.py       # 메인 서버 (15 tools)
│   ├── vector_db_client.py # Vector DB 직접 접근
│   ├── oracle_connector.py # DB 연결
│   ├── credentials_manager.py # DB 접속 정보 암호화
│   └── ...
├── backend/                # Backend Server (학습 전용)
│   ├── app/
│   │   ├── main.py         # FastAPI 메인
│   │   ├── api/            # REST API
│   │   └── core/           # 핵심 로직
│   └── requirements.txt
├── frontend/               # Web UI (Next.js)
│   └── app/
├── data/                   # 공유 데이터 디렉토리 ★★★
│   ├── credentials/        # Backend 쓰기, MCP 읽기
│   └── vector_db/          # Backend 쓰기, MCP 읽기
├── .env                    # 환경 변수
├── ARCHITECTURE.md         # 아키텍처 문서
└── README.md               # 이 파일
```

---

## 🔐 보안

- **DB 접속 정보**: AES-256 암호화 → `data/credentials/`
- **환경 변수**: `.env`에 `ENCRYPTION_KEY` 설정 필수
  ```bash
  # .env 파일에 추가
  ENCRYPTION_KEY=your_32_byte_base64_key
  
  # 생성 명령어:
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
  ```
- **Vector DB**: 메타데이터만 저장 (민감정보 없음)
- **MCP**: 읽기 전용, Backend: 읽기/쓰기

---

## 📚 문서

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - 상세 시스템 구조 및 설계 원칙
- **[sql_rules.md](sql_rules.md)** - Oracle SQL 생성 가이드

---

## ⚙️ 요구사항

- **Python**: 3.11+
- **Oracle Instant Client**: cx_Oracle 사용
- **Node.js**: 18+ (Frontend, 선택 사항)

---

## 🚧 트러블슈팅

### MCP 연결 안됨

**증상:** Claude Desktop에서 oracle-nlsql 도구가 보이지 않음

**해결:**
1. Claude Desktop 완전 종료 후 재시작
2. 로그 확인:
   - Windows: `%APPDATA%\Claude\logs\mcp-server-oracle-nlsql.log`
   - Mac/Linux: `~/.config/claude/logs/mcp-server-oracle-nlsql.log`
3. Python 경로 확인: `claude_desktop_config.json`에서 절대 경로 사용
4. 환경변수 확인: `.env` 파일에 `ENCRYPTION_KEY` 설정되어 있는지

### DB 등록 실패

**증상:** "ENCRYPTION_KEY 환경 변수가 설정되지 않았습니다" 에러

**해결:**
```bash
# .env 파일 생성 및 키 추가
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 출력된 키를 .env 파일에 ENCRYPTION_KEY=여기에_붙여넣기
```

### Vector DB 검색 안됨

**증상:** 테이블을 찾지 못하거나 엉뚱한 테이블 반환

**해결:**
```
Claude에게: "Vector DB 상태 확인해줘"
→ 학습된 테이블 개수 확인

# CSV 다시 임포트
"테이블 정보 CSV 임포트해줘: D:/metadata/table_info.csv"
```

### Backend 없이 동작 확인

**테스트:**
```bash
# 1. Backend 종료 (실행 중이라면)
Ctrl+C

# 2. Claude Desktop에서 테스트
"등록된 데이터베이스 목록 보여줘"
"고객 테이블 구조 보여줘"

# MCP가 data/ 폴더만 읽어서 동작하면 정상!
```

---

## 💡 핵심 개념

### 1. MCP는 완전 독립
- Backend API 호출 **없음**
- `data/` 폴더만 읽기
- Backend가 꺼져도 동작

### 2. Backend는 학습 도구
- Web UI로 편리한 관리
- CSV → Vector DB 변환
- 학습 후 종료 가능

### 3. data/ 폴더로 공유
- Backend: 쓰기 (학습)
- MCP: 읽기 (운영)
- 파일 시스템으로 통신

### 4. 사용 우선순위
1. **일상 사용**: MCP 도구만 사용 (Backend 불필요)
2. **대량 작업**: Backend Web UI 사용
3. **학습 완료 후**: Backend 종료, MCP만 실행

---

## 🎯 실전 시나리오

### 시나리오 1: 처음 시작하는 경우

```bash
# 1. 설치 및 설정 (5분)
git clone https://github.com/YouHyuksoo/mcp_db.git
cd mcp_db
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# .env 파일에 ENCRYPTION_KEY 설정

# 2. Claude Desktop 설정 (2분)
# claude_desktop_config.json 편집
# Claude Desktop 재시작

# 3. DB 등록 (1분)
Claude에게: "DB 등록해줘 - SID: PROD, Host: 192.168.1.100, ..."

# 4. 메타데이터 학습 (2분)
Claude에게: "테이블 정보 CSV 임포트해줘: D:/metadata/tables.csv"

# 5. 사용 시작! (즉시)
Claude에게: "지난주 매출 집계해줘"
```

### 시나리오 2: 기존 사용자 - 새 DB 추가

```bash
# Backend 불필요!
Claude에게: "DB 등록해줘 - SID: DEV, Host: ..."
Claude에게: "테이블 정보 CSV 임포트해줘: D:/dev_metadata.csv"
→ 완료! 바로 사용 가능
```

### 시나리오 3: 대량 DB 관리

```bash
# Backend 사용
cd backend
python -m uvicorn app.main:app --reload

# Web UI로 10개 DB 한번에 등록
# CSV 파일 드래그앤드롭으로 업로드

# 작업 완료 후 Backend 종료
Ctrl+C

# MCP는 계속 동작
```

---

## 📝 라이선스

MIT License

---

## 🤝 기여

이슈 및 PR 환영합니다!

- **GitHub**: https://github.com/YouHyuksoo/mcp_db
- **Issues**: https://github.com/YouHyuksoo/mcp_db/issues

---

## 📞 지원

- **문서**: 이 README 및 [ARCHITECTURE.md](ARCHITECTURE.md)
- **예제**: [sql_rules.md](sql_rules.md)
- **문제 보고**: GitHub Issues

---

**버전**: 3.1
**최종 업데이트**: 2025-12-28
**핵심 원칙**: MCP 도구 우선 사용, Backend는 선택적 관리 도구
