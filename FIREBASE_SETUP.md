# HEALTH QUEST Firebase 연결 안내

현재 앱은 Python/Streamlit 서버만 Firestore와 Storage에 접근합니다. 브라우저의 직접 접근은 `firestore.rules`와 `storage.rules`에서 전부 차단합니다.

## 로컬 Secrets

1. `.streamlit/secrets.toml.example`을 참고해 기존 `.streamlit/secrets.toml`에 `[firebase]`, `[firebase.service_account]`, `[auth]`, `[auth.google]`, `[authz]` 섹션을 추가합니다.
2. 서비스 계정 JSON 파일 자체를 저장소에 복사하지 말고, 필요한 값을 Secrets에만 옮깁니다.
3. 교사 Google 이메일 2개를 `teacher_emails`에 입력합니다.
4. 모든 값 입력 후에만 `firebase.enabled = true`로 바꿉니다.

모의상황실습의 수업자료 검색(RAG)을 사용하려면 TOML 최상단에 `OPENAI_API_KEY`와 `VECTOR_STORE_ID`(또는 `VECTOR_STORE_FILE_ID`)를 설정합니다. 로컬과 Streamlit Community Cloud의 Secrets는 별도입니다. 값이 없는 환경에서는 단원 내장 자료로 시연합니다.

## Google OIDC

Google Cloud Console에서 웹 애플리케이션 OAuth 클라이언트를 만들고 승인된 리디렉션 URI에 다음을 등록합니다.

- 로컬: `http://localhost:8503/oauth2callback`
- 학생 Google 로그인 로컬: `http://localhost:8504/oauth2callback`
- 배포: `https://<통합앱주소>.streamlit.app/oauth2callback`

OAuth 클라이언트 ID와 Secret은 `[auth.google]`에 입력합니다.

## 실행

로컬 Secrets의 `[auth]`에는 `redirect_uri = "http://localhost:{port}/oauth2callback"`를 둡니다. Streamlit은 실행 포트를 대입하므로 Google Cloud에서 8503과 8504의 실제 콜백을 각각 등록합니다. 두 버전을 동시에 실행하려면 프로젝트 폴더에서 PowerShell 창을 두 개 열고 아래 명령을 하나씩 실행합니다.

```powershell
python -m streamlit run app_firebase_codes.py --server.address localhost --server.port 8503
python -m streamlit run app_firebase_google.py --server.address localhost --server.port 8504
```

