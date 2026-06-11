import html as html_lib
import json
import markdown as md_lib
import streamlit as st
from openai import OpenAI

st.set_page_config(
    page_title="서울 관광 AI 가이드",
    page_icon="🗼",
    layout="centered",
)

SYSTEM_PROMPT = """당신은 서울 전문 관광 AI 가이드 '서울이'입니다.
서울의 관광지, 맛집, 교통, 숙소, 쇼핑, 문화, 축제 등 모든 서울 여행 관련 질문에 친절하고 상세하게 답변합니다.
답변 시 구체적인 장소명, 운영시간, 교통 정보, 실용적인 팁을 포함하세요.
한국어로 답변하되, 사용자가 다른 언어로 질문하면 그 언어로 답변하세요.
답변은 간결하고 읽기 쉽게 작성하세요."""

WELCOME_MSG = "안녕하세요! 저는 서울 관광 AI 가이드 **서울이**예요 🗼\n\n서울 여행에 대해 무엇이든 물어보세요!\n관광지, 맛집, 교통, 숙소 정보를 안내해 드릴게요 😊"

CATEGORY_QUERIES = {
    "🏛️ 관광지": "서울의 꼭 가봐야 할 대표 관광지를 추천해줘",
    "🍜 맛집": "서울에서 꼭 먹어야 할 음식과 맛집을 알려줘",
    "🚇 교통": "서울 대중교통 이용 방법을 알려줘",
    "🏨 숙소": "여행자를 위한 서울 숙소를 추천해줘",
    "🛍️ 쇼핑": "서울 쇼핑 명소와 쇼핑 팁을 알려줘",
    "🎭 문화/축제": "서울의 주요 문화 행사와 축제를 알려줘",
}

# ── CSS ──────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
#MainMenu, footer, header { visibility: hidden; }

.stApp {
    background: #f0f4f8;
    font-family: -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo',
                 'Noto Sans KR', sans-serif;
}

/* Center narrow container */
.main .block-container {
    max-width: 460px !important;
    margin: 0 auto !important;
    padding: 78px 14px 90px !important;
}

