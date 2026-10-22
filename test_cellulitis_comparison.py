import asyncio
import os
import sys
import json
from pathlib import Path
from tutor import build_agent, new_session, run_turn, reply_to_markdown
from agents import FileSearchTool

sys.stdout.reconfigure(encoding="utf-8")

SECRETS_FILE = Path(".streamlit/secrets.toml")
if SECRETS_FILE.exists():
    with open(SECRETS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("OPENAI_API_KEY") and "=" in line:
                k = line.split("=", 1)[1].strip().strip('"').strip("'")
                if k:
                    os.environ["OPENAI_API_KEY"] = k
            elif line.startswith("VECTOR_STORE_URL_ID") and "=" in line:
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    os.environ["VECTOR_STORE_URL_ID"] = v
            elif line.startswith("VECTOR_STORE_FILE_ID") and "=" in line:
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if v:
                    os.environ["VECTOR_STORE_FILE_ID"] = v

URL_STORE_ID = os.environ.get("VECTOR_STORE_URL_ID", "vs_6ad8458c601c8191b96326fa84a89fdd")
FILE_STORE_ID = os.environ.get("VECTOR_STORE_FILE_ID", "vs_6ad59e8eae9081919a57db129940e045")

async def test_cellulitis_mode(mode_name: str, vs_id: str = None):
    print(f"\n=======================================================")
    print(f"🔬 [{mode_name}] 봉와직염 다회차 테스트 시작 (VS_ID: {vs_id})")
    print(f"=======================================================")
    
    tools = [FileSearchTool(vector_store_ids=[vs_id], max_num_results=3)] if vs_id else []
    agent = build_agent(model="gpt-4.1-mini", version="v2", tools=tools)
    session = new_session()

    # Step 1: 초기 발화 (봉와직염 개념 탐색)
    p1 = "봉와직염 환자 간호하는 모의상황 사례 만들기"
    print(f"\n[Turn 1 입력]: {p1}")
    r1, _ = await run_turn(agent, p1, session)
    print(f"-> 결과 단계: {r1.stage}")
    print(f"-> 설명 요약:\n{r1.support.explanation[:200]}...")

    # Step 2: 학생의 개념설명 + 탐구질문 + 상황초안 입력 (사례후보 유도)
    p2 = (
        "봉와직염은 피부 진피와 피하 조직에 세균이 침범해 발생하는 급성 화농성 염증으로, "
        "환부에 발적, 부종, 열감, 심한 통증이 나타나고 오한이나 발열 같은 전신 증상이 동반될 수 있어요. "
        "탐구질문: '다리에 봉와직염이 발생한 고령 환자의 염증 확산을 막고 통증을 완화하기 위해 어떤 간호 우선순위를 적용해야 할까?' "
        "상황초안: 오른쪽 하지에 발적과 열감이 심해 입원한 60대 봉와직염 환자에게 환부 거상과 냉/온요법, 항생제 투약 관찰을 수행하는 상황이야."
    )
    print(f"\n[Turn 2 입력]: 개념 설명 + 탐구질문 + 상황초안")
    r2, _ = await run_turn(agent, p2, session)
    print(f"-> 결과 단계: {r2.stage} (후보 카드 수: {len(r2.support.candidates)})")
    for c in r2.support.candidates:
        print(f"   * [{c.id}] {c.title}: {c.situation}")

    # Step 3: 학생이 1개 사례 선택 (사례 A 선택)
    p3 = "가상 사례 A가 내가 의도한 상황과 가장 맞아. A를 선택할게."
    print(f"\n[Turn 3 입력]: 사례 A 선택")
    r3, _ = await run_turn(agent, p3, session)
    print(f"-> 결과 단계: {r3.stage}")
    print(f"-> 심도 확장 질문:\n{r3.support.explanation}")

    # Step 4: 학생의 3대 심도 답변 (선택이유, 우선순위, 평가방법)
    p4 = (
        "사례 A를 선택한 이유는 하지 봉와직염 환자에서 부종과 통증 완화, 염증 확산 방지가 가장 시급한 간호 문제이기 때문이야. "
        "간호 우선순위 1순위는 환부를 심장보다 높게 올려주는 환부 거상(elevation)과 발적 부위 경계선 표시(pen marking)를 통한 병변 진행 관찰이고, "
        "2순위는 처방된 정맥 항생제 투약 전 알레르기 반응 확인 및 투약 부작용 관찰이야. "
        "평가방법은 발적 부위가 경계선 밖으로 번지지 않는지, 환부 둘레와 통증 NRS 점수가 감소하는지, 체온이 정상 범위로 유지되는지 측정할 거야. "
        "이제 최종 병원 임상 PBL 모의실습 시나리오를 만들어줘."
    )
    print(f"\n[Turn 4 입력]: 심도 확장 질문 답변 제출")
    r4, _ = await run_turn(agent, p4, session)
    print(f"-> 결과 단계: {r4.stage}")
    full_output = reply_to_markdown(r4)
    print(f"-> 최종 시나리오 전문:\n{full_output}")

    return {
        "mode": mode_name,
        "vs_id": vs_id,
        "r1_explanation": r1.support.explanation,
        "candidates": [c.model_dump() for c in r2.support.candidates],
        "deep_questions": r3.support.explanation,
        "final_scenario": full_output
    }

async def run_all():
    results = {}
    # 1. 교과서 PDF RAG
    results["FILE_RAG"] = await test_cellulitis_mode("📚 교과서 PDF RAG", FILE_STORE_ID)
    # 2. 웹 URL RAG
    results["URL_RAG"] = await test_cellulitis_mode("🌐 웹 URL RAG", URL_STORE_ID)
    # 3. RAG OFF
    results["RAG_OFF"] = await test_cellulitis_mode("⚪ RAG OFF (순수 LLM)", None)

    with open("cellulitis_rag_comparison_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n🎉 모든 모드 봉와직염 비교 검증 완료! -> cellulitis_rag_comparison_result.json")

if __name__ == "__main__":
    asyncio.run(run_all())
