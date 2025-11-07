# ✅ Oracle Database MCP 서버 설치 체크리스트

이 문서는 프로젝트 설치 및 설정을 단계별로 안내합니다.

---

## 📋 사전 준비

### 1. 시스템 요구사항
- [ ] Python 3.9 이상 설치됨
- [ ] Oracle Database 접속 가능
- [ ] Claude Desktop 설치됨
- [ ] Anthropic API 키 보유

### 2. 프로젝트 파일
- [ ] `D:\Project\mcp_db` 폴더에 모든 파일 위치
- [ ] `venv` 폴더 존재 (가상환경)
- [ ] `src` 폴더 내 7개 Python 파일 존재

---

## 🔧 1단계: 환경 설정

### 가상환경 활성화
```bash
cd D:\Project\mcp_db
venv\Scripts\activate
```
- [ ] 가상환경 활성화 완료 (프롬프트에 `(venv)` 표시)

### 의존성 확인
```bash
pip list
```
다음 패키지들이 설치되어 있어야 함:
- [ ] mcp (>=1.0.0)
- [ ] oracledb (>=2.0.0)
- [ ] anthropic (>=0.18.0)
- [ ] pandas (>=2.0.0)
- [ ] cryptography (>=41.0.0)
- [ ] python-dotenv (>=1.0.0)
- [ ] python-dateutil (>=2.8.0)

누락된 경우:
```bash
pip install -r requirements.txt
```

---

## 🔑 2단계: API 키 설정

### .env 파일 생성
```bash
copy .env.example .env
```
- [ ] `.env` 파일 생성됨

