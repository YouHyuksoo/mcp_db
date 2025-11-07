# 📊 메타데이터 가이드

## 개요

이 가이드는 Oracle Database의 스키마 정보에 비즈니스 의미를 추가하는 방법을 설명합니다.

---

## 메타데이터 구조

### 1. DB 스키마 메타데이터 (자동 추출)

Oracle Database에서 자동으로 추출되는 기술 정보:

```json
{
  "table_name": "CUSTOMERS",
  "columns": [
    {
      "column_name": "CUSTOMER_ID",
      "data_type": "NUMBER(10)",
      "nullable": "N"
    }
  ],
  "primary_keys": ["CUSTOMER_ID"],
  "foreign_keys": [...],
  "indexes": [...]
}
```

### 2. 공통 메타데이터 (사용자 작성)

비즈니스 의미를 추가하는 3가지 CSV 파일:

#### common_columns.csv
- 여러 테이블에서 공통으로 사용되는 칼럼 정의
- 예: CREATE_DATE, UPDATE_USER 등

#### code_definitions.csv
- 칼럼에 사용되는 코드값의 의미
- 예: STATUS='A' → '활성'

#### table_info.csv
- 테이블별 특화 정보
- 예: 테이블 한글명, 칼럼 한글명, 설명

---

## CSV 파일 작성 가이드

### 📋 common_columns.csv

**위치**: `common_metadata/<DB_SID>/common_columns.csv`

**용도**: 여러 테이블에서 공통으로 사용되는 칼럼의 의미 정의

**형식**:
```csv
column_name,column_name_kr,description
CREATE_DATE,생성일시,레코드 생성 일시
CREATE_USER,생성자,레코드 생성 사용자 ID
UPDATE_DATE,수정일시,최종 수정 일시
UPDATE_USER,수정자,최종 수정 사용자 ID
DELETE_YN,삭제여부,삭제 여부 (Y/N)
USE_YN,사용여부,사용 여부 (Y/N)
COMPANY_CODE,회사코드,회사 구분 코드
PLANT_CODE,공장코드,공장 구분 코드
```

**필드 설명**:
- `column_name`: 칼럼명 (대문자)
- `column_name_kr`: 한글 칼럼명
- `description`: 칼럼 설명

**작성 팁**:
1. 모든 테이블에서 공통으로 사용되는 칼럼만 정의
2. 테이블별로 의미가 다른 칼럼은 table_info.csv에 정의
3. UTF-8 인코딩 필수

---

### 🔢 code_definitions.csv

**위치**: `common_metadata/<DB_SID>/code_definitions.csv`

**용도**: 칼럼의 코드값 의미 정의

**형식**:
```csv
column_name,code_value,code_name,description
STATUS,A,활성,활성 상태
STATUS,I,비활성,비활성 상태
STATUS,D,삭제,삭제된 상태
GRADE,VIP,VIP고객,VIP 등급 고객
GRADE,GOLD,골드고객,골드 등급 고객
GRADE,SILVER,실버고객,실버 등급 고객
ORDER_STATUS,PENDING,대기,주문 대기 중
ORDER_STATUS,CONFIRMED,확정,주문 확정
ORDER_STATUS,SHIPPED,출하,출하 완료
ORDER_STATUS,DELIVERED,배송완료,배송 완료
ORDER_STATUS,CANCELLED,취소,주문 취소
```

**필드 설명**:
- `column_name`: 칼럼명 (대문자)
- `code_value`: 코드값 (DB에 저장된 실제 값)
- `code_name`: 코드 이름 (한글)
- `description`: 코드 설명

**작성 팁**:
1. 같은 칼럼명이 여러 테이블에서 같은 의미로 사용될 때 유용
2. 테이블별로 다른 코드 체계를 사용하면 table_info.csv에 정의
3. 모든 가능한 코드값을 나열

---

### 📊 table_info.csv

**위치**: `common_metadata/<DB_SID>/<SCHEMA>/table_info.csv`

**용도**: 테이블 및 칼럼별 특화 정보

