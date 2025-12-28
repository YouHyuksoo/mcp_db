# Oracle NL-SQL MCP Server - 워크플로우 설계

## 전체 워크플로우 개요

```
┌─────────────────────────────────────────────────────────────────┐
│                    1단계: DB 정보 등록 (TNSNames)                  │
├─────────────────────────────────────────────────────────────────┤
│ • tnsnames.ora 파싱                                              │
│ • Oracle DB 연결 정보 추출                                        │
│ • 사용자 인증 정보 암호화 저장 (credentials/)                      │
│ • 등록된 DB 목록 관리                                             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│              2단계: 메타데이터 통합 및 벡터화 (Upload)              │
├─────────────────────────────────────────────────────────────────┤
│ • CSV 3종 업로드:                                                │
│   1. table_info_template.csv (테이블 기본 정보)                  │
│   2. common_columns_template.csv (공통 컬럼 정의)                │
│   3. code_definitions_template.csv (코드 값 정의)                │
│ • DB 스키마와 연동하여 통합 메타정보 생성                          │
│ • 메타정보 임베딩 (sentence-transformers)                        │
│ • Vector DB에 저장 (ChromaDB - metadata collection)             │
│ • data/{database_sid}/{schema_name}/metadata/ 에 JSON 저장       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│           3단계: 패턴 학습 및 벡터화 (Patterns)                    │
├─────────────────────────────────────────────────────────────────┤
│ • SQL 학습 패턴:                                                 │
│   - 사용자 질문 + SQL 쿼리 쌍                                     │
│   - 성공/실패 피드백 학습                                         │
│   - 사용 빈도 및 성공률 추적                                      │
│ • PowerBuilder 파싱 패턴:                                        │
│   - .pbl, .srd 파일 파싱                                         │
│   - DataWindow 정의 추출                                         │
│   - SQL 쿼리 패턴 추출                                           │
│   - 비즈니스 로직 추출                                            │
│ • 모든 패턴 임베딩 및 벡터화                                      │
│ • Vector DB에 저장 (ChromaDB - patterns collection)             │
│ • MCP Tools에 컨텍스트 제공                                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                 4단계: MCP Tools 활용 (실행)                      │
├─────────────────────────────────────────────────────────────────┤
│ • 자연어 질의 입력                                                │
│ • Vector DB에서 관련 메타데이터 + 패턴 검색                       │
│ • LLM을 통한 SQL 생성                                            │
│ • Oracle DB 실행                                                 │
│ • 결과 반환 및 패턴 학습                                          │
└─────────────────────────────────────────────────────────────────┘
```

## 1단계: TNSNames 페이지 (DB 정보 등록)

### 목적
- Oracle 데이터베이스 연결 정보를 시스템에 등록
- 모든 워크플로우의 시작점

### 기능
1. **tnsnames.ora 파일 파싱**
   - 파일 경로: 사용자 지정 또는 기본 경로
   - TNS 항목 목록 표시
   - SID, Host, Port, Service Name 추출

2. **DB 등록**
   - TNS 항목 선택
   - 사용자명/비밀번호 입력
   - 연결 테스트
   - 암호화하여 저장 (`credentials/{database_sid}.json.enc`)

3. **등록된 DB 관리**
   - 등록된 DB 목록 표시
   - 연결 상태 확인
   - 삭제 기능

### 데이터 저장 위치
```
credentials/
  ├── {database_sid}.json.enc    # 암호화된 인증 정보
data/
  └── tnsnames/
      └── parsed_entries.json     # 파싱된 TNS 항목 캐시
```

### UI 개선사항
- ✅ 현재 구조 유지
- ✅ 등록 상태 명확히 표시
- 🔄 워크플로우 진행 상태 표시 추가 필요

---

## 2단계: Upload 페이지 (메타데이터 통합 및 벡터화)

### 목적
- CSV 3종을 업로드하여 DB 스키마와 연동
- 통합 메타정보 생성 및 Vector DB 저장

### 전제조건
- 1단계에서 DB가 최소 1개 이상 등록되어 있어야 함

### 워크플로우

#### Step 1: DB 선택
```tsx
<Select>
  <SelectTrigger>데이터베이스 선택</SelectTrigger>
  <SelectContent>
    {registeredDatabases.map(db => (
      <SelectItem value={`${db.database_sid}:${db.schema_name}`}>
        {db.database_sid} ({db.schema_name})
      </SelectItem>
    ))}
  </SelectContent>
</Select>
```

