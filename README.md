# 파일 공유 웹페이지

5명 정도의 사용자가 파일을 업로드하고 공유할 수 있는 웹 애플리케이션입니다.

## 주요 기능

- 파일 업로드 (비밀번호 설정)
- 파일 다운로드
- 업로드한 사람만 삭제 가능 (비밀번호 인증)
- 2주 후 자동 삭제

## 설치 방법

1. Python 3.7 이상이 설치되어 있어야 합니다.

2. 의존성 패키지 설치:
```bash
pip install -r requirements.txt
```

3. 설정 파일 생성:
   - `secret_key.txt`: Flask 세션 키 파일 생성 (아래 "설정 파일 생성" 섹션 참조)
   - `ids01.txt`: 사용자 인증 정보 파일 생성 (아래 "설정 파일 생성" 섹션 참조)

## 실행 방법

```bash
python app.py
```

서버가 시작되면 브라우저에서 `http://localhost:5000`으로 접속하세요.

## 사용 방법

1. **파일 업로드**
   - 파일 선택 후 삭제 비밀번호를 입력하고 업로드 버튼을 클릭합니다.
   - 비밀번호는 파일 삭제 시 필요합니다.

2. **파일 다운로드**
   - 업로드된 파일 목록에서 다운로드 버튼을 클릭합니다.

3. **파일 삭제**
   - 삭제 버튼을 클릭하고 업로드 시 설정한 비밀번호를 입력합니다.
   - 비밀번호가 일치하면 파일이 삭제됩니다.

4. **자동 삭제**
   - 업로드 후 14일이 지나면 자동으로 삭제됩니다.
   - 백그라운드 작업이 매 시간마다 확인합니다.

## 기술 스택

- Backend: Python Flask
- Database: SQLite
- Frontend: HTML, CSS, JavaScript
- Scheduler: APScheduler

## 파일 구조

```
프로젝트 루트/
├── app.py                 # Flask 메인 애플리케이션
├── models.py              # 데이터베이스 모델
├── requirements.txt       # Python 의존성
├── templates/
│   └── index.html         # 메인 페이지
└── static/
    ├── css/
    │   └── style.css      # 스타일시트
    └── js/
        └── main.js        # 클라이언트 사이드 스크립트

데이터 디렉토리/ (app.py에서 설정한 경로)
├── uploads/               # 업로드된 파일 저장 디렉토리
├── files.db               # SQLite 데이터베이스
└── secret_key.txt         # Flask 세션 키
```

## 설정 파일 생성

애플리케이션을 실행하기 전에 다음 설정 파일들을 생성해야 합니다.

### 1. secret_key.txt 생성

Flask 세션 암호화를 위한 SECRET_KEY를 생성합니다. 다음 방법 중 하나를 사용하세요:

**방법 1: Python으로 생성**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))" > secret_key.txt
```

**방법 2: Python 스크립트로 생성**
```python
import secrets
secret_key = secrets.token_hex(32)
with open('secret_key.txt', 'w') as f:
    f.write(secret_key)
print(f"Secret key generated: {secret_key}")
```

**방법 3: 환경 변수 사용**
`secret_key.txt` 파일 대신 환경 변수로 설정할 수도 있습니다:
```bash
export SECRET_KEY="your-secret-key-here"
```

> **참고**: `app.py`는 먼저 환경 변수 `SECRET_KEY`를 확인하고, 없으면 `secret_key.txt` 파일을 읽습니다. 파일도 없으면 자동으로 생성합니다.

### 2. ids01.txt 생성

사용자 인증 정보를 저장하는 파일입니다. 각 줄에 이메일과 비밀번호를 공백으로 구분하여 작성합니다.

**파일 형식:**
```
이메일1 비밀번호1
이메일2 비밀번호2
이메일3 비밀번호3
```

**예시:**
```
user1@example.com mypassword123
user2@example.com securepass456
admin@example.com adminpass789
```

**생성 방법:**
```bash
cat > ids01.txt << EOF
user1@example.com mypassword123
user2@example.com securepass456
admin@example.com adminpass789
EOF
```

또는 텍스트 에디터로 직접 생성:
```bash
nano ids01.txt
# 또는
vim ids01.txt
```

> **보안 주의사항**: 
> - `ids01.txt` 파일에는 평문 비밀번호가 저장되지만, 애플리케이션 내부에서 bcrypt로 해시화되어 사용됩니다.
> - 이 파일은 절대 Git에 커밋하지 마세요 (`.gitignore`에 포함되어 있습니다).
> - 파일 권한을 제한하세요: `chmod 600 ids01.txt`

## 보안 기능

- 비밀번호는 bcrypt로 해시화하여 저장
- 파일명 정규화 (경로 탐색 공격 방지)
- 최대 파일 크기 제한 (10GB)
- CSRF 보호 (Flask-WTF)
- 세션 쿠키 보안 설정