**형식**:
```csv
table_name,column_name,column_name_kr,description,sample_values
CUSTOMERS,TABLE,고객,고객 마스터 테이블,
CUSTOMERS,CUSTOMER_ID,고객ID,고객 고유 식별자,C001|C002|C003
CUSTOMERS,CUSTOMER_NAME,고객명,고객 이름,홍길동|김철수|이영희
CUSTOMERS,PHONE,전화번호,고객 연락처,010-1234-5678
CUSTOMERS,EMAIL,이메일,이메일 주소,hong@example.com
CUSTOMERS,GRADE,등급,고객 등급 (VIP/GOLD/SILVER),VIP|GOLD|SILVER
CUSTOMERS,TOTAL_AMOUNT,총구매액,누적 구매 금액,1000000|500000
ORDERS,TABLE,주문,주문 내역 테이블,
ORDERS,ORDER_ID,주문ID,주문 고유 번호,ORD-2024-001|ORD-2024-002
ORDERS,CUSTOMER_ID,고객ID,주문한 고객 ID (CUSTOMERS 참조),C001
ORDERS,ORDER_DATE,주문일자,주문 일자,2024-01-15
ORDERS,TOTAL_PRICE,총금액,주문 총 금액,150000
```

**필드 설명**:
- `table_name`: 테이블명 (대문자)
- `column_name`: 칼럼명 (대문자, 또는 'TABLE'로 테이블 자체 설명)
- `column_name_kr`: 한글 이름
- `description`: 설명
- `sample_values`: 샘플 데이터 (파이프 `|`로 구분)

**특별 행**:
```csv
CUSTOMERS,TABLE,고객,고객 마스터 테이블,
```
- `column_name`이 'TABLE'인 행은 테이블 자체에 대한 설명

**작성 팁**:
1. 테이블별로 특화된 의미가 있는 칼럼 정의
2. common_columns.csv에 있는 공통 칼럼은 제외 가능
3. sample_values는 LLM이 데이터 형식을 이해하는데 도움

---

## CSV → JSON 변환

CSV 파일은 MCP 서버가 JSON으로 자동 변환합니다:

### CSV Import Tool 사용

```
Claude에게 요청:
"common_metadata/SMVNPDBext/ 폴더의 CSV 파일들을 임포트해줘"
```

MCP 서버가 자동으로:
1. `common_columns.csv` → `common_columns.json`
2. `code_definitions.csv` → `code_definitions.json`
3. `table_info.csv` → `table_info.json`

### 직접 변환 (Python 스크립트)

```bash
# 공통 칼럼 CSV 생성
python generate_common_columns.py

# 코드 정의 CSV 생성
python generate_code_definitions.py

# 테이블 정보 CSV 생성
python generate_table_info.py
```

---

## 메타데이터 통합 프로세스

### 1단계: CSV 작성

```
common_metadata/
└── SMVNPDBext/
    ├── common_columns.csv          ← 작성
    ├── code_definitions.csv        ← 작성
    └── INFINITY21_JSMES/
        └── table_info.csv          ← 작성
```

### 2단계: CSV 임포트

Claude에게 요청:
```
SMVNPDBext 데이터베이스의 공통 칼럼 CSV를 임포트해줘:
common_metadata/SMVNPDBext/common_columns.csv
```

### 3단계: 스키마 추출 및 통합

Claude에게 요청:
```
INFINITY21_JSMES 스키마의 메타데이터를 추출하고
공통 메타데이터와 통합해줘
```

### 4단계: 결과 확인

```
metadata/
└── SMVNPDBext/
    └── INFINITY21_JSMES/
        ├── CUSTOMERS/
        │   └── unified_metadata.json    ← 통합 완료
        └── ORDERS/
            └── unified_metadata.json    ← 통합 완료
```

**unified_metadata.json 예시**:
```json
{
  "table_name": "CUSTOMERS",
  "table_name_kr": "고객",
  "description": "고객 마스터 테이블",
  "columns": [
    {
      "column_name": "CUSTOMER_ID",
      "column_name_kr": "고객ID",
      "data_type": "NUMBER(10)",
      "nullable": "N",
      "description": "고객 고유 식별자",
      "sample_values": ["C001", "C002", "C003"]
    },
    {
      "column_name": "GRADE",
      "column_name_kr": "등급",
      "data_type": "VARCHAR2(10)",
      "description": "고객 등급",
      "code_values": [
        {"code": "VIP", "name": "VIP고객", "description": "VIP 등급 고객"},
        {"code": "GOLD", "name": "골드고객", "description": "골드 등급 고객"}
      ]
    },
    {
      "column_name": "CREATE_DATE",
      "column_name_kr": "생성일시",
      "data_type": "DATE",
      "description": "레코드 생성 일시"
    }
  ],
  "primary_keys": ["CUSTOMER_ID"],
  "foreign_keys": [],
  "indexes": [...]
}
```

