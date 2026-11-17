# HEALTH QUEST 앱 분리 및 배포 안내

## 두 앱의 역할

| 구분 | 진입 파일 | 학습 방식 | 권장 배포 이름 |
| --- | --- | --- | --- |
| 기존 간호 미션룸 | `app.py` | 교사가 설계한 단원별 기초·중급·심화 미션과 팀 협력 | `health-tutor-week5-20261010` 유지 |
| 새 RAG PBL 실습실 | `app_rag_pbl.py` | 학생 질문 2~3개 분석 → RAG 기반 상황 3개 생성 → 1개 선택 → 서술형 PBL 해결과 재도전 | 예: `health-quest-rag-pbl` |

두 앱은 같은 저장소를 사용해도 진입 파일과 Streamlit 세션이 서로 다르다. 새 앱을 배포해도 기존 `app.py`의 화면과 학습 기록 로직은 변경되지 않는다.

## 새 앱의 실제 학습 흐름

1. 학생이 교과목과 단원을 선택한다.
2. 의학·간호·의학용어 질문 2~3개와 현재 알고 있는 내용을 자기 말로 작성한다.
3. 단일 AI 보건튜터가 교과서 PDF와 공공기관·병원 Vector Store를 함께 검색한다.
4. 질문의 개념 연결과 근거 표현을 바탕으로 기초·발전·심화의 학습 출발점을 제시한다.
5. 서로 다른 가상 병원 모의실습 상황 A·B·C를 생성한다.
6. 학생이 한 상황을 선택하고 문제 정의, 가설, 해결안, 근거, 평가·성찰을 서술한다.
7. 같은 단일 에이전트가 RAG 근거로 강점과 놓친 단서, 수정 질문을 제공한다.
8. 학생은 재도전한 뒤 Excel 학습기록을 내려받아 교사에게 제출한다.

## Streamlit Community Cloud에 새 주소로 배포

1. 현재 저장소의 변경사항을 검토한 뒤 GitHub에 커밋하고 푸시한다.
2. Streamlit Community Cloud에서 `Create app`을 선택한다.
3. 기존 앱과 같은 저장소·브랜치를 선택한다.
4. Main file path만 `app_rag_pbl.py`로 지정한다.
5. 새 앱 이름을 기존 앱과 다르게 지정한다. 이 이름이 새 배포 URL에 사용된다.
6. 새 앱의 Secrets에 아래 값을 등록한다.

```toml
OPENAI_API_KEY = "..."
VECTOR_STORE_FILE_ID = "vs_..."
VECTOR_STORE_URL_ID = "vs_..."
RAG_PBL_MODEL = "gpt-4.1-mini"
```

`VECTOR_STORE_ID`는 이전 버전과의 호환을 위한 대체값이다. 새 앱에서는 `VECTOR_STORE_FILE_ID`와 `VECTOR_STORE_URL_ID`를 모두 등록해야 교과서와 공공자료를 동시에 검색한다.

## 로컬 실행

기존 앱:

```powershell
python -m streamlit run app.py --server.port 8501
```

새 RAG PBL 앱:

```powershell
python -m streamlit run app_rag_pbl.py --server.port 8502
```

브라우저에서 `http://localhost:8502`로 접속하면 기존 앱과 동시에 비교할 수 있다.

## 현재 저장 범위

새 앱의 입력과 피드백은 현재 브라우저 세션에만 유지된다. Excel 다운로드는 가능하지만 자동으로 교사에게 전송되지는 않는다. 실제 학생별·모둠별 평가 시스템으로 운영하려면 Firebase 로그인, Firestore 영속 저장, 교사 권한과 제출함을 다음 단계에서 연결해야 한다.