### API 키 입력
`.env` 파일을 텍스트 에디터로 열고:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```
- [ ] ANTHROPIC_API_KEY 입력 완료

---

## 🖥️ 3단계: Claude Desktop 설정

### 설정 파일 위치
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

파일 탐색기 주소창에 입력:
```
%APPDATA%\Claude
```

### 설정 추가
`claude_desktop_config.json` 파일을 열고 다음 추가:
```json
{
  "mcpServers": {
    "oracle-db": {
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

**주의사항**:
- 경로의 백슬래시(`\`)를 이중 백슬래시(`\\`)로 작성
- 프로젝트 경로가 다르면 위 경로를 실제 경로로 수정

- [ ] 설정 파일 수정 완료

### Claude Desktop 재시작
- [ ] Claude Desktop 완전히 종료
- [ ] Claude Desktop 재시작

---

## 🧪 4단계: MCP 서버 연결 확인

### Claude Desktop에서 확인
Claude Desktop을 열고 새 대화 시작:

**입력**: "어떤 도구들을 사용할 수 있어?"

**기대 결과**: 다음과 같은 도구들이 표시되어야 함:
- register_database_credentials
- extract_and_integrate_metadata
- show_databases
- show_tables
- query_natural_language
- 등 12개 도구

- [ ] MCP 도구 목록 확인됨

**문제 발생 시**:
1. Claude Desktop 재시작
2. 설정 파일 JSON 문법 오류 확인
3. 경로가 정확한지 확인
4. Python 가상환경 경로 확인

---

## 🗄️ 5단계: Oracle Database 등록

### DB 접속 정보 준비
다음 정보가 필요합니다:
- [ ] Database SID (예: PROD_DB)
- [ ] 호스트 주소 (예: db.company.com)
- [ ] 포트 번호 (기본: 1521)
- [ ] 서비스명 또는 SID (예: ORCL)
- [ ] 사용자 이름 (예: scott)
- [ ] 비밀번호

### Claude.ai에서 등록
Claude Desktop에서 다음과 같이 요청:

```
"Oracle 데이터베이스 접속 정보를 등록해줘.
- Database SID: PROD_DB
- 호스트: db.company.com
- 포트: 1521
- 서비스명: ORCL
- 사용자: scott
- 비밀번호: your_password"
```

- [ ] DB 접속 정보 등록 완료
- [ ] `credentials/PROD_DB.json.enc` 파일 생성 확인

---

## 📝 6단계: CSV 메타데이터 작성

### 폴더 생성
```
input/
  └── PROD_DB/          # 등록한 Database SID
      └── SCOTT/        # Schema 이름 (대문자)
```

- [ ] `input/PROD_DB/SCOTT/` 폴더 생성

### CSV 파일 작성

**참고**: `input/EXAMPLE_DB/SCOTT/` 폴더의 예시 파일 참조

#### 1. table_info.csv
- [ ] `table_info.csv` 작성 완료
- [ ] 모든 테이블의 business_purpose 작성됨
- [ ] usage_scenario 3개 작성됨
- [ ] related_tables 작성됨

#### 2. column_info.csv
- [ ] `column_info.csv` 작성 완료
- [ ] 모든 칼럼의 korean_name 작성됨
- [ ] description 작성됨
- [ ] 코드 칼럼은 is_code_column=Y 표시됨

#### 3. code_values.csv
- [ ] `code_values.csv` 작성 완료
- [ ] 모든 코드값의 의미 작성됨
- [ ] 상태 전이 규칙 작성됨 (해당되는 경우)

**CSV 작성 가이드**: `USAGE_GUIDE.md` 참조

---

## 🔄 7단계: 메타데이터 추출 및 통합

### Claude.ai에서 실행
```
"PROD_DB의 SCOTT 스키마 메타데이터를 추출하고 통합해줘"
```

**처리 과정**:
1. Oracle DB 연결
2. 테이블, 칼럼, PK, FK, 인덱스 추출
3. CSV 파일 파싱
4. 통합 메타데이터 생성

- [ ] 메타데이터 추출 성공
- [ ] `metadata/PROD_DB/SCOTT/table_summaries.json` 생성 확인
- [ ] `metadata/PROD_DB/SCOTT/{TABLE}/unified_metadata.json` 생성 확인

**에러 발생 시**:
- Oracle 연결 실패: DB 접속 정보 확인
- CSV 파일 없음: CSV 파일 경로 및 이름 확인
- 파싱 에러: CSV 파일 형식 확인

---

## 🚀 8단계: 자연어 쿼리 테스트

### 간단한 테스트
```
"SCOTT 스키마의 테이블 목록을 보여줘"
```
- [ ] 테이블 목록 정상 출력

### 테이블 구조 확인
```
"ORDERS 테이블의 구조를 보여줘"
```
- [ ] 칼럼, PK, FK, 인덱스 정보 출력

### 자연어 SQL 생성 (핵심)
```
"최근 1개월간 주문 건수를 보여줘"
```

**기대 결과**:
1. Stage 1: 관련 테이블 선택 (ORDERS)
2. Stage 2: SQL 생성
3. SQL 실행
4. 결과 반환

- [ ] SQL 자동 생성됨
- [ ] SQL 실행 성공
- [ ] 결과 정상 출력

---

## 🎓 9단계: 복잡한 쿼리 테스트

### 다중 테이블 JOIN
```
"VIP 고객의 최근 주문 내역을 보여줘"
```
- [ ] CUSTOMERS와 ORDERS JOIN 성공
- [ ] WHERE 조건에 GRADE='VIP' 적용됨

### 집계 쿼리
```
"월별 매출 집계를 보여줘"
```
- [ ] GROUP BY 적용됨
- [ ] Oracle 날짜 함수 사용됨 (TO_CHAR, TRUNC 등)

### 코드값 매핑
```
"주문 상태가 '배송중'인 주문을 보여줘"
```
- [ ] "배송중" → 코드값 자동 변환
- [ ] WHERE STATUS='03' (또는 해당 코드) 생성됨

---

## ✅ 설치 완료

모든 체크 항목이 완료되었다면 설치 성공입니다!

### 최종 확인
- [ ] MCP 서버 연결 확인
- [ ] Oracle DB 접속 확인
- [ ] 메타데이터 추출 성공
- [ ] 자연어 쿼리 실행 성공

---

## 🔧 문제 해결

### MCP 서버가 표시되지 않음
1. Claude Desktop 재시작
2. `claude_desktop_config.json` 문법 오류 확인
3. Python 경로 확인
4. 가상환경 활성화 확인

### Oracle 연결 실패
1. DB 접속 정보 재확인
2. 방화벽/네트워크 확인
3. Oracle Listener 상태 확인
4. 접속 정보 재등록

### CSV 파일 오류
1. 파일 경로 확인: `input/{DB_SID}/{SCHEMA}/`
2. 파일명 확인: `table_info.csv`, `column_info.csv`, `code_values.csv`
3. CSV 인코딩 확인: UTF-8
4. 칼럼 헤더 확인

### SQL 생성이 부정확함
1. CSV 파일의 설명을 더 상세히 작성
2. business_rule 추가
3. code_values.csv에 모든 코드값 정의
4. 메타데이터 재추출

---

## 📚 추가 자료

- **README.md**: 프로젝트 개요
- **USAGE_GUIDE.md**: 상세 사용 가이드
- **PROJECT_COMPLETION_SUMMARY.md**: 프로젝트 완료 보고서
- **input/EXAMPLE_DB/SCOTT/**: CSV 예시 파일

---

**설치 문의 및 이슈**: GitHub Issues 또는 프로젝트 문서 참조

**마지막 업데이트**: 2025-01-05