접속코드 버전은 [http://localhost:8503](http://localhost:8503), Google 버전은 [http://localhost:8504](http://localhost:8504)입니다. 두 앱은 같은 Firebase를 사용하되 로그인 방식별 기록과 모둠 편성을 각각 표시합니다. 현재 로컬 설정이 운영 Firebase를 가리킨다면 로컬에서 발급·제출한 기록도 그 Firebase에 저장됩니다. 별도 테스트 프로젝트를 쓰려면 로컬 `[firebase]`와 서비스 계정 설정을 해당 프로젝트로 지정합니다.

1. 등록 교사 Google 계정으로 로그인합니다.
2. ‘학생 접속코드 발급 및 꽃 별명 확인’에서 한 반에 최대 20명까지 발급합니다. 교사 배부 화면과 CSV는 학생 순서와 무관한 표식을 보여 줍니다. 실제 학생과 표식의 대응은 학교 내부 명부에만 기록합니다.
3. 학생에게는 비밀 접속코드만 개별 전달합니다. 학생은 로그인 후 꽃 별명을 고릅니다. 교사는 배부 표식과 별명의 연결을 확인합니다. 학생 화면과 새 학습·제출 기록에는 표식을 넣지 않습니다. ‘개인·모둠 별명 학습지 Excel 받기’와 인쇄용 학습지는 등록된 별명으로 작성됩니다.
4. 코드는 첫 발급일로부터 3년간 재사용할 수 있습니다. 재발급하면 기존 코드가 무효화되고 배부 표식, 별명, 만료일, 제출물은 유지됩니다. 브라우저 세션을 잃었을 때는 같은 코드를 다시 입력합니다.

학생들이 꽃 별명을 등록하면 교사 대시보드의 ‘모둠 편성 관리’에서 학급과 모둠 이름을 고르고 같은 반 학생 2~6명을 선택해 저장합니다. 학생의 수행평가 제출과 모의상황실습 화면에 모둠 이름과 명단이 표시됩니다. 모둠 대표 한 명이 최종 답안과 녹음을 제출하면 제출 당시 모둠원이 각자의 제출 기록에서 결과를 확인할 수 있습니다. ‘수행평가 제출’ 화면의 ‘제출 테스트용 Excel 받기’로 개인 첨부 제출을 먼저 시험할 수 있습니다.

Google 버전에서는 코드 발급 없이 학생이 Google 로그인 후 학급·학번·이름을 등록합니다. 나머지 수업과 평가 기능은 접속코드 버전과 같습니다. 편성된 모둠은 로그인 방식별로 따로 저장됩니다.

## Streamlit Community Cloud Secrets

기존 `health-quest-firebase-2026.streamlit.app` 배포의 진입점인 `app_firebase.py`는 학생 개별 접속코드와 교사 Google 로그인을 사용합니다. 이 주소를 계속 쓸 때는 현재 공개 OAuth 콜백을 유지합니다.

두 앱을 새로 배포할 때는 같은 저장소의 `deploy/health-quest-login` 브랜치를 선택하고 아래 실행 파일을 지정합니다. 하위 도메인은 예시이며, 실제로 확보한 주소를 콜백에도 동일하게 사용합니다.

| 학생 로그인 | Main file path | App URL 하위 도메인 예시 |
|---|---|---|
| 개별 접속코드 | `app_firebase_codes.py` | `health-quest-codes-2026` |
| Google 계정 | `app_firebase_google.py` | `health-quest-google-2026` |

대상 앱의 **Settings → Secrets**에서 그 앱에 저장된 설정을 확인합니다. 로컬 파일이나 다른 앱에 저장된 Secrets는 대상 앱으로 복사되지 않습니다. 같은 Firebase 프로젝트와 Google OAuth 클라이언트를 쓰는 기존 설정은 재사용할 수 있습니다.

- `[firebase]`의 활성화 설정, 프로젝트와 버킷, `[firebase.service_account]`를 확인합니다.
- 각 새 앱에서 `[auth]`의 `redirect_uri`를 `https://<앱의 실제 하위 도메인>.streamlit.app/oauth2callback`으로 설정하고, 앱마다 별도의 `cookie_secret`을 사용합니다. 같은 Google OAuth 클라이언트의 승인된 리디렉션 URI에 두 새 콜백을 추가합니다. 기존 앱에 등록된 콜백과 로컬 테스트용 콜백도 유지합니다.
- `[auth.google]`과 `[authz]`의 교사 허용 목록을 확인합니다. `app_firebase_google.py`와 `app_firebase_codes.py`는 각 실행 파일에서 학생 로그인 방식이 정해집니다.

## 규칙 배포 전 검사

```powershell
python -m unittest test_firebase_security.py test_app_integrated.py
```

Firebase CLI를 설치한 환경에서는 프로젝트 `health-quest-agent`에 `firestore.rules`와 `storage.rules`를 배포합니다. 규칙은 직접 클라이언트 접근을 전부 차단하므로, 실제 데이터 작업은 인증된 Streamlit 서버를 통해서만 수행됩니다.

Firebase CLI가 없는 환경에서는 서비스 계정 파일의 경로를 런타임 인수로만 전달하여 다음 스크립트로 동일한 규칙을 배포할 수 있습니다. 서비스 계정 파일은 저장소에 복사하거나 커밋하지 않습니다.

```powershell
python scripts/deploy_firebase_rules.py "C:\path\to\service-account.json"
```
