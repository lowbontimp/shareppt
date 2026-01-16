# 배포 가이드

## 개요

이 가이드는 Flask 파일 공유 애플리케이션을 `example.com/share` 하위 경로로 배포하는 방법을 설명합니다.

## 사전 요구사항

- Python 3.7 이상
- Nginx 설치됨
- Systemd 사용 가능
- sudo 권한

## 배포 단계

### 1. 의존성 설치

```bash
cd /path/to/your/app
pip3 install -r requirements.txt
```

또는 시스템 전역 설치:
```bash
sudo pip3 install -r requirements.txt
```

### 2. 파일 권한 설정

```bash
cd /path/to/your/app
sudo chown -R nginx:nginx .
sudo chmod -R 755 .

# 업로드 디렉토리는 별도 위치에 있음 (app.py의 UPLOAD_FOLDER 설정에 맞춰 생성)
sudo mkdir -p /path/to/data/uploads
sudo chown -R nginx:nginx /path/to/data/uploads
sudo chmod -R 755 /path/to/data/uploads
```

### 3. Systemd 서비스 설정

```bash
# 서비스 파일 복사
sudo cp share_ppts.service /etc/systemd/system/

# 서비스 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable share_ppts
sudo systemctl start share_ppts

# 서비스 상태 확인
sudo systemctl status share_ppts
```

### 4. Nginx 설정

#### 방법 A: 기존 설정 파일에 추가

기존 nginx 설정 파일을 편집:
```bash
sudo nano /etc/nginx/sites-available/default
# 또는
sudo nano /etc/nginx/conf.d/default.conf
```

`nginx_config.conf` 파일의 내용을 server 블록에 추가합니다.

#### 방법 B: 별도 설정 파일 생성

```bash
sudo cp nginx_config.conf /etc/nginx/sites-available/share_ppts
sudo ln -s /etc/nginx/sites-available/share_ppts /etc/nginx/sites-enabled/
```

#### Nginx 설정 테스트 및 재시작

```bash
# 설정 파일 문법 검사
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 5. 방화벽 설정 (필요한 경우)

```bash
# 포트 5000은 localhost에서만 접근하므로 외부 방화벽 설정 불필요
# Nginx가 포트 80/443에서만 외부 접근 허용
```

### 6. 서비스 관리

#### 서비스 시작/중지/재시작
```bash
sudo systemctl start share_ppts
sudo systemctl stop share_ppts
sudo systemctl restart share_ppts
```

#### 로그 확인
```bash
# 서비스 로그
sudo journalctl -u share_ppts -f

# Nginx 로그
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## 접속 방법

배포 완료 후 다음 주소로 접속:
- `http://example.com/share`
- 또는 `https://example.com/share` (HTTPS 설정 시)

> **참고**: `example.com`을 실제 도메인으로 변경하세요.

## 문제 해결

### 서비스가 시작되지 않는 경우
1. 로그 확인: `sudo journalctl -u share_ppts -n 50`
2. Python 경로 확인: `which python3` 또는 `which gunicorn`
3. 파일 권한 확인: `ls -la /path/to/your/app`
4. 업로드 디렉토리 확인: `ls -la /path/to/data/uploads`

### Nginx 502 Bad Gateway 오류
1. Gunicorn 서비스가 실행 중인지 확인: `sudo systemctl status share_ppts`
2. 포트 5000이 열려있는지 확인: `sudo netstat -tlnp | grep 5000`
3. Nginx 에러 로그 확인: `sudo tail -f /var/log/nginx/error.log`

### 정적 파일이 로드되지 않는 경우
1. Nginx 설정에서 `/share/static` 프록시 설정 확인
2. Flask의 `url_for('static', ...)`가 올바른 경로 생성하는지 확인

## 파일 구조

배포 후 예상되는 구조:
```
/path/to/your/app/
├── app.py
├── models.py
├── static/
├── templates/
└── ...

/path/to/data/
├── uploads/          # 업로드된 파일 저장 위치
├── files.db          # SQLite 데이터베이스
└── secret_key.txt    # Flask 세션 키
```

> **참고**: 경로는 `app.py`와 `models.py`에서 설정한 경로에 맞춰 변경하세요.

## 보안 고려사항

1. **파일 권한**: 업로드 디렉토리는 nginx 사용자만 쓰기 가능하도록 설정
   ```bash
   sudo chmod 755 /path/to/data/uploads
   sudo chown nginx:nginx /path/to/data/uploads
   ```

2. **데이터베이스**: 데이터베이스 파일 권한 설정 (644, 읽기/쓰기만 허용)
   ```bash
   sudo chmod 644 /path/to/data/files.db
   ```

3. **보안 키**: SECRET_KEY 파일 권한 설정 (600, 소유자만 읽기/쓰기)
   ```bash
   sudo chmod 600 /path/to/data/secret_key.txt
   ```

4. **사용자 인증 파일**: `ids01.txt` 파일 권한 설정 (600, 소유자만 읽기/쓰기)
   ```bash
   sudo chmod 600 /path/to/your/app/ids01.txt
   ```

5. **로그 파일**: 민감한 정보가 로그에 기록되지 않도록 주의

6. **HTTPS**: 프로덕션 환경에서는 HTTPS 사용 권장

## 업데이트 방법

애플리케이션 업데이트 시:
```bash
cd /path/to/your/app
# 코드 수정 후
sudo systemctl restart share_ppts
```

