"""
tnsnames.ora 파일 파서
Oracle tnsnames.ora 파일을 파싱하여 DB 접속 정보 추출
"""

import re
from typing import Dict, List, Optional
from pathlib import Path


class TNSNamesParser:
    """tnsnames.ora 파일 파서"""

    def __init__(self):
        self.databases = {}

    def parse_file(self, file_path: str) -> Dict[str, Dict]:
        """
        tnsnames.ora 파일 파싱

        Args:
            file_path: tnsnames.ora 파일 경로

        Returns:
            {
                'DB_SID': {
                    'host': '192.168.1.100',
                    'port': 1521,
                    'service_name': 'ORCL',
                    'sid': None,  # SID 방식인 경우
                    'description': '설명 (주석에서 추출)'
                }
            }
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"tnsnames.ora 파일을 찾을 수 없습니다: {file_path}")

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 주석 처리된 줄은 제외하고 파싱 (단, 설명용 주석은 보존)
        self.databases = self._parse_content(content)

        return self.databases

    def _parse_content(self, content: str) -> Dict[str, Dict]:
        """tnsnames.ora 내용 파싱"""
        databases = {}

        # 줄 단위로 처리
        lines = content.split('\n')

        current_db = None
        current_block = []
        current_description = None
        in_comment_block = False

        for line in lines:
            stripped = line.strip()

            # 주석 블록 시작 (설명용)
            if stripped.startswith('#'):
                # 설명 주석 추출 (DB 이름이 아닌 일반 설명)
                if not any(char in stripped for char in ['=', '(', ')']):
                    comment_text = stripped.lstrip('#').strip()
                    if comment_text and len(comment_text) > 2:
                        current_description = comment_text
                continue

            # 빈 줄
            if not stripped:
                # 이전 블록 처리
                if current_db and current_block:
                    db_info = self._parse_description_block('\n'.join(current_block))
                    if db_info:
                        db_info['description'] = current_description or ''
                        databases[current_db] = db_info
                    current_block = []
                    current_db = None
                    current_description = None
                continue

            # DB 이름 라인 (등호 포함, 괄호 없음)
            if '=' in stripped and '(' not in stripped:
                # 이전 블록 처리
                if current_db and current_block:
                    db_info = self._parse_description_block('\n'.join(current_block))
                    if db_info:
                        db_info['description'] = current_description or ''
                        databases[current_db] = db_info
                    current_block = []

                # 새 DB 시작
                db_name = stripped.split('=')[0].strip()
                current_db = db_name
                # 등호 뒤에 바로 DESCRIPTION이 오는 경우도 처리
                if '(' in line:
                    current_block.append(line)
                continue

            # DESCRIPTION 블록
            if current_db:
                current_block.append(line)

        # 마지막 블록 처리
        if current_db and current_block:
            db_info = self._parse_description_block('\n'.join(current_block))
            if db_info:
                db_info['description'] = current_description or ''
                databases[current_db] = db_info

        return databases

    def _parse_description_block(self, block: str) -> Optional[Dict]:
        """DESCRIPTION 블록 파싱"""
        try:
            # HOST 추출
            host_match = re.search(r'HOST\s*=\s*([^\s)]+)', block, re.IGNORECASE)
            if not host_match:
                return None
            host = host_match.group(1).strip()

            # PORT 추출
            port_match = re.search(r'PORT\s*=\s*(\d+)', block, re.IGNORECASE)
            port = int(port_match.group(1)) if port_match else 1521

            # SERVICE_NAME 추출
            service_match = re.search(r'SERVICE_NAME\s*=\s*([^\s)]+)', block, re.IGNORECASE)
            service_name = service_match.group(1).strip() if service_match else None

            # SID 추출 (SERVICE_NAME이 없는 경우)
            sid_match = re.search(r'SID\s*=\s*([^\s)]+)', block, re.IGNORECASE)
            sid = sid_match.group(1).strip() if sid_match else None

            # SERVICE_NAME 또는 SID 중 하나는 있어야 함
            if not service_name and not sid:
                return None

            return {
                'host': host,
                'port': port,
                'service_name': service_name or sid,  # SERVICE_NAME 우선, 없으면 SID
                'sid': sid,
                'connection_type': 'SERVICE_NAME' if service_name else 'SID'
            }

        except Exception as e:
            # 파싱 실패 시 None 반환
            return None

    def get_database_info(self, db_sid: str) -> Optional[Dict]:
        """특정 DB 정보 조회"""
        return self.databases.get(db_sid)

    def list_databases(self) -> List[str]:
        """DB SID 목록 반환"""
        return sorted(self.databases.keys())

    def search_databases(self, keyword: str) -> List[str]:
        """키워드로 DB 검색"""
        keyword_lower = keyword.lower()
        return [
            db_sid for db_sid in self.databases.keys()
            if keyword_lower in db_sid.lower() or
               keyword_lower in self.databases[db_sid].get('description', '').lower()
        ]

    def get_databases_by_host(self, host: str) -> List[str]:
        """특정 호스트의 DB 목록"""
        return [
            db_sid for db_sid, info in self.databases.items()
            if info['host'] == host
        ]

    def export_summary(self) -> str:
        """DB 목록 요약 텍스트 생성"""
        lines = []
        lines.append(f"총 {len(self.databases)}개의 데이터베이스 연결 정보\n")

        for db_sid in sorted(self.databases.keys()):
            info = self.databases[db_sid]
            desc = info.get('description', '')
            lines.append(f"### {db_sid}")
            if desc:
                lines.append(f"  - 설명: {desc}")
            lines.append(f"  - 호스트: {info['host']}:{info['port']}")
            lines.append(f"  - 서비스명: {info['service_name']}")
            lines.append(f"  - 연결방식: {info['connection_type']}")
            lines.append("")

        return '\n'.join(lines)


if __name__ == "__main__":
    # 테스트
    parser = TNSNamesParser()
    parser.parse_file(r"D:\app\hsyou\virtual\product\12.2.0\dbhome_1\network\admin\tnsnames.ora")

    print(f"총 {len(parser.databases)}개 DB 발견")
    print("\n첫 5개:")
    for db_sid in list(parser.databases.keys())[:5]:
        info = parser.databases[db_sid]
        print(f"  {db_sid}: {info['host']}:{info['port']} ({info['service_name']})")
