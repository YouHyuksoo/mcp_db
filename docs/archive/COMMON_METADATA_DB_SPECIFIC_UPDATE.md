# 공통 메타데이터 DB별 관리 업데이트

**업데이트 날짜**: 2025-01-06
**변경 사유**: 공통 메타데이터가 전체가 아닌 **각 DB별로 관리**되어야 함

---

## 📋 핵심 변경사항

### 변경 전 (잘못된 구조)
```
common_metadata/
├── common_columns.json          # 전체 DB 공용 ❌
└── code_definitions.json        # 전체 DB 공용 ❌
```

**문제점**:
- 모든 DB가 같은 공통 메타데이터를 공유
- DB마다 다른 칼럼 정의/코드 체계를 지원할 수 없음
- 예: PROD_DB의 STATUS와 TEST_DB의 STATUS가 다른 코드를 사용하는 경우 처리 불가

### 변경 후 (올바른 구조)
```
common_metadata/
├── PROD_DB/
│   ├── common_columns.json      # PROD_DB 전용 ✅
│   └── code_definitions.json    # PROD_DB 전용 ✅
├── TEST_DB/
│   ├── common_columns.json      # TEST_DB 전용 ✅
│   └── code_definitions.json    # TEST_DB 전용 ✅
└── {DB_SID}/
    ├── common_columns.json
    └── code_definitions.json
```

**장점**:
- ✅ 각 DB가 독립적인 공통 메타데이터 관리
- ✅ DB별로 다른 칼럼 정의 지원
- ✅ DB별로 다른 코드 체계 지원
- ✅ DB 간 충돌 없음

---

## 🛠️ 변경된 파일

### 1. `src/common_metadata_manager.py`

모든 메서드에 `database_sid` 파라미터 추가:

#### 변경된 메서드 시그니처

| 변경 전 | 변경 후 |
|--------|--------|
| `save_common_columns(columns)` | `save_common_columns(database_sid, columns)` |
| `load_common_columns()` | `load_common_columns(database_sid)` |
| `get_column_info(column_name)` | `get_column_info(database_sid, column_name)` |
| `delete_column(column_name)` | `delete_column(database_sid, column_name)` |
| `save_code_definitions(codes)` | `save_code_definitions(database_sid, codes)` |
| `load_code_definitions()` | `load_code_definitions(database_sid)` |
| `get_codes_for_column(column_name)` | `get_codes_for_column(database_sid, column_name)` |
| `delete_code_column(column_name)` | `delete_code_column(database_sid, column_name)` |
| `get_statistics()` | `get_statistics(database_sid)` |

#### 추가된 메서드

```python
def _get_db_dir(self, database_sid: str) -> Path:
    """DB별 폴더 경로"""
    db_dir = self.common_metadata_dir / database_sid
    db_dir.mkdir(exist_ok=True)
    return db_dir

def _get_common_columns_file(self, database_sid: str) -> Path:
    """DB별 공통 칼럼 파일 경로"""
    return self._get_db_dir(database_sid) / "common_columns.json"

def _get_code_definitions_file(self, database_sid: str) -> Path:
    """DB별 코드 정의 파일 경로"""
    return self._get_db_dir(database_sid) / "code_definitions.json"
```

### 2. `src/metadata_manager.py`

`integrate_metadata` 메서드에서 `database_sid` 사용:

```python
# 변경 전
common_columns = self.common_metadata_manager.load_common_columns()
code_definitions = self.common_metadata_manager.load_code_definitions()

# 변경 후
common_columns = self.common_metadata_manager.load_common_columns(database_sid)
code_definitions = self.common_metadata_manager.load_code_definitions(database_sid)
```

### 3. `src/mcp_server.py`

#### Tool 5: register_common_columns

```python
# 변경 전
async def register_common_columns(
    columns_data: str
) -> list[dict]:

# 변경 후
async def register_common_columns(
    database_sid: str,    # ← 추가
    columns_data: str
) -> list[dict]:
```

#### Tool 6: register_code_values

```python
# 변경 전
async def register_code_values(
    codes_data: str
) -> list[dict]:

# 변경 후
async def register_code_values(
    database_sid: str,    # ← 추가
    codes_data: str
) -> list[dict]:
```

#### Tool 7: view_common_metadata

```python
# 변경 전
async def view_common_metadata(
    metadata_type: str = "all"
) -> list[dict]:

# 변경 후
async def view_common_metadata(
    database_sid: str,    # ← 추가
    metadata_type: str = "all"
) -> list[dict]:
```

#### Tool 9: extract_and_integrate_metadata

```python
# 변경 후 (내부적으로 database_sid 사용)
stats = common_metadata_manager.get_statistics(database_sid)
```

### 4. `common_metadata/README.md`

전체 문서 업데이트:
- DB별 관리 개념 추가
- 폴더 구조 다이어그램 업데이트
- 모든 Tool 사용 예시에 `database_sid` 추가
- 프로세스 설명 업데이트

---