#### Step 2: CSV 3종 업로드
```
┌─────────────────────────────────────────┐
│ 1. table_info_template.csv              │
│    - table_name (테이블명)               │
│    - table_comment (테이블 설명)         │
│    - business_purpose (비즈니스 목적)    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 2. common_columns_template.csv          │
│    - column_name (컬럼명)                │
│    - data_type (데이터 타입)             │
│    - column_comment (컬럼 설명)          │
│    - business_meaning (비즈니스 의미)    │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ 3. code_definitions_template.csv        │
│    - code_column (코드 컬럼명)           │
│    - code_value (코드 값)                │
│    - code_meaning (코드 의미)            │
└─────────────────────────────────────────┘
```

#### Step 3: 통합 메타정보 생성
```python
# Backend API: POST /api/metadata/process
{
  "database_sid": "ORCL",
  "schema_name": "HR",
  "table_info_file": "file1.csv",
  "common_columns_file": "file2.csv",
  "code_definitions_file": "file3.csv"
}

# 처리 과정:
1. CSV 파싱
2. Oracle DB에 연결하여 실제 스키마 정보 조회
3. CSV 정보 + DB 스키마 정보 통합
4. 각 테이블별 JSON 메타데이터 생성
5. 임베딩 생성 (sentence-transformers/all-MiniLM-L6-v2)
6. Vector DB에 저장 (collection: metadata)
7. 파일 시스템에 저장 (data/{sid}/{schema}/metadata/)
```

#### Step 4: 진행 상태 표시
```tsx
<Card>
  <CardHeader>
    <CardTitle>처리 진행 상황</CardTitle>
  </CardHeader>
  <CardContent>
    <Progress value={progress} />
    <div className="space-y-2 mt-4">
      <StatusItem status="completed" text="CSV 파일 검증" />
      <StatusItem status="in_progress" text="DB 스키마 조회 중..." />
      <StatusItem status="pending" text="메타정보 통합" />
      <StatusItem status="pending" text="임베딩 생성" />
      <StatusItem status="pending" text="Vector DB 저장" />
    </div>
  </CardContent>
</Card>
```

### 데이터 저장 위치
```
data/
  └── {database_sid}/
      └── {schema_name}/
          ├── metadata/
          │   ├── EMPLOYEES.json
          │   ├── DEPARTMENTS.json
          │   └── ...
          ├── csv_uploads/
          │   ├── table_info_template.csv
          │   ├── common_columns_template.csv
          │   └── code_definitions_template.csv
          └── upload_history.json

vector_db/
  └── chroma/
      └── metadata/                # ChromaDB collection
```

### Backend API 엔드포인트
```python
# POST /api/metadata/upload
# - CSV 파일 3개 업로드 및 임시 저장

# POST /api/metadata/process
# - DB 스키마 조회 및 통합 처리
# - 임베딩 생성 및 Vector DB 저장

# GET /api/metadata/status/{job_id}
# - 처리 진행 상태 조회

# GET /api/metadata/list
# - 등록된 메타데이터 목록 조회 (DB별)
```

---

## 3단계: Patterns 페이지 (패턴 학습 및 벡터화)

### 목적
- SQL 학습 패턴 관리
- PowerBuilder 파싱 패턴 추출 및 저장
- 모든 패턴을 벡터화하여 MCP Tools에 제공

### 3-1: SQL 학습 패턴

#### 기능
1. **수동 패턴 등록**
   ```tsx
   <Dialog>
     <DialogContent>
       <FormField label="질문" value={question} />
       <FormField label="SQL 쿼리" value={sqlQuery} />
       <FormField label="설명" value={description} />
       <Button onClick={handleAddPattern}>패턴 추가</Button>
     </DialogContent>
   </Dialog>
   ```

2. **자동 학습 패턴**
   - MCP Tools 실행 시 성공한 쿼리 자동 저장
   - 사용 빈도 추적
   - 성공률 계산

