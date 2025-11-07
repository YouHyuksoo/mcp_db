# 🔄 아키텍처 변경 사항

**변경일**: 2025-01-05
**변경 사유**: MCP 서버가 Anthropic API를 직접 호출하지 않고, Claude Desktop이 직접 추론하도록 변경

---

## 📋 변경 전 vs 변경 후

### 🔴 변경 전 (잘못된 설계)

```
사용자 질문
    ↓
Claude Desktop
    ↓
MCP 서버
    ↓
[MCP 서버가 Anthropic API 호출]
    ├─ Stage 1: 테이블 선택
    └─ Stage 2: SQL 생성
    ↓
SQL 실행
    ↓
결과 반환
```

**문제점**:
- ❌ Anthropic API 키 필요
- ❌ MCP 서버가 LLM 추론 수행 (역할 혼동)
- ❌ 불필요한 외부 API 호출 비용
- ❌ `two_stage_llm.py` 모듈 불필요

---

### 🟢 변경 후 (올바른 설계)

```
사용자 질문: "최근 1개월간 VIP 고객 주문 내역 보여줘"
    ↓
Claude Desktop이 Stage 1 Tool 호출
    ↓
[get_table_summaries_for_query]
MCP 서버: 테이블 요약 정보 제공
    ↓
Claude Desktop이 메타데이터 분석
    ↓
Claude: "CUSTOMERS, ORDERS 테이블이 필요함"
    ↓
Claude Desktop이 Stage 2 Tool 호출
    ↓
[get_detailed_metadata_for_sql]
MCP 서버: 선택된 테이블의 상세 메타데이터 제공
    ↓
Claude Desktop이 메타데이터로 SQL 생성
    ↓
Claude Desktop이 execute_sql Tool 호출
    ↓
MCP 서버: SQL 실행 후 결과 반환
```

**장점**:
- ✅ **API 키 불필요**: Claude Desktop이 이미 인증된 상태
- ✅ **역할 명확**: MCP 서버는 데이터 제공만, 추론은 Claude가 수행
- ✅ **비용 절감**: 외부 API 호출 없음
- ✅ **코드 간소화**: `two_stage_llm.py` 제거

---

## 🛠️ 주요 변경 사항

### 1. 삭제된 모듈
- ❌ `src/two_stage_llm.py` (더 이상 필요 없음)

### 2. 변경된 Tool (2개 → 2개)

#### 변경 전
| Tool | 설명 |
|------|------|
| `query_natural_language` | 자연어 → SQL 생성 → 실행 (One-shot) |
| `generate_sql_only` | SQL만 생성 (실행 X) |

#### 변경 후
| Tool | 설명 |
|------|------|
| `get_table_summaries_for_query` | **Stage 1**: 테이블 요약 제공 (Claude가 선택) |
| `get_detailed_metadata_for_sql` | **Stage 2**: 상세 메타데이터 제공 (Claude가 SQL 생성) |

### 3. 의존성 제거
**`requirements.txt`**:
```diff
- anthropic>=0.18.0
```

### 4. 환경변수 제거
**`.env.example`**:
```diff
- ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

---

## 📊 새로운 Tool 상세 설명

### Tool 1: `get_table_summaries_for_query`

**용도**: Stage 1 - 전체 테이블 요약 제공

**파라미터**:
- `database_sid`: Database SID
- `schema_name`: 스키마 이름
- `natural_query`: 사용자의 자연어 질문

**반환**:
```markdown
📊 테이블 요약 정보 (Stage 1)

**질문**: 최근 1개월간 VIP 고객 주문 내역 보여줘

### ORDERS
- **목적**: 고객 주문 정보를 저장하고 주문 생명주기를 관리하는 핵심 테이블
- **칼럼 수**: 7
- **주요 칼럼**: ORDER_ID, CUSTOMER_ID, ORDER_DATE, STATUS, AMOUNT
- **연관 테이블**: CUSTOMERS, ORDER_ITEMS, SHIPMENTS

### CUSTOMERS
- **목적**: 고객의 기본 정보 및 연락처를 관리하는 마스터 테이블
- **칼럼 수**: 6
- **주요 칼럼**: CUSTOMER_ID, CUSTOMER_NAME, EMAIL, GRADE
- **연관 테이블**: ORDERS, CUSTOMER_ADDRESSES

...

**다음 단계**: 위 테이블들 중에서 질문에 답하기 위해 필요한 테이블(최대 5개)을 선택하고,
`get_detailed_metadata_for_sql` Tool을 호출하여 상세 메타데이터를 받아 SQL을 생성하세요.
```

**Claude의 판단**:
- 메타데이터 분석 → "CUSTOMERS, ORDERS 필요" 선택

---

### Tool 2: `get_detailed_metadata_for_sql`

**용도**: Stage 2 - 선택된 테이블들의 상세 메타데이터 제공

**파라미터**:
- `database_sid`: Database SID
- `schema_name`: 스키마 이름
- `table_names`: 쉼표로 구분된 테이블명 (예: `"CUSTOMERS,ORDERS"`)
- `natural_query`: 사용자의 자연어 질문

**반환**:
```markdown
📊 상세 메타데이터 (Stage 2)

