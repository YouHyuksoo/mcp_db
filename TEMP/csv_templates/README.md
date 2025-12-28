# Enhanced Metadata CSV 템플릿 가이드

## 📋 CSV 파일 구조

### 필수 컬럼

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `table_name` | 테이블명 (필수) | CUSTOMERS |
| `korean_name` | 한글 테이블명 | 고객 |
| `description` | 테이블 설명 | 고객 정보 관리 테이블 |

### 컬럼 정보 (선택)

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `column_name` | 컬럼명 | CUSTOMER_ID |
| `column_korean_name` | 한글 컬럼명 | 고객ID |
| `column_description` | 컬럼 설명 | 고객 고유 식별자 |
| `column_type` | 데이터 타입 | NUMBER(10) |
| `is_pk` | Primary Key 여부 | Y/N |
| `nullable` | NULL 허용 여부 | Y/N |
| `code_values` | 코드값 (쉼표 구분) | VIP,GOLD,SILVER |

### 관계 정보 (선택)

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `related_table` | 연관 테이블명 | ORDERS |
| `related_table_korean` | 연관 테이블 한글명 | 주문 |
| `relationship_type` | 관계 유형 | 1:N, N:1, 1:1 |
| `foreign_key` | 외래키 컬럼 | CUSTOMER_ID |
| `relationship_description` | 관계 설명 | 고객의 주문 내역 |

### 비즈니스 규칙 (선택)

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `business_rule` | 규칙명 | VIP 고객 할인 |
| `business_rule_description` | 규칙 설명 | VIP 고객은 전 품목 20% 할인 |

---

## 📝 작성 예시

### 예시 1: 기본 테이블 정보

```csv
table_name,korean_name,description,column_name,column_korean_name,column_description,column_type,is_pk,nullable
CUSTOMERS,고객,고객 정보 관리 테이블,CUSTOMER_ID,고객ID,고객 고유 식별자,NUMBER(10),Y,N
CUSTOMERS,고객,고객 정보 관리 테이블,CUSTOMER_NAME,고객명,고객 이름,VARCHAR2(100),N,N
CUSTOMERS,고객,고객 정보 관리 테이블,EMAIL,이메일,연락용 이메일,VARCHAR2(100),N,Y
```

### 예시 2: 코드값 포함

```csv
table_name,korean_name,description,column_name,column_korean_name,column_description,column_type,is_pk,nullable,code_values
ORDERS,주문,주문 정보 관리,ORDER_STATUS,주문상태,주문 처리 상태,VARCHAR2(20),N,N,"PENDING,CONFIRMED,SHIPPED,DELIVERED,CANCELLED"
```

### 예시 3: 관계 정보

```csv
table_name,korean_name,description,column_name,column_korean_name,column_description,column_type,is_pk,nullable,code_values,related_table,related_table_korean,relationship_type,foreign_key,relationship_description
CUSTOMERS,고객,고객 정보 관리,,,,,,,ORDERS,주문,1:N,CUSTOMER_ID,고객의 주문 내역
CUSTOMERS,고객,고객 정보 관리,,,,,,,CUSTOMER_ADDRESSES,배송지,1:N,CUSTOMER_ID,고객 배송지 정보
```

### 예시 4: 비즈니스 규칙

```csv
table_name,korean_name,description,column_name,column_korean_name,column_description,column_type,is_pk,nullable,code_values,related_table,related_table_korean,relationship_type,foreign_key,relationship_description,business_rule,business_rule_description
CUSTOMERS,고객,고객 정보 관리,,,,,,,,,,,VIP 고객 할인,VIP 고객은 전 품목 20% 할인 적용
CUSTOMERS,고객,고객 정보 관리,,,,,,,,,,,등급 자동 승급,최근 3개월 구매액 100만원 이상 시 GOLD 자동 승급
```

---

## 🎯 작성 팁

### 1. 테이블당 여러 행 작성

하나의 테이블에 대해:
- 첫 행: 테이블 기본 정보 + 첫 번째 컬럼
- 2~N행: 추가 컬럼 (table_name, korean_name, description 반복)
- N+1행: 관계 정보 (컬럼 정보는 비움)
- N+2행: 비즈니스 규칙 (컬럼, 관계 정보는 비움)

### 2. 최소 필수 정보

최소한 다음 정보는 포함 권장:
- 테이블명 (table_name)
- 한글명 (korean_name)
- 설명 (description)
- 핵심 컬럼 3~5개 (PK 포함)

### 3. CSV 인코딩

- **UTF-8 인코딩** 필수
- Excel에서 작성 시 "UTF-8 CSV"로 저장

---

## 📤 업로드 방법

### 방법 1: Backend Web UI

```bash
cd backend
python -m uvicorn app.main:app --reload

# Web UI: http://localhost:3000/upload
# - database_sid 입력
# - schema_name 입력
# - CSV 파일 선택
# - 업로드
```

### 방법 2: MCP Tool (Claude 대화)

```
Claude에게:
"테이블 정보 CSV를 임포트해줘
- 파일: D:/metadata/customers.csv
- Database: MYDB
- Schema: SALES"
```

---

## 🔍 Vector DB 저장 결과

CSV 업로드 후 다음과 같이 저장됩니다:

```
data/vector_db/chroma.sqlite3

Collection: oracle_metadata
├── Document (임베딩 대상):
│   "[MYDB.SALES] CUSTOMERS (고객)
│    설명: 고객 정보 관리 테이블
│    핵심 컬럼: CUSTOMER_ID (고객ID), CUSTOMER_TYPE (고객유형)...
│    비즈니스 로직: VIP 고객 20% 할인...
│    연관 테이블: ORDERS (주문)..."
│
└── Metadata (검색 필터):
    - database_sid: "MYDB"
    - schema_name: "SALES"
    - table_name: "CUSTOMERS"
    - key_columns: JSON
    - related_tables: JSON
    - business_rules: JSON
```

---

## ⚠️ 주의사항

1. **필수 필터**: 검색 시 반드시 database_sid + schema_name 필터 사용
2. **중복 테이블**: 같은 database_sid + schema_name + table_name 조합은 덮어쓰기됨
3. **JSON 필드**: key_columns, related_tables 등은 JSON 문자열로 저장
4. **다중 DB**: 여러 DB의 메타데이터를 하나의 Vector DB에 저장 가능

---

**파일 위치**: `data/csv_templates/enhanced_table_metadata_template.csv`
**최종 업데이트**: 2025-01-09
