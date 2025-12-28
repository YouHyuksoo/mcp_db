#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backend 실행 스크립트
Oracle NL-SQL MCP Server Backend
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Backend 서버 실행"""
    print("=" * 40)
    print("Oracle NL-SQL Backend Server 시작")
    print("=" * 40)
    
    # 현재 스크립트의 디렉토리로 이동
    script_dir = Path(__file__).parent.absolute()
    os.chdir(script_dir)
    print(f"현재 경로: {os.getcwd()}")
    
    # 가상환경 확인
    venv_python = script_dir / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        print(f"[오류] 가상환경을 찾을 수 없습니다: {venv_python}")
        print("가상환경을 먼저 생성해주세요: python -m venv venv")
        input("계속하려면 Enter를 누르세요...")
        sys.exit(1)
    
    print(f"가상환경 Python 사용: {venv_python}")
    
    # Backend 디렉토리 확인
    backend_dir = script_dir / "backend"
    if not backend_dir.exists():
        print(f"[오류] backend 디렉토리를 찾을 수 없습니다: {backend_dir}")
        input("계속하려면 Enter를 누르세요...")
        sys.exit(1)
    
    # Backend 서버 시작
    print()
    print("Backend 서버를 시작합니다...")
    print("API 문서: http://localhost:8000/api/docs")
    print("Web UI: http://localhost:3000")
    print()
    print("종료하려면 Ctrl+C를 누르세요.")
    print()
    
    # uvicorn 실행
    try:
        os.chdir(backend_dir)
        subprocess.run([
            str(venv_python),
            "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ], check=True)
    except KeyboardInterrupt:
        print("\n서버를 종료합니다...")
    except subprocess.CalledProcessError as e:
        print(f"\n[오류] 서버 실행 중 오류 발생: {e}")
        input("계속하려면 Enter를 누르세요...")
        sys.exit(1)

if __name__ == "__main__":
    main()

