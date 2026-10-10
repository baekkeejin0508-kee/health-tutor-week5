"""Run: streamlit run app.py. Use fictional learning cases only."""
import asyncio
import json
import os
from datetime import datetime, timezone

import streamlit as st
from tutor import build_agent, new_session, reply_to_markdown, run_turn

st.set_page_config(page_title='AI 보건튜터 5주차', page_icon='📘', layout='centered')


def reset():
    st.session_state.agent_session = new_session()
    st.session_state.messages = []
    st.session_state.events = []


if 'agent_session' not in st.session_state:
    reset()

st.title('AI 보건튜터')
st.caption('특성화고 2학년 · 단원 개념부터 탐구질문과 모의실습까지')
st.info('가상 사례 학습용입니다. 실제 환자·학생의 이름, 연락처, 건강정보를 입력하지 마세요. '
        '5주차는 자료 검색이 연결되지 않았으며 의학적 설명과 실습 적합성은 교사가 확인합니다.')

try:
    secret_key = st.secrets.get('OPENAI_API_KEY', '')
except FileNotFoundError:
    secret_key = ''
if not os.getenv('OPENAI_API_KEY') and secret_key:
    os.environ['OPENAI_API_KEY'] = secret_key

with st.sidebar:
    st.header('테스트 설정')
    version = st.selectbox('Instructions', ['v2', 'v1'])
    model = st.text_input('사용 가능한 모델 ID', value=os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'))
    model = model.strip()
    config = (version, model)
    if 'config' not in st.session_state:
        st.session_state.config = config
    elif st.session_state.config != config:
        reset()
        st.session_state.config = config
    if st.button('새 학습 시작 · 대화 초기화'):
        reset()
        st.rerun()
    st.caption('모델·Instructions 변경 시 대화가 초기화됩니다. 새로고침 전 기록을 다운로드하세요.')
    st.write('개념 자기 설명 → 탐구질문 → 상황 초안 → 후보 3개 → 학생 선택 → 간호활동 → 수정 → 교사 검토')
    st.write('교사 확인은 학생이 기록을 전달하는 방식입니다. 자동 발송·교사 로그인은 없습니다.')

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

ready = bool(os.getenv('OPENAI_API_KEY')) and bool(model)
if not ready:
    st.warning('OPENAI_API_KEY와 모델 ID를 설정하면 대화를 실행할 수 있습니다. 실행 안내를 확인하세요.')

text_input = st.chat_input('단원, 어려운 개념, 내 생각을 적어 주세요.', disabled=not ready)
if text_input:
    if len(text_input) > 6000:
        st.error('한 번에 6000자 이내로 나누어 입력해 주세요.')
    else:
        with st.chat_message('user'):
            st.markdown(text_input)
        with st.chat_message('assistant'):
            with st.spinner('학생의 생각을 확인하고 있습니다.'):
                try:
                    agent = build_agent(model, version)
                    reply, event = asyncio.run(run_turn(agent, text_input, st.session_state.agent_session))
                    response = reply_to_markdown(reply)
                    st.markdown(response)
                    st.session_state.messages.extend([
                        {'role': 'user', 'content': text_input},
                        {'role': 'assistant', 'content': response},
                    ])
                    st.session_state.events.append({
                        'utc': datetime.now(timezone.utc).isoformat(),
                        'model': model, 'instructions': version,
                        'reply': reply.model_dump(), **event,
                    })
                except Exception as exc:
                    # Do not expose exception text, key, endpoint or hidden prompt.
                    st.error('응답을 완료하지 못했습니다. 키·모델 접근 권한·잔액·네트워크를 확인한 후 다시 입력하세요. '
                             '형식 오류가 반복되면 새 학습으로 테스트하세요.')
                    st.session_state.events.append({
                        'utc': datetime.now(timezone.utc).isoformat(),
                        'model': model, 'instructions': version,
                        'error_type': type(exc).__name__,
                    })

if st.session_state.messages or st.session_state.events:
    export = {'notice': '가상 학습 기록. 교사에게 자동 전송되지 않음.',
              'messages': st.session_state.messages, 'events': st.session_state.events}
    st.download_button('교사 검토 및 테스트 기록 다운로드 JSON',
                       json.dumps(export, ensure_ascii=False, indent=2),
                       file_name='health_tutor_record.json', mime='application/json')
    transcript = '\n\n'.join(f'{m["role"]}\n{m["content"]}' for m in st.session_state.messages)
    st.download_button('대화 기록 다운로드 TXT', transcript,
                       file_name='health_tutor_record.txt', mime='text/plain')
    with st.expander('관찰 기록 · 내부 추론 아님'):
        st.json(st.session_state.events)
