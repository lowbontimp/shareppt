#!/bin/bash

CURRENT_USER="hbim"
NGINX_USER="nginx"

echo "파일 소유권을 $CURRENT_USER로 변경 중..."

# 현재 디렉토리의 모든 파일과 디렉토리 소유권 변경
sudo chown -R $CURRENT_USER:$CURRENT_USER .

# uploads 디렉토리는 별도 위치에 있으므로 nginx 소유권 유지
#sudo chown -R $NGINX_USER:$NGINX_USER /home/hbim/hdd1/share_ppts/uploads

echo "완료: 모든 파일의 소유권이 $CURRENT_USER로 변경되었습니다."
echo "이제 파일을 편집할 수 있습니다."
