import json
import streamlit as st
from openai import OpenAI

st.title("💬 Chatbot")
st.write(
    "OpenAI 모델을 사용하는 챗봇입니다. "
    "사용하려면 OpenAI API 키를 입력하세요. "
    "[API 키 발급](https://platform.openai.com/account/api-keys)"
)

# --- Sidebar ---
with st.sidebar:
    st.header("설정")

    openai_api_key = st.text_input("OpenAI API Key", type="password")

    model = st.selectbox(
        "모델 선택",
        ["gpt-4o-mini", "gpt-4-mini", "gpt-5", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
        help="gpt-4-mini / gpt-5: 최신 모델 / gpt-4o-mini: 빠르고 저렴 / gpt-4o: 고성능",
    )

    temperature = st.slider(
        "Temperature (창의성)",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="낮을수록 일관된 답변, 높을수록 창의적인 답변",
    )

    st.divider()

    if st.button("대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    # Export buttons
    if st.session_state.get("messages"):
        st.download_button(
            label="대화 내보내기 (.txt)",
            data="\n\n".join(
                f"[{m['role'].upper()}]\n{m['content']}"
                for m in st.session_state.messages
            ),
            file_name="chat_history.txt",
            mime="text/plain",
            use_container_width=True,
        )
        st.download_button(
            label="대화 내보내기 (.json)",
            data=json.dumps(st.session_state.messages, ensure_ascii=False, indent=2),
            file_name="chat_history.json",
            mime="application/json",
            use_container_width=True,
        )

# --- Main chat area ---
if not openai_api_key:
    st.info("사이드바에 OpenAI API 키를 입력하면 대화를 시작할 수 있습니다.", icon="🗝️")
    st.stop()

client = OpenAI(api_key=openai_api_key)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("메시지를 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            temperature=temperature,
            stream=True,
        )
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