## 📊 사용 예시

### 시나리오: 2개 DB에 각각 다른 코드 체계

#### PROD_DB (운영 DB)

**공통 칼럼 등록**:
```
Tool: register_common_columns
- database_sid: "PROD_DB"
- columns_data: [
    {
      "column_name": "STATUS",
      "korean_name": "상태",
      "is_code_column": true,
      ...
    }
  ]
```

**코드 등록** (숫자 코드):
```
Tool: register_code_values
- database_sid: "PROD_DB"
- codes_data: [
    {"column_name": "STATUS", "code_value": "01", "code_label": "접수"},
    {"column_name": "STATUS", "code_value": "02", "code_label": "처리중"},
    {"column_name": "STATUS", "code_value": "03", "code_label": "완료"}
  ]
```

**저장 위치**: `common_metadata/PROD_DB/`

---

#### TEST_DB (테스트 DB)

**공통 칼럼 등록**:
```
Tool: register_common_columns
- database_sid: "TEST_DB"
- columns_data: [
    {
      "column_name": "STATUS",
      "korean_name": "상태",
      "is_code_column": true,
      ...
    }
  ]
```

**코드 등록** (문자 코드):
```
Tool: register_code_values
- database_sid: "TEST_DB"
- codes_data: [
    {"column_name": "STATUS", "code_value": "A", "code_label": "대기"},
    {"column_name": "STATUS", "code_value": "B", "code_label": "진행"},
    {"column_name": "STATUS", "code_value": "C", "code_label": "종료"}
  ]
```

**저장 위치**: `common_metadata/TEST_DB/`

---

#### 메타데이터 추출

```
# PROD_DB 메타데이터 추출
Tool: extract_and_integrate_metadata
- database_sid: "PROD_DB"
- schema_name: "SCOTT"
→ PROD_DB의 공통 메타데이터 사용 (01, 02, 03)

# TEST_DB 메타데이터 추출
Tool: extract_and_integrate_metadata
- database_sid: "TEST_DB"
- schema_name: "SCOTT"
→ TEST_DB의 공통 메타데이터 사용 (A, B, C)
```

---

## 🔄 마이그레이션 가이드

### 기존 사용자 (공통 메타데이터가 이미 등록된 경우)

**1단계**: 기존 데이터 백업
```bash
# 기존 파일이 있다면 백업
cp common_metadata/common_columns.json common_metadata/common_columns_backup.json
cp common_metadata/code_definitions.json common_metadata/code_definitions_backup.json
```

**2단계**: DB별로 재등록

각 DB마다 `register_common_columns`와 `register_code_values`를 다시 실행하되, 이번에는 `database_sid` 파라미터를 지정합니다.

**3단계**: 기존 파일 삭제
```bash
# DB별 폴더로 마이그레이션 완료 후
rm common_metadata/common_columns.json
rm common_metadata/code_definitions.json
```

### 새 사용자

처음부터 `database_sid`를 지정하여 등록하면 됩니다.

---

## 🎯 전체 워크플로우 (DB별)

```
┌─────────────────────────────────────┐
│ 1. DB 등록                          │
│    register_database_credentials    │
│    또는                              │
│    load_tnsnames + connect_database │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ 2. 공통 칼럼 등록 (DB별)            │
│    register_common_columns          │
│    (database_sid 지정)              │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ 3. 코드 정의 등록 (DB별)            │
│    register_code_values             │
│    (database_sid 지정)              │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ 4. 메타데이터 추출 (DB별)           │
│    extract_and_integrate_metadata   │
│    → 자동 매칭                       │
└─────────────────────────────────────┘
                ↓
┌─────────────────────────────────────┐
│ 5. 자연어 질의                       │
│    Stage 1: get_table_summaries     │
│    Stage 2: get_detailed_metadata   │
│    SQL 실행: execute_sql            │
└─────────────────────────────────────┘
```

---

## 💡 핵심 포인트

1. **DB별 독립성**: 각 DB는 자신만의 공통 메타데이터를 가짐
2. **충돌 방지**: DB 간 칼럼/코드 정의가 달라도 문제없음
3. **Tool 호출 시 주의**: 모든 공통 메타데이터 관련 Tool은 `database_sid` 필수
4. **자동 폴더 생성**: `database_sid`별로 폴더 자동 생성
5. **폴더 구조**: `common_metadata/{DB_SID}/common_columns.json`

---

## ✅ 체크리스트

기존 코드를 수정하는 경우:

- [ ] `register_common_columns` 호출 시 `database_sid` 추가
- [ ] `register_code_values` 호출 시 `database_sid` 추가
- [ ] `view_common_metadata` 호출 시 `database_sid` 추가
- [ ] 기존 `common_columns.json` / `code_definitions.json` 삭제
- [ ] DB별로 재등록

새로 시작하는 경우:

- [ ] 모든 공통 메타데이터 Tool에 `database_sid` 지정
- [ ] 완료!

---

**업데이트 완료 날짜**: 2025-01-06
