#!/bin/bash
# 데이터베이스 초기화 스크립트
# 모든 파일 레코드를 삭제하고 테이블을 새로 생성합니다.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "데이터베이스 초기화 중..."

# Python 스크립트 실행
python3 << 'EOF'
import sys
import os
sys.path.insert(0, os.getcwd())

try:
    from models import get_db, init_db
    
    # 기존 테이블 삭제
    print("기존 테이블 삭제 중...")
    conn = get_db()
    conn.execute('DROP TABLE IF EXISTS files')
    conn.commit()
    conn.close()
    
    # 새로 초기화
    print("새 테이블 생성 중...")
    init_db()
    
    # 확인
    conn = get_db()
    cursor = conn.execute('SELECT COUNT(*) FROM files')
    count = cursor.fetchone()[0]
    conn.close()
    
    print(f"✓ 데이터베이스 초기화 완료!")
    print(f"  현재 파일 개수: {count}")
    
except Exception as e:
    print(f"✗ 오류 발생: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "데이터베이스가 성공적으로 초기화되었습니다."
else
    echo ""
    echo "데이터베이스 초기화 중 오류가 발생했습니다."
    exit 1
fi


