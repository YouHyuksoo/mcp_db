# SQL 작성 규칙 (인덱스 최적화)

이 규칙은 Oracle SQL 작성 시 인덱스를 효율적으로 사용하기 위한 가이드라인입니다.

## 1. 날짜 컬럼 검색 (인덱스 사용을 위해 컬럼 변형 금지)

### ❌ 나쁜 예 (인덱스 사용 불가)
```sql
WHERE TRUNC(date_col) = DATE '2025-01-01'
WHERE TO_CHAR(date_col, 'YYYY-MM-DD') = '2025-01-01'
```

### ✅ 좋은 예 (인덱스 사용 가능)
```sql
WHERE date_col >= DATE '2025-01-01' AND date_col < DATE '2025-01-02'
WHERE date_col >= TO_DATE('2025-01-01', 'YYYY-MM-DD')
  AND date_col < TO_DATE('2025-01-02', 'YYYY-MM-DD')
```

## 2. 문자열 검색 (함수 사용 금지)

### ❌ 나쁜 예
```sql
WHERE UPPER(col) = 'VALUE'
WHERE LOWER(col) = 'value'
```

### ✅ 좋은 예
```sql
WHERE col = 'VALUE'
-- 대소문자 구분 없이 검색이 필요한 경우 Function-based Index 고려
```

## 3. 숫자 연산 (컬럼 왼쪽에 연산자 금지)

### ❌ 나쁜 예
```sql
WHERE col * 1.1 > 100
WHERE col + 10 = 50
WHERE col / 2 < 25
```

### ✅ 좋은 예
```sql
WHERE col > 100 / 1.1
WHERE col = 50 - 10
WHERE col < 25 * 2
```

## 4. LIKE 검색

### ✅ 허용 (인덱스 사용 가능)
```sql
WHERE col LIKE 'ABC%'     -- 앞부분 고정
WHERE col LIKE 'A_C%'     -- 앞부분 고정 + 중간 와일드카드
```

### ❌ 금지 (Full Table Scan 발생)
```sql
WHERE col LIKE '%ABC'     -- 끝부분 패턴
WHERE col LIKE '%ABC%'    -- 중간 패턴
```

## 5. NULL 체크

### ✅ 올바른 사용
```sql
WHERE col IS NULL
WHERE col IS NOT NULL
```

### ❌ 잘못된 사용
```sql
WHERE col = NULL      -- 항상 FALSE
WHERE col != NULL     -- 항상 FALSE
```

## 6. IN 조건 vs OR

### ✅ 좋은 예
```sql
WHERE col IN ('A', 'B', 'C')
WHERE col IN (SELECT ...)
```

### ⚠️ 주의
```sql
-- OR 조건이 많은 경우 IN으로 변환 고려
WHERE col = 'A' OR col = 'B' OR col = 'C'  -- IN으로 변경 권장
```

## 7. 복합 인덱스 활용

복합 인덱스 (col1, col2, col3)가 있는 경우:

### ✅ 인덱스 사용 가능
```sql
WHERE col1 = 'A'
WHERE col1 = 'A' AND col2 = 'B'
WHERE col1 = 'A' AND col2 = 'B' AND col3 = 'C'
```

### ❌ 인덱스 사용 불가 (선행 컬럼 누락)
```sql
WHERE col2 = 'B'
WHERE col3 = 'C'
WHERE col2 = 'B' AND col3 = 'C'
```

## 8. 추가 권장사항

1. **바인드 변수 사용**: 하드코딩된 값 대신 바인드 변수 사용
2. **SELECT 절**: 필요한 컬럼만 조회 (SELECT * 지양)
3. **JOIN 순서**: 작은 테이블을 먼저 JOIN
4. **EXISTS vs IN**: 서브쿼리 결과가 큰 경우 EXISTS 사용
5. **DISTINCT 최소화**: 가능하면 GROUP BY로 대체

## 적용 예시

### 어제 데이터 조회 (날짜 범위 검색)
```sql
-- ❌ 나쁜 예
WHERE TRUNC(order_date) = TRUNC(SYSDATE - 1)

-- ✅ 좋은 예
WHERE order_date >= TRUNC(SYSDATE - 1)
  AND order_date < TRUNC(SYSDATE)
```

### 특정 월 데이터 조회
```sql
-- ❌ 나쁜 예
WHERE TO_CHAR(order_date, 'YYYYMM') = '202501'

-- ✅ 좋은 예
WHERE order_date >= DATE '2025-01-01'
  AND order_date < DATE '2025-02-01'
```
