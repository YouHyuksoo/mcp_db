@echo off
REM Backend 실행 스크립트
REM Oracle NL-SQL MCP Server Backend

echo ========================================
echo Oracle NL-SQL Backend Server 시작
echo ========================================

REM 현재 디렉토리 확인
cd /d "%~dp0"
echo 현재 경로: %CD%

REM 가상환경 활성화
if exist "venv\Scripts\activate.bat" (
    echo 가상환경 활성화 중...
    call venv\Scripts\activate.bat
) else (
    echo [오류] 가상환경을 찾을 수 없습니다: venv\Scripts\activate.bat
    pause
    exit /b 1
)

REM Backend 디렉토리로 이동
if exist "backend" (
    cd backend
    echo Backend 디렉토리로 이동: %CD%
) else (
    echo [오류] backend 디렉토리를 찾을 수 없습니다.
    pause
    exit /b 1
)

REM Backend 서버 시작
echo.
echo Backend 서버를 시작합니다...
echo API 문서: http://localhost:8000/api/docs
echo Web UI: http://localhost:3000
echo.
echo 종료하려면 Ctrl+C를 누르세요.
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

