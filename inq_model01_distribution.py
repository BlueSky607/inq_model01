import streamlit as st
from openai import OpenAI
from datetime import datetime
import pymongo
from pymongo import MongoClient
import os

# --- MongoDB 연결 설정 ---
MONGO_URI = st.secrets["MONGO_URI"]
client = MongoClient(MONGO_URI)
db = client["math_tutor"]
collection = db["chat_logs"]

# --- GPT API 설정 ---
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# --- GPT 호출 함수 ---
def ask_gpt(messages):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content

# --- 초기 system 메시지 ---
SYSTEM_PROMPT = """
너는 '수학여행 도우미'라는 이름의 챗봇이야. 중학생이 수학 문제를 스스로 탐구할 수 있도록 질문하고 안내하는 역할을 해. 절대 정답이나 해설을 직접 알려주지 말고, 학생이 생각할 수 있도록 유도해줘.
"""

# --- 초기화 함수 ---
def reset_session():
    st.session_state.clear()
    st.session_state["step"] = "page_1"
    st.session_state["messages"] = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state["history"] = []

# --- MongoDB 저장 함수 ---
def save_to_mongo():
    data = {
        "학번": st.session_state.get("student_id", ""),
        "이름": st.session_state.get("student_name", ""),
        "시작시각": st.session_state.get("start_time", ""),
        "종료시각": datetime.now(),
        "대화기록": st.session_state.get("history", []),
        "최종요약": st.session_state.get("summary", "")
    }
    collection.insert_one(data)

# --- 1단계: 이름과 학번 입력 페이지 ---
def page_1():
    st.title("수학여행 도우미 🧭")
    st.write("수학 문제를 탐구하는 여정에 오신 것을 환영합니다.")

    with st.form("user_info_form"):
        student_id = st.text_input("학번을 입력하세요")
        student_name = st.text_input("이름을 입력하세요")
        submitted = st.form_submit_button("시작하기")

    if submitted:
        if not student_id or not student_name:
            st.warning("모든 항목을 입력해주세요.")
        else:
            st.session_state["student_id"] = student_id
            st.session_state["student_name"] = student_name
            st.session_state["start_time"] = datetime.now()
            st.session_state["step"] = "page_2"
            st.rerun()

# --- 2단계: 사용법 안내 페이지 ---
def page_2():
    st.header("📝 사용 방법 안내")
    st.markdown("""
    - 이 챗봇은 정답을 알려주지 않고 **생각을 이끌어주는 질문**을 해줄 거예요.
    - 여러분은 문제를 풀기 위한 **전략, 아이디어, 계산 과정**을 자유롭게 이야기해보세요.
    - 탐구가 끝났다고 생각되면 **[마침] 버튼**을 눌러 대화를 종료할 수 있어요.
    """)
    if st.button("탐구 시작하기"):
        st.session_state["step"] = "page_3"
        st.rerun()

# --- 3단계: 챗봇 대화 페이지 ---
def page_3():
    st.header("💬 수학 탐구 챗봇")
    chat_placeholder = st.empty()
    user_input = st.chat_input("당신의 생각을 이야기해 보세요!")

    # 이전 메시지 출력
    with chat_placeholder.container():
        for msg in st.session_state["messages"][1:]:
            role = "🧑" if msg["role"] == "user" else "🤖"
            st.markdown(f"{role} **{msg['content']}**")

    # 사용자 입력 처리
    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        st.session_state["history"].append({"role": "user", "content": user_input})

        with st.spinner("도우미가 생각 중입니다..."):
            assistant_response = ask_gpt(st.session_state["messages"])
            st.session_state["messages"].append({"role": "assistant", "content": assistant_response})
            st.session_state["history"].append({"role": "assistant", "content": assistant_response})

        st.rerun()

    # 마침 버튼
    if st.button("🔚 마침"):
        st.session_state["step"] = "page_4"
        st.rerun()

# --- 4단계: 요약 및 저장 페이지 ---
def page_4():
    st.header("🧾 탐구 요약 및 저장")

    st.markdown("이번 탐구를 마치며, 어떤 내용을 탐구했는지 요약해드릴게요.")

    # GPT에게 요약 요청
    if "summary" not in st.session_state:
        with st.spinner("요약 중입니다..."):
            summary_prompt = [
                {"role": "system", "content": "지금부터 너는 대화를 요약하는 수학 도우미야."},
                {"role": "user", "content": "아래는 학생과 도우미의 대화야. 수학 탐구 주제, 시도한 방법, 학생이 도달한 결론 또는 전략을 요약해줘. 절대 정답을 평가하지 말고 탐구 과정만 정리해줘."},
                {"role": "user", "content": str(st.session_state["history"])}
            ]
            summary = ask_gpt(summary_prompt)
            st.session_state["summary"] = summary

    st.markdown(f"📝 **탐구 요약**\n\n{st.session_state['summary']}")

    if st.button("💾 저장하고 종료"):
        save_to_mongo()
        st.success("탐구 내용이 저장되었습니다. 수고하셨습니다!")
        if st.button("🔁 처음으로"):
            reset_session()
            st.rerun()

# --- 앱 실행 ---
if "step" not in st.session_state:
    reset_session()

step = st.session_state["step"]

if step == "page_1":
    page_1()
elif step == "page_2":
    page_2()
elif step == "page_3":
    page_3()
elif step == "page_4":
    page_4()




