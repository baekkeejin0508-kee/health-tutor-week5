"""지정한 웹 URL의 정적 본문을 수집하여 OpenAI Vector Store에 등록하는 RAG 지식 구축 스크립트.
교수님 [6-1. RAG-URL로 데이터 가져오기] 교안 준수.
"""
import os
import sys
import hashlib
from pathlib import Path
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Windows 콘솔 유니코드 이모지 인코딩 지원
if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr:
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# -------------------------------------------------------------
# 1. 수집할 웹페이지 URL 목록
#    (고등학교 간호과정 30대 핵심 질환 + 질병관리청 & 상급종합병원 임상 가이드라인)
# -------------------------------------------------------------
URLS = [
    # -------------------------------------------------------------
    # [A. 교육학 & 보건 기초] 교사 AI 역량 및 간호학 기초 (4종)
    # -------------------------------------------------------------
    # 1. 유네스코 AI 교사 역량 프레임워크 (교수님 공통 지침 URL)
    "https://www.unesco.org/en/articles/ai-competency-framework-teachers",
    # 2. 비뇨계 (인체 해부생리 기초)
    "https://ko.wikipedia.org/wiki/%EB%B9%84%EB%87%A8%EA%B3%84",
    # 3. 간호학 개론 (기본간호 및 간호과정 원론)
    "https://ko.wikipedia.org/wiki/%EA%B0%84%ED%98%B8",
    # 4. 응급처치 (학교보건 및 일상 응급 대처 원칙)
    "https://ko.wikipedia.org/wiki/%EC%9D%91%EA%B8%89%EC%B2%98%EC%B9%98",

    # -------------------------------------------------------------
    # [B. 질병관리청 & 상급종합병원 임상 가이드라인] (8종)
    # -------------------------------------------------------------
    # 5. 질병관리청 국가건강정보포털 - 연조직염(봉와직염)
    "https://health.kdca.go.kr/healthinfo/biz/health/gnrlzHealthInfo/gnrlzHealthInfo/gnrlzHealthInfoView.do?cntnts_sn=5238",
    # 6. 서울아산병원 질환백과 - 봉와직염(Cellulitis)
    "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=31537",
    # 7. 서울대학교병원 N의학정보 - 봉와직염(Cellulitis)
    "https://www.snuh.org/health/nMedInfo/nView.do?category=DIS&medid=AA000217",
    # 8. 서울아산병원 질환백과 - 당뇨병(Diabetes)
    "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=31596",
    # 9. 서울아산병원 질환백과 - 본태성 고혈압(Hypertension)
    "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=31322",
    # 10. 서울아산병원 질환백과 - 욕창(Pressure Sore)
    "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=31557",
    # 11. 서울아산병원 질환백과 - 기관지 천식(Asthma)
    "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=31811",
    # 12. 서울아산병원 질환백과 - 급성 심근경색증(AMI)
    "https://www.amc.seoul.kr/asan/healthinfo/disease/diseaseDetail.do?contentId=32111",

    # -------------------------------------------------------------
    # [C. 고등학교 간호과정 30대 핵심 질환 - 성인·기본·응급간호] (30종)
    # -------------------------------------------------------------
    # [1. 감염 및 피부 간호 (4종)]
    # 13. 연조직염 / 봉와직염
    "https://ko.wikipedia.org/wiki/%EC%97%B0%EC%A1%B0%EC%A7%81%EC%97%BC",
    # 14. 욕창 (단계별 사정 및 체위변경)
    "https://ko.wikipedia.org/wiki/%EC%9A%95%EC%B0%BD",
    # 15. 대상포진 (수포 관리 및 신경통)
    "https://ko.wikipedia.org/wiki/%EB%8C%80%EC%83%81%ED%8F%AC%EC%A7%84",
    # 16. 옴 / 옴진드기 감염 (격리 및 접촉주의)
    "https://ko.wikipedia.org/wiki/%EC%98%B4_(%EC%A7%88%EB%B3%91)",

    # [2. 순환기 및 대사 간호 (5종)]
    # 17. 고혈압 (혈압 측정 및 생활습관)
    "https://ko.wikipedia.org/wiki/%EA%B3%A0%ED%98%88%EC%95%95",
    # 18. 당뇨병 (혈당 사정 및 인슐린 요법)
    "https://ko.wikipedia.org/wiki/%EB%8B%B9%EB%87%A8%EB%B3%91",
    # 19. 저혈당증 (저혈당 쇼크 및 응급 당분 섭취)
    "https://ko.wikipedia.org/wiki/%EC%A0%80%ED%98%88%EB%8B%B9%EC%A6%9D",
    # 20. 협심증 (니트로글리세린 설하투여 및 흉통 사정)
    "https://ko.wikipedia.org/wiki/%ED%98%91%EC%8B%AC%EC%A6%9D",
    # 21. 급성 심근경색증 (심전도 및 산소요법)
    "https://ko.wikipedia.org/wiki/%EC%8B%AC%EA%B7%BC%EA%B2%BD%EC%83%89",

    # [3. 호흡기 간호 (5종)]
    # 22. 기관지 천식 (흡입제 사용 및 천명음 사정)
    "https://ko.wikipedia.org/wiki/%EC%B2%9C%EC%8B%9D",
    # 23. 폐렴 (객담 배출 및 호흡음 청진)
    "https://ko.wikipedia.org/wiki/%ED%8F%90%EB%A0%B4",
    # 24. 만성 폐쇄성 폐질환 (COPD, 입술오므리기 호흡)
    "https://ko.wikipedia.org/wiki/%EB%A7%8C%EC%84%B1_%ED%8F%90%EC%87%84%EC%84%B1_%ED%8F%90%EC%A7%88%ED%99%98",
    # 25. 결핵 (음압격리 및 공기주의 간호)
    "https://ko.wikipedia.org/wiki/%EA%B2%B0%ED%95%B5",
    # 26. 기흉 (밀봉흉곽유도 및 호흡곤란 관찰)
    "https://ko.wikipedia.org/wiki/%EA%B8%B0%ED%9D%89",

    # [4. 소화기 및 배설 간호 (5종)]
    # 27. 위염 및 위궤양 (식이지도 및 흑색변 사정)
    "https://ko.wikipedia.org/wiki/%EC%9C%84%EC%97%BC",
    # 28. 급성 충수염 (반발압통 및 맥버니점 사정)
    "https://ko.wikipedia.org/wiki/%EC%B6%A9%EC%88%98%EC%97%BC",
    # 29. 간경변증 (복수, 황달, 간성혼수 사정)
    "https://ko.wikipedia.org/wiki/%EA%B0%84%EA%B2%BD%EB%B3%80",
    # 30. 요로감염증 (단순 도뇨 및 배뇨통 간호)
    "https://ko.wikipedia.org/wiki/%EC%9A%94%EB%A1%9C%EA%B0%90%EC%97%BC%EC%A6%9D",
    # 31. 급성 신부전 (소변량 모니터링 및 전해질 관리)
    "https://ko.wikipedia.org/wiki/%EA%B8%89%EC%84%B1_%EC%8B%A0%EB%B6%80%EC%A0%84",

    # [5. 신경 및 뇌혈관 간호 (4종)]
    # 32. 뇌졸중 / 뇌경색 (FAST 평가 및 마비 간호)
    "https://ko.wikipedia.org/wiki/%EB%87%8C%EC%A1%B8%EC%A4%91",
    # 33. 뇌출혈 (두개내압 상승 징후 관찰)
    "https://ko.wikipedia.org/wiki/%EB%87%8C%EC%B6%9C%ED%98%88",
    # 34. 파킨슨병 (낙상 예방 및 진전 간호)
    "https://ko.wikipedia.org/wiki/%ED%8C%8C%ED%82%A8%EC%8A%A8%EB%B3%91",
    # 35. 치매 (지남력 유지 및 안전 환경)
    "https://ko.wikipedia.org/wiki/%EC%B9%98%EB%A7%A4",

    # [6. 근골격 및 수술 전후 간호 (3종)]
    # 36. 골절 (석고붕대, 견인간호, 낙상주의)
    "https://ko.wikipedia.org/wiki/%EA%B3%A8%EC%A0%88",
    # 37. 골관절염 (퇴행성 관절염, 관절 가동범위 운동)
    "https://ko.wikipedia.org/wiki/%EA%B3%A8%EA%B4%80%EC%A0%88%EC%97%BC",
    # 38. 심부정맥 혈전증 (DVT, 탄력스타킹 및 조기이상)
    "https://ko.wikipedia.org/wiki/%EC%8B%AC%EB%B6%80%EC%A0%95%EB%A7%A5_%ED%98%88%EC%A0%84%EC%A6%9D",

    # [7. 응급 및 환경 손상 간호 (4종)]
    # 39. 아나필락시스 (에피네프린 투여 및 기도확보)
    "https://ko.wikipedia.org/wiki/%EC%95%84%EB%82%98%ED%95%84%EB%9D%BD%EC%8B%9C%EC%8A%A4",
    # 40. 열사병 (체온하강법 및 수액 공급)
    "https://ko.wikipedia.org/wiki/%EC%97%B4%EC%82%AC%EB%B3%91",
    # 41. 화상 (9의 법칙, 감염관리, 수액요법)
    "https://ko.wikipedia.org/wiki/%ED%99%94%EC%83%81",
    # 42. 심폐소생술 (CPR & 제세동기 AED 사용법)
    "https://ko.wikipedia.org/wiki/%EC%8B%AC%ED%8F%90%EC%86%8C%EC%83%9D%EC%88%A0",
]

