# HEALTH QUEST 통합 앱 실행·배포 안내

## 통합 학습 흐름

1. `간호 미션룸`에서 단원 질문과 기초·중급·심화 미션을 완료합니다.
2. 3개 미션을 모두 제출하면 `모의상황실습 시작` 버튼이 열립니다.
3. 현재 교과목과 단원이 RAG PBL 실습실로 이어집니다.
4. 학생은 질문 2~3개를 작성하고, 모의실습 상황 3개 중 1개를 선택해 PBL 해결안을 작성합니다.

## 로컬 실행

```powershell
python -m streamlit run app_integrated.py --server.port 8503
```

접속 주소: `http://localhost:8503`

## Streamlit Community Cloud에서 세 번째 앱 만들기

- Repository: `baekkeejin0508-kee/health-tutor-week5`
- Branch: `main`
- Main file path: `app_integrated.py`
- App URL 예시: `health-quest-integrated`

Advanced settings의 Secrets에는 GitHub에 올리지 않은 다음 값을 직접 입력합니다.

```toml
OPENAI_API_KEY = ""
VECTOR_STORE_URL_ID = ""
VECTOR_STORE_FILE_ID = ""
```

API 키와 Vector Store ID는 코드, 스크린샷, 공유 문서에 기록하지 마세요.

## 저장 범위

현재 학습 상태는 브라우저 탭의 Streamlit 세션에 저장됩니다. 새로고침·서버 재시작·탭 종료 후의 영구 보존과 학생별 평가를 위해서는 Firebase 같은 별도 저장소가 필요합니다.