---

## 자동 CSV 템플릿 생성

MCP 서버는 스키마에서 CSV 템플릿을 자동 생성할 수 있습니다:

```
Claude에게 요청:
"INFINITY21_JSMES 스키마에서 CSV 템플릿을 생성해줘:
출력 디렉토리: common_metadata/SMVNPDBext/INFINITY21_JSMES/"
```

생성 결과:
```
common_metadata/SMVNPDBext/INFINITY21_JSMES/
├── common_columns_from_schema.csv
├── code_definitions_from_schema.csv
└── table_info_from_schema.csv
```

**사용자가 할 일**:
1. 생성된 CSV 파일 열기
2. 한글명, 설명, 코드값 등 비즈니스 의미 추가
3. 파일명에서 `_from_schema` 제거
4. CSV 임포트 및 메타데이터 통합 실행

---

## 메타데이터 업데이트

### 신규 테이블 추가
1. `table_info.csv`에 새 테이블 정보 추가
2. CSV 재임포트
3. 메타데이터 재추출

### 기존 테이블 수정
1. CSV 파일 수정
2. CSV 재임포트
3. 해당 테이블만 재추출 (전체 재추출 불필요)

### 코드값 추가
1. `code_definitions.csv`에 새 코드 추가
2. CSV 재임포트
3. 메타데이터 재추출

---

## 베스트 프랙티스

### ✅ DO
1. **UTF-8 인코딩 사용**: Excel에서는 "CSV UTF-8" 형식으로 저장
2. **일관된 명명**: 칼럼명은 대문자, 한글명은 간결하게
3. **상세한 설명**: LLM이 이해할 수 있도록 명확히 작성
4. **샘플 데이터 제공**: 데이터 형식 이해에 도움
5. **버전 관리**: CSV 파일도 Git으로 관리

### ❌ DON'T
1. **중복 정의 피하기**: 같은 칼럼을 여러 곳에 정의하지 말 것
2. **특수문자 주의**: CSV에서 쉼표, 따옴표 사용 시 이스케이프
3. **과도한 정보**: 불필요한 칼럼까지 모두 정의하지 말 것
4. **ANSI 인코딩**: 한글 깨짐 발생

---

## 트러블슈팅

### 한글 깨짐
- **원인**: CSV 파일이 ANSI 인코딩
- **해결**: UTF-8로 다시 저장

### 칼럼 정보가 적용 안됨
- **원인**: CSV 임포트 후 메타데이터 재추출 안함
- **해결**: `extract_and_integrate_metadata` 재실행

### 코드값이 안 보임
- **원인**: `column_name`이 대소문자 불일치
- **해결**: CSV에서 칼럼명을 대문자로 수정

### 테이블 설명이 안 보임
- **원인**: `TABLE` 행 누락
- **해결**: `table_info.csv`에 TABLE 행 추가

---

## 예제: 전체 워크플로우

```
# 1. CSV 템플릿 생성
"INFINITY21_JSMES 스키마에서 CSV 템플릿을 생성해줘"

# 2. CSV 파일 편집 (Excel 또는 텍스트 에디터)
# - 한글명 추가
# - 설명 추가
# - 코드값 추가

# 3. CSV 임포트
"common_metadata/SMVNPDBext/ 폴더의 CSV 파일들을 임포트해줘"

# 4. 메타데이터 통합
"INFINITY21_JSMES 스키마의 메타데이터를 추출하고 공통 메타데이터와 통합해줘"

# 5. 자연어 질의 테스트
"지난 1개월간 VIP 고객의 주문 내역을 보여줘"
```

---

## 참고 자료

- [프로젝트 구조](../README.md#프로젝트-구조)
- [아키텍처](ARCHITECTURE.md)
- [CSV 템플릿](../common_metadata/)