3. **패턴 목록 표시**
   ```tsx
   <Table>
     <TableHead>
       <TableRow>
         <TableHead>질문</TableHead>
         <TableHead>SQL 패턴</TableHead>
         <TableHead>사용 횟수</TableHead>
         <TableHead>성공률</TableHead>
         <TableHead>마지막 사용</TableHead>
       </TableRow>
     </TableHead>
     <TableBody>
       {patterns.map(pattern => (
         <TableRow>
           <TableCell>{pattern.question}</TableCell>
           <TableCell><CodeBlock>{pattern.sql}</CodeBlock></TableCell>
           <TableCell>{pattern.useCount}</TableCell>
           <TableCell>{pattern.successRate}%</TableCell>
           <TableCell>{pattern.lastUsed}</TableCell>
         </TableRow>
       ))}
     </TableBody>
   </Table>
   ```

### 3-2: PowerBuilder 파싱 패턴

#### 기능
1. **PowerBuilder 파일 업로드**
   ```tsx
   <DropZone
     accept=".pbl,.srd,.srw"
     onDrop={handlePowerBuilderUpload}
   >
     PowerBuilder 파일을 드래그하거나 클릭하여 업로드
   </DropZone>
   ```

2. **파싱 및 패턴 추출**
   ```python
   # Backend: POST /api/patterns/powerbuilder/parse
   {
     "file": "uploaded_file.pbl",
     "database_sid": "ORCL",
     "schema_name": "HR"
   }

   # 추출 항목:
   - DataWindow 정의
   - SQL 쿼리 패턴
   - WHERE 조건 패턴
   - JOIN 패턴
   - 비즈니스 규칙 (스크립트 분석)
   ```

3. **추출된 패턴 표시**
   ```tsx
   <Tabs>
     <TabsList>
       <TabsTrigger value="datawindows">DataWindows</TabsTrigger>
       <TabsTrigger value="queries">SQL Queries</TabsTrigger>
       <TabsTrigger value="business_rules">Business Rules</TabsTrigger>
     </TabsList>
     <TabsContent value="datawindows">
       <DataWindowList dataWindows={extractedDataWindows} />
     </TabsContent>
     {/* ... */}
   </Tabs>
   ```

### 데이터 저장 위치
```
data/
  └── {database_sid}/
      └── {schema_name}/
          ├── patterns/
          │   ├── learned_patterns.json      # SQL 학습 패턴
          │   ├── powerbuilder_patterns.json # PB 파싱 패턴
          │   └── business_rules.json        # 비즈니스 규칙
          └── powerbuilder/
              ├── uploads/
              │   ├── app.pbl
              │   └── reports.srd
              └── parsed/
                  ├── datawindows.json
                  └── queries.json

vector_db/
  └── chroma/
      ├── patterns/              # SQL 패턴 collection
      └── business_rules/        # 비즈니스 규칙 collection
```

### Backend API 엔드포인트
```python
# SQL 학습 패턴
# POST /api/patterns/add
# GET /api/patterns/list
# PUT /api/patterns/{pattern_id}/feedback
# DELETE /api/patterns/{pattern_id}

# PowerBuilder 파싱
# POST /api/patterns/powerbuilder/upload
# POST /api/patterns/powerbuilder/parse
# GET /api/patterns/powerbuilder/list
# GET /api/patterns/powerbuilder/{file_id}/details
```

---

## 4단계: Dashboard (워크플로우 진행 상태)

### 개선사항

#### 워크플로우 상태 카드 추가
```tsx
<Card className="col-span-full">
  <CardHeader>
    <CardTitle>워크플로우 진행 상태</CardTitle>
  </CardHeader>
  <CardContent>
    <div className="grid grid-cols-3 gap-4">
      {/* 1단계: DB 등록 */}
      <WorkflowStep
        stepNumber={1}
        title="DB 정보 등록"
        status={dbCount > 0 ? "completed" : "pending"}
        description={`${dbCount}개 데이터베이스 등록됨`}
        link="/tnsnames"
      />

      {/* 2단계: 메타데이터 */}
      <WorkflowStep
        stepNumber={2}
        title="메타데이터 통합"
        status={metadataCount > 0 ? "completed" : dbCount > 0 ? "available" : "locked"}
        description={`${metadataCount}개 테이블 메타데이터`}
        link="/upload"
      />

      {/* 3단계: 패턴 학습 */}
      <WorkflowStep
        stepNumber={3}
        title="패턴 학습"
        status={patternsCount > 0 ? "completed" : metadataCount > 0 ? "available" : "locked"}
        description={`${patternsCount}개 학습된 패턴`}
        link="/patterns"
      />
    </div>
  </CardContent>
</Card>
```