/* Fixed top app bar */
.topbar {
    position: fixed; top: 0; left: 0; right: 0; z-index: 1000;
    background: linear-gradient(135deg, #002d72 0%, #0054b0 100%);
    text-align: center; padding: 11px 16px 10px;
    box-shadow: 0 2px 12px rgba(0,45,114,0.35);
}
.topbar-title { color: #fff; font-size: 16px; font-weight: 700; margin: 0; letter-spacing: -.3px; }
.topbar-sub   { color: rgba(255,255,255,.72); font-size: 11px; margin: 2px 0 0; }

/* Date divider */
.date-div {
    text-align: center; color: #9aabbd; font-size: 11px;
    margin: 12px 0 8px; letter-spacing: .3px;
}

/* User bubble — right */
.bubble-user { display: flex; justify-content: flex-end; margin: 5px 0 3px; }
.bubble-user-inner {
    background: #0084ff; color: #fff;
    border-radius: 18px 18px 4px 18px;
    padding: 9px 14px; max-width: 78%;
    font-size: 14px; line-height: 1.55;
    word-break: break-word; white-space: pre-wrap;
}

/* AI bubble — left */
.bubble-ai { display: flex; align-items: flex-start; gap: 8px; margin: 5px 0 3px; }
.bubble-ai-avatar {
    width: 34px; height: 34px; border-radius: 50%;
    background: linear-gradient(135deg, #002d72, #0054b0);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
    box-shadow: 0 2px 5px rgba(0,45,114,.25);
}
.bubble-ai-inner {
    background: #fff; color: #1a1a1a;
    border-radius: 4px 18px 18px 18px;
    padding: 10px 14px; max-width: 78%;
    font-size: 14px; line-height: 1.6;
    box-shadow: 0 1px 4px rgba(0,0,0,.1);
    word-break: break-word;
}
.bubble-ai-inner p  { margin: 0 0 6px; }
.bubble-ai-inner p:last-child { margin: 0; }
.bubble-ai-inner ul, .bubble-ai-inner ol { margin: 4px 0; padding-left: 20px; }
.bubble-ai-inner li { margin: 2px 0; }
.bubble-ai-inner strong { color: #002d72; }
.bubble-ai-inner code {
    background: #f0f4f8; border-radius: 4px;
    padding: 1px 5px; font-size: 12px;
}

/* Category pill buttons */
div[data-testid="stHorizontalBlock"] button {
    border-radius: 18px !important;
    border: 1.5px solid #0054b0 !important;
    color: #0054b0 !important;
    background: #fff !important;
    font-size: 11.5px !important;
    padding: 4px 0 !important;
    font-weight: 500 !important;
    transition: all .15s !important;
}
div[data-testid="stHorizontalBlock"] button:hover {
    background: #0054b0 !important;
    color: #fff !important;
}

/* Fixed bottom chat input */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important; left: 50% !important;
    transform: translateX(-50%) !important;
    width: min(460px, 100%) !important;
    background: #f0f4f8 !important;
    padding: 10px 14px 16px !important;
    z-index: 999 !important;
    border-top: 1px solid #dde3ec !important;
}

/* Sidebar */
section[data-testid="stSidebar"] > div { background: #001f4d !important; }
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p { color: rgba(255,255,255,.88) !important; }
section[data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
    background: rgba(255,255,255,.12) !important;
    color: #fff !important; border: none !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #c0c8d8; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

# ── Top bar ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="topbar">
    <div class="topbar-title">🗼 서울 관광 AI 가이드</div>
    <div class="topbar-sub">Seoul Travel Assistant · AI Powered</div>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    openai_api_key = st.text_input("OpenAI API Key", type="password")
    st.divider()
    model = st.selectbox(
        "모델 선택",
        ["gpt-4o-mini", "gpt-4-mini", "gpt-5", "gpt-4o", "gpt-3.5-turbo"],
        index=0,
        help="gpt-4o-mini: 빠르고 저렴 / gpt-4o: 고성능",
    )
    temperature = st.slider("Temperature (창의성)", 0.0, 2.0, 0.7, 0.1)
    st.divider()
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    if st.session_state.get("messages"):
        msgs = st.session_state.messages
        st.download_button(
            "💾 내보내기 (.txt)",
            data="\n\n".join(f"[{m['role'].upper()}]\n{m['content']}" for m in msgs),
            file_name="seoul_chat.txt", mime="text/plain",
            use_container_width=True,
        )
        st.download_button(
            "📄 내보내기 (.json)",
            data=json.dumps(msgs, ensure_ascii=False, indent=2),
            file_name="seoul_chat.json", mime="application/json",
            use_container_width=True,
        )

# ── API key guard ─────────────────────────────────────────────────────────────
if not openai_api_key:
    st.info("사이드바에 OpenAI API 키를 입력하면 대화를 시작할 수 있습니다.", icon="🗝️")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# ── Session state ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "preset_prompt" not in st.session_state:
    st.session_state.preset_prompt = None

# ── Render helpers ────────────────────────────────────────────────────────────
def render_user(content: str):
    escaped = html_lib.escape(content)
    st.markdown(
        f'<div class="bubble-user"><div class="bubble-user-inner">{escaped}</div></div>',
        unsafe_allow_html=True,
    )

def render_assistant(content: str):
    html_content = md_lib.markdown(content)
    st.markdown(
        f'<div class="bubble-ai">'
        f'<div class="bubble-ai-avatar">🗼</div>'
        f'<div class="bubble-ai-inner">{html_content}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def render_streaming(placeholder, text: str, done: bool = False):
    cursor = "" if done else "▌"
    escaped = html_lib.escape(text)
    placeholder.markdown(
        f'<div class="bubble-ai">'
        f'<div class="bubble-ai-avatar">🗼</div>'
        f'<div class="bubble-ai-inner" style="white-space:pre-wrap">{escaped}{cursor}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Welcome (first visit) ─────────────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown('<div class="date-div">오늘 서울 여행을 시작해보세요 ✈️</div>', unsafe_allow_html=True)
    render_assistant(WELCOME_MSG)

# ── Chat history ──────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        render_user(msg["content"])
    else:
        render_assistant(msg["content"])

# ── Category quick buttons ────────────────────────────────────────────────────
cols = st.columns(len(CATEGORY_QUERIES))
for col, (cat, query) in zip(cols, CATEGORY_QUERIES.items()):
    with col:
        if st.button(cat, key=f"cat_{cat}", use_container_width=True):
            st.session_state.preset_prompt = query
            st.rerun()

# ── Chat input ────────────────────────────────────────────────────────────────
typed = st.chat_input("서울 여행에 대해 무엇이든 물어보세요! 🗼")

prompt = typed
if st.session_state.preset_prompt:
    prompt = st.session_state.preset_prompt
    st.session_state.preset_prompt = None

# ── Generate response ─────────────────────────────────────────────────────────
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_user(prompt)

    placeholder = st.empty()
    full_response = ""

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *[{"role": m["role"], "content": m["content"]}
                  for m in st.session_state.messages],
            ],
            temperature=temperature,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            full_response += delta
            render_streaming(placeholder, full_response)
        render_streaming(placeholder, full_response, done=True)
    except Exception as e:
        placeholder.error(f"오류가 발생했습니다: {e}")
        full_response = None

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