**질문**: 최근 1개월간 VIP 고객 주문 내역 보여줘
**선택된 테이블**: CUSTOMERS, ORDERS

### CUSTOMERS
- 목적: 고객의 기본 정보 및 연락처를 관리하는 마스터 테이블
- 칼럼 수: 6

### ORDERS
- 목적: 고객 주문 정보를 저장하고 주문 생명주기를 관리하는 핵심 테이블
- 칼럼 수: 7

---

**전체 메타데이터 (SQL 생성용)**:

```json
[
  {
    "database": {"sid": "PROD_DB", "schema": "SCOTT", "table": "CUSTOMERS"},
    "table_info": {
      "business_purpose": "고객의 기본 정보 및 연락처를 관리하는 마스터 테이블",
      ...
    },
    "columns": [
      {
        "name": "CUSTOMER_ID",
        "data_type": "NUMBER(10)",
        "korean_name": "고객번호",
        "description": "고객을 고유하게 식별하는 번호",
        ...
      },
      {
        "name": "GRADE",
        "data_type": "VARCHAR2(20)",
        "korean_name": "회원등급",
        "is_code_column": true,
        "codes": [
          {"value": "VIP", "label": "VIP", "description": "최근 1년간 구매 실적 1000만원 이상"},
          ...
        ]
      }
    ],
    "foreign_keys": [...]
  },
  { /* ORDERS 테이블 메타데이터 */ }
]
```

**다음 단계**: 위 메타데이터를 참고하여 Oracle SQL을 생성한 후,
`execute_sql` Tool을 호출하여 실행하세요.

**Oracle SQL 생성 가이드**:
- Schema.Table 형식 사용 (예: SCOTT.ORDERS)
- Oracle 날짜 함수 사용 (TRUNC, ADD_MONTHS, TO_CHAR 등)
- 코드 칼럼의 경우 코드값으로 WHERE 조건 작성
- FK 정보를 참고하여 정확한 JOIN 조건 작성
```

**Claude의 SQL 생성**:
```sql
SELECT o.ORDER_ID, o.ORDER_DATE, c.CUSTOMER_NAME, o.AMOUNT
FROM SCOTT.ORDERS o
JOIN SCOTT.CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
WHERE c.GRADE = 'VIP'
  AND o.ORDER_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -1)
ORDER BY o.ORDER_DATE DESC
```

---

## 🎯 사용자 경험 비교

### 변경 전 (자동)
```
사용자: "최근 1개월간 VIP 고객 주문 내역 보여줘"
→ [MCP 서버가 자동으로 처리]
→ 결과 표시
```

### 변경 후 (명시적)
```
사용자: "최근 1개월간 VIP 고객 주문 내역 보여줘"
→ Claude: get_table_summaries_for_query 호출
→ Claude: 테이블 선택 (CUSTOMERS, ORDERS)
→ Claude: get_detailed_metadata_for_sql 호출
→ Claude: SQL 생성
→ Claude: execute_sql 호출
→ 결과 표시
```

**차이점**:
- 변경 전: 완전 자동 (블랙박스)
- 변경 후: 단계별 진행 (투명성 ↑, Claude의 추론 과정 확인 가능)

---

## 💡 설계 철학

### 역할 분리 (Separation of Concerns)

**MCP 서버의 역할**:
- ✅ Oracle DB 연결 및 스키마 추출
- ✅ 사용자 CSV 파싱 및 메타데이터 통합
- ✅ 메타데이터 제공 (경량 / 상세)
- ✅ SQL 실행
- ❌ LLM 추론 (이것은 Claude의 역할)

**Claude Desktop의 역할**:
- ✅ 사용자 질문 이해
- ✅ 메타데이터 분석
- ✅ 관련 테이블 선택
- ✅ SQL 생성
- ✅ Tool 호출 순서 결정

---

## 📝 마이그레이션 가이드

### 기존 사용자

**변경 사항**:
1. `.env` 파일에서 `ANTHROPIC_API_KEY` 제거
2. `requirements.txt` 재설치 (anthropic 패키지 제거됨)
3. 새로운 Tool 이름 숙지

**설치 명령**:
```bash
pip install -r requirements.txt
```

### 새 사용자

- API 키 불필요
- Claude Desktop만 있으면 바로 사용 가능

---

## 🎉 결론

**핵심 개선사항**:
1. ✅ **더 이상 Anthropic API 키 불필요**
2. ✅ **MCP 서버는 데이터 제공만 담당** (역할 명확)
3. ✅ **Claude Desktop이 직접 추론** (투명성 ↑)
4. ✅ **코드 간소화** (two_stage_llm.py 제거)
5. ✅ **비용 절감** (외부 API 호출 없음)

**사용자 경험**:
- 기능은 동일하게 유지
- 단계별 진행 과정 확인 가능
- Claude의 추론 과정 투명하게 확인

---

**업데이트 날짜**: 2025-01-05