#### 선택된 DB 상세 정보
- ✅ 현재 구조 유지
- 테이블 수, 패턴 수, 마지막 업데이트 시간 표시

---

## Vector DB 구조

### ChromaDB Collections

```python
# 1. metadata collection
{
  "id": "{database_sid}_{schema_name}_{table_name}",
  "embedding": [...],  # 임베딩 벡터
  "metadata": {
    "database_sid": "ORCL",
    "schema_name": "HR",
    "table_name": "EMPLOYEES",
    "table_comment": "직원 정보",
    "business_purpose": "직원 관리",
    "columns": [...],
    "indexes": [...],
    "constraints": [...]
  },
  "document": "직원 정보 테이블: 직원의 기본 정보와 부서 정보를 관리..."
}

# 2. patterns collection
{
  "id": "{pattern_id}",
  "embedding": [...],
  "metadata": {
    "database_sid": "ORCL",
    "schema_name": "HR",
    "question": "전체 직원 수를 알려줘",
    "sql": "SELECT COUNT(*) FROM EMPLOYEES",
    "use_count": 15,
    "success_rate": 0.95,
    "learned_at": "2025-01-09T10:00:00Z"
  },
  "document": "전체 직원 수를 알려줘 -> SELECT COUNT(*) FROM EMPLOYEES"
}

# 3. business_rules collection
{
  "id": "{rule_id}",
  "embedding": [...],
  "metadata": {
    "database_sid": "ORCL",
    "schema_name": "HR",
    "source": "employee_report.srd",
    "source_type": "powerbuilder_datawindow",
    "rule_type": "validation",
    "tables": ["EMPLOYEES", "DEPARTMENTS"]
  },
  "document": "직원 급여는 부서별 최소 급여 이상이어야 함..."
}
```

---

## MCP Tools와의 연동

### MCP Server가 제공하는 정보

```python
# Tool: search_metadata
# - Vector DB에서 관련 테이블 메타데이터 검색
# - 입력: 자연어 질의
# - 출력: 관련 테이블 목록 + 상세 정보

# Tool: search_patterns
# - Vector DB에서 유사한 SQL 패턴 검색
# - 입력: 자연어 질의
# - 출력: 유사 패턴 목록 + SQL 쿼리

# Tool: search_business_rules
# - Vector DB에서 관련 비즈니스 규칙 검색
# - 입력: 테이블명 또는 자연어
# - 출력: 적용 가능한 비즈니스 규칙

# Tool: execute_query
# - 생성된 SQL을 실제 Oracle DB에서 실행
# - 결과를 패턴으로 학습
```

---

## 구현 우선순위

### Phase 1: 기본 워크플로우 (현재 작업)
1. ✅ TNSNames 페이지 구조 완성
2. 🔄 Upload 페이지 구현
   - DB 선택
   - CSV 3종 업로드
   - 통합 처리 백엔드 API
   - 진행 상태 표시
3. 🔄 Dashboard 워크플로우 상태 표시

### Phase 2: 패턴 학습
4. ⏳ Patterns 페이지 - SQL 학습 패턴
5. ⏳ Patterns 페이지 - PowerBuilder 파싱

### Phase 3: 고도화
6. ⏳ 패턴 자동 학습 강화
7. ⏳ 성능 모니터링 및 최적화
8. ⏳ 사용자 피드백 시스템

---

## 기술 스택 정리

### Frontend
- Next.js 16 (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- React Hook Form (폼 관리)
- Axios (HTTP 클라이언트)

### Backend
- FastAPI
- Python 3.11+
- ChromaDB (Vector DB)
- sentence-transformers (임베딩)
- cx_Oracle (Oracle DB 연결)
- cryptography (인증 정보 암호화)

### MCP Server
- Python MCP SDK
- 17 Tools for SQL execution
- Shared data/ directory

---

## 다음 단계

1. **Upload 페이지 구현 시작**
   - DB 선택 UI
   - CSV 파일 업로드 UI (3종)
   - 진행 상태 표시 컴포넌트

2. **Backend API 구현**
   - `/api/metadata/upload` - CSV 업로드
   - `/api/metadata/process` - 통합 처리
   - `/api/metadata/status/{job_id}` - 진행 상태

3. **Dashboard 개선**
   - 워크플로우 상태 카드 추가
   - 단계별 진행 상황 시각화