OUT_DIR = Path("knowledge_web")


def extract_page(url: str) -> str:
    """웹페이지를 요청하고 불필요한 태그를 제거한 순수 본문 텍스트를 추출합니다."""
    import urllib.parse
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("https", "http") or not parsed.netloc:
        raise ValueError(f"올바른 HTTP(S) URL이 아닙니다: {url}")

    safe_path = urllib.parse.quote(urllib.parse.unquote(parsed.path))
    safe_query = urllib.parse.quote(urllib.parse.unquote(parsed.query), safe="=&?+")
    safe_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, safe_path, safe_query, parsed.fragment))

    import urllib3
    urllib3.disable_warnings()

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) EducationRAGDemo/1.0"}
    response = requests.get(safe_url, timeout=20, headers=headers, verify=False)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type:
        raise ValueError(f"HTML 페이지가 아닙니다 (Content-Type: {content_type}).")

    soup = BeautifulSoup(response.text, "html.parser")
    # 네비게이션, 푸터, 스크립트, 스타일 등 잡음 요소 제거
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    # 전자정부 포털 등은 본문이 <form> 내부에 감싸져 있으므로 decompose 대신 unwrap 처리
    for form in soup.find_all("form"):
        form.unwrap()

    # 본문 영역 탐색 우선순위 (질병관리청, 서울아산병원, 서울대병원, 위키백과 등 지원)
    root = (
        soup.find("div", class_="data-content")
        or soup.find("div", id="sub-content")
        or soup.find("div", class_="contents-wrap")
        or soup.find("main")
        or soup.find("article")
        or soup.find("div", id="content")
        or soup.find("div", class_="subContent")
        or soup.body
        or soup
    )
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    lines = [x.strip() for x in root.get_text("\n", strip=True).splitlines()]
    body = "\n".join(x for x in lines if x)

    if len(body) < 200:
        raise ValueError(f"추출된 본문이 너무 짧습니다 ({len(body)}자). 동적 페이지 또는 접근 제한 여부를 확인하세요.")

    return f"제목: {title}\n출처 URL: {url}\n\n{body}\n"


