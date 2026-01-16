#!/bin/bash
# 배포를 위해 파일 소유권을 nginx로 변경

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

NGINX_USER="nginx"

echo "파일 소유권을 $NGINX_USER로 변경 중..."

# 현재 디렉토리의 모든 파일과 디렉토리 소유권 변경
sudo chown -R $NGINX_USER:$NGINX_USER .

# uploads 디렉토리도 nginx 소유권으로 설정
sudo chown -R $NGINX_USER:$NGINX_USER /home/hbim/share_ppts/uploads

echo "완료: 모든 파일의 소유권이 $NGINX_USER로 변경되었습니다."
echo "배포 준비가 완료되었습니다."

sudo systemctl restart share_ppts
