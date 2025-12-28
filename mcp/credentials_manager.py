"""
DB 접속 정보 암호화 관리 모듈
"""

import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Dict
import logging
import traceback

logger = logging.getLogger(__name__)


class CredentialsManager:
    """DB 접속 정보 암호화 저장 및 로드"""

    def __init__(self, credentials_dir: str = "./credentials"):
        """
        Args:
            credentials_dir: 접속 정보 저장 디렉토리
        """
        self.credentials_dir = Path(credentials_dir)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # 환경 변수에서 암호화 키 로드
        encryption_key = os.getenv('ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("ENCRYPTION_KEY 환경 변수가 설정되지 않았습니다.")

        self.cipher = Fernet(encryption_key.encode())

        logger.info(f"CredentialsManager 초기화: {self.credentials_dir}")

    def save_credentials(self, database_sid: str, credentials: Dict) -> bool:
        """
        DB 접속 정보 암호화하여 저장

        Args:
            database_sid: 데이터베이스 SID
            credentials: 접속 정보
                - host: str
                - port: int
                - service_name: str
                - user: str
                - password: str

        Returns:
            성공 여부
        """
        try:
            # JSON으로 변환
            credentials_json = json.dumps(credentials)

            # 암호화
            encrypted_data = self.cipher.encrypt(credentials_json.encode())

            # 파일로 저장
            file_path = self.credentials_dir / f"{database_sid}.json.enc"
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)

            logger.info(f"✅ 접속 정보 저장: {database_sid}")
            return True

        except Exception as e:
            logger.error(f"❌ 접속 정보 저장 실패: {e}\n{traceback.format_exc()}")
            return False

    def load_credentials(self, database_sid: str) -> Dict:
        """
        DB 접속 정보 로드 및 복호화

        Args:
            database_sid: 데이터베이스 SID

        Returns:
            접속 정보 딕셔너리

        Raises:
            FileNotFoundError: 접속 정보 파일이 없을 때
            Exception: 복호화 실패 시
        """
        file_path = self.credentials_dir / f"{database_sid}.json.enc"

        if not file_path.exists():
            raise FileNotFoundError(f"접속 정보가 없습니다: {database_sid}")

        try:
            # 파일 읽기
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()

            # 복호화
            decrypted_data = self.cipher.decrypt(encrypted_data)

            # JSON 파싱
            credentials = json.loads(decrypted_data.decode())

            logger.info(f"✅ 접속 정보 로드: {database_sid}")
            return credentials

        except Exception as e:
            logger.error(f"❌ 접속 정보 로드 실패: {e}\n{traceback.format_exc()}")
            raise

    def delete_credentials(self, database_sid: str) -> bool:
        """접속 정보 삭제"""
        file_path = self.credentials_dir / f"{database_sid}.json.enc"

        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"✅ 접속 정보 삭제: {database_sid}")
                return True
            else:
                logger.warning(f"접속 정보 파일이 없습니다: {database_sid}")
                return False

        except Exception as e:
            logger.error(f"❌ 접속 정보 삭제 실패: {e}\n{traceback.format_exc()}")
            return False

    def list_databases(self) -> list:
        """저장된 모든 DB SID 목록"""
        databases = []

        for file_path in self.credentials_dir.glob("*.json.enc"):
            database_sid = file_path.stem.replace('.json', '')
            databases.append(database_sid)

        return sorted(databases)


def generate_encryption_key() -> str:
    """새로운 암호화 키 생성"""
    key = Fernet.generate_key()
    return key.decode()


if __name__ == "__main__":
    # 암호화 키 생성 예시
    print("새로운 암호화 키:")
    print(generate_encryption_key())
    print("\n이 키를 .env 파일의 ENCRYPTION_KEY에 설정하세요.")