def load_openai_key():
    """환경변수 또는 .streamlit/secrets.toml에서 API Key를 로드합니다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        secrets_path = Path(".streamlit/secrets.toml")
        if secrets_path.exists():
            import tomllib
            with open(secrets_path, "rb") as f:
                secrets = tomllib.load(f)
                api_key = secrets.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다. .streamlit/secrets.toml을 확인하세요.")
    return api_key


def update_secrets_with_vector_store(vs_id: str):
    """secrets.toml 파일에 새로 생성된 VECTOR_STORE_URL_ID 및 기본 VECTOR_STORE_ID를 등록합니다."""
    secrets_path = Path(".streamlit/secrets.toml")
    lines = []
    if secrets_path.exists():
        lines = secrets_path.read_text(encoding="utf-8").splitlines()

    new_lines = []
    has_vs = False
    has_vs_url = False

    for line in lines:
        if line.startswith("VECTOR_STORE_URL_ID"):
            new_lines.append(f'VECTOR_STORE_URL_ID = "{vs_id}"')
            has_vs_url = True
        elif line.startswith("VECTOR_STORE_ID"):
            new_lines.append(f'VECTOR_STORE_ID = "{vs_id}"')
            has_vs = True
        else:
            new_lines.append(line)

    if not has_vs_url:
        new_lines.append(f'VECTOR_STORE_URL_ID = "{vs_id}"')
    if not has_vs:
        new_lines.append(f'VECTOR_STORE_ID = "{vs_id}"')

    secrets_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"✅ .streamlit/secrets.toml 에 VECTOR_STORE_ID = '{vs_id}' 등록 완료")


def main():
    api_key = load_openai_key()
    client = OpenAI(api_key=api_key)

    OUT_DIR.mkdir(exist_ok=True)
    paths = []

    print("===============================================================")
    print("🌐 [6-1. RAG-URL로 데이터 가져오기] 웹페이지 수집 시작")
    print("===============================================================")

    for url in URLS:
        try:
            print(f">> 수집 중: {url}")
            text = extract_page(url)
            file_name = hashlib.sha256(url.encode()).hexdigest()[:12] + ".txt"
            path = OUT_DIR / file_name
            path.write_text(text, encoding="utf-8")
            paths.append(path)
            print(f"   ✓ 수집 완료: {path.name} ({len(text):,}자)")
        except Exception as exc:
            print(f"   ✗ 수집 실패: {url} - {exc}")

    if not paths:
        raise RuntimeError("수집된 웹페이지가 없습니다. URL과 네트워크 상태를 확인하세요.")

    print(f"\n총 {len(paths)}개 웹페이지 텍스트 추출 완료. OpenAI Vector Store 등록 시작...")

    store = client.vector_stores.create(name="High School Nursing 30 Core Diseases Web Knowledge (6-1 URL RAG)")
    print(f"생성된 Vector Store ID: {store.id}")

    streams = [p.open("rb") for p in paths]
    try:
        batch = client.vector_stores.file_batches.upload_and_poll(
            vector_store_id=store.id,
            files=streams
        )
    finally:
        for s in streams:
            s.close()

    print(f"인덱싱 상태: {batch.status}")
    print(f"처리 파일 현황: {batch.file_counts}")

    if batch.status != "completed":
        raise RuntimeError(f"인덱싱이 완료되지 않았습니다. 상태: {batch.status}")

    update_secrets_with_vector_store(store.id)
    print("\n🎉 URL RAG Knowledge 구축 성공!")


if __name__ == "__main__":
    main()
