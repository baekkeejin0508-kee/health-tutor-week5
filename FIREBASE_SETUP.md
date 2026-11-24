# HEALTH QUEST Firebase 연결 안내

현재 앱은 Python/Streamlit 서버만 Firestore와 Storage에 접근합니다. 브라우저의 직접 접근은 `firestore.rules`와 `storage.rules`에서 전부 차단합니다.

## 로컬 Secrets

1. `.streamlit/secrets.toml.example`을 참고해 기존 `.streamlit/secrets.toml`에 `[firebase]`, `[firebase.service_account]`, `[auth]`, `[auth.google]`, `[authz]` 섹션을 추가합니다.
2. 서비스 계정 JSON 파일 자체를 저장소에 복사하지 말고, 필요한 값을 Secrets에만 옮깁니다.
3. 교사 Google 이메일 2개를 `teacher_emails`에 입력합니다.
4. 모든 값 입력 후에만 `firebase.enabled = true`로 바꿉니다.

## Google OIDC

Google Cloud Console에서 웹 애플리케이션 OAuth 클라이언트를 만들고 승인된 리디렉션 URI에 다음을 등록합니다.

- 로컬: `http://localhost:8503/oauth2callback`
- 배포: `https://<통합앱주소>.streamlit.app/oauth2callback`

OAuth 클라이언트 ID와 Secret은 `[auth.google]`에 입력합니다.

## 실행

```powershell
python -m streamlit run app_firebase.py --server.port 8503
```

## 규칙 배포 전 검사

```powershell
python -m unittest test_firebase_security.py test_app_integrated.py
```

Firebase CLI를 설치한 환경에서는 프로젝트 `health-quest-agent`에 `firestore.rules`와 `storage.rules`를 배포합니다. 규칙은 직접 클라이언트 접근을 전부 차단하므로, 실제 데이터 작업은 인증된 Streamlit 서버를 통해서만 수행됩니다.
