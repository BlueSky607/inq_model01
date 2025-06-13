import pymongo
import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from datetime import datetime

# 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

# OpenAI API 설정
client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB 클라이언트 초기화 (글로벌로 한 번만)
@st.cache_resource
def get_mongo_client():
    return pymongo.MongoClient(st.secrets["MONGO_URI"])

mongo_client = pymongo.MongoClient(st.secrets["MONGO_URI"])
mongo_db = mongo_client['qua_db']  # DB 이름 변경
qna_collection = mongo_db['qna']  # 콜렉션 이름 변경
feedback_collection = mongo_db['feedback']  # 피드백 저장을 위한 콜렉션 추가

# MongoDB 저장 함수 (대화 기록)
def save_to_db(all_data):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False

    try:
        now = datetime.now()
        document = {
            "number": number,
            "name": name,
            "chat": all_data,  # 그대로 리스트 형태 저장 가능
            "time": now
        }
        qna_collection.insert_one(document)
        return True
    except Exception as e:
        st.error(f"MongoDB 저장 중 오류가 발생했습니다: {e}")
        return False

# MongoDB 저장 함수 (피드백)
def save_feedback_to_db(feedback):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False

    try:
        now = datetime.now()
        document = {
            "number": number,
            "name": name,
            "feedback": feedback,
            "time": now
        }
        feedback_collection.insert_one(document)
        st.success("피드백이 성공적으로 저장되었습니다.")
        return True
    except Exception as e:
        st.error(f"MongoDB 저장 중 오류가 발생했습니다: {e}")
        return False

# GPT 응답 생성 함수
def get_chatgpt_response(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": "수학여행 도우미 챗봇"}] + st.session_state["messages"] + [{"role": "user", "content": prompt}],
        )

        # 응답 로그 출력
        st.write("API 응답:", response)

        # 응답 내용이 정상적으로 들어있는지 확인 (응답 구조 변경을 반영)
        if 'choices' in response and len(response['choices']) > 0:
            # 메시지가 존재하는지 확인
            if 'message' in response['choices'][0] and 'content' in response['choices'][0]['message']:
                answer = response['choices'][0]['message']['content']
            else:
                raise KeyError("Expected keys not found in response['choices'][0]['message']")
        else:
            raise KeyError("Expected 'choices' key not found or it's empty")

        # 대화 저장
        st.session_state["messages"].append({"role": "user", "content": prompt})
        st.session_state["messages"].append({"role": "assistant", "content": answer})
        return answer

    except KeyError as e:
        st.error(f"API 응답에서 예상한 키가 없습니다: {e}")
        st.write("응답 구조:", response)  # 응답 구조를 자세히 출력
        return "오류가 발생했습니다. 잠시 후 다시 시도해주세요."

    except Exception as e:
        st.error(f"예상치 못한 오류가 발생했습니다: {e}")
        st.write("응답 구조:", response)  # 응답 구조를 자세히 출력
        return "오류가 발생했습니다. 잠시 후 다시 시도해주세요."


# 페이지 1: 학번 및 이름 입력
def page_1():
    st.title("수학여행 도우미 챗봇 M1")
    st.write("학번과 이름을 입력한 뒤 '다음' 버튼을 눌러주세요.")

    if "user_number" not in st.session_state:
        st.session_state["user_number"] = ""
    if "user_name" not in st.session_state:
        st.session_state["user_name"] = ""

    st.session_state["user_number"] = st.text_input("학번", value=st.session_state["user_number"])
    st.session_state["user_name"] = st.text_input("이름", value=st.session_state["user_name"])

    st.write(" ")  # Add space to position the button at the bottom properly
    if st.button("다음", key="page1_next_button"):
        if st.session_state["user_number"].strip() == "" or st.session_state["user_name"].strip() == "":
            st.error("학번과 이름을 모두 입력해주세요.")
        else:
            st.session_state["step"] = 2
            st.rerun()

# 페이지 2: 사용법 안내
def page_2():
    st.title("수학여행 도우미 활용 방법")
    st.write(
       """  
        ※주의! '자동 번역'을 활성화하면 대화가 이상하게 번역되므로 활성화하면 안 돼요. 혹시 이미 '자동 번역' 버튼을 눌렀다면 비활성화 하세요.  

학생은 다음과 같은 절차로 챗봇을 활용하도록 안내되었습니다:

① 인공지능에게 수학 문제를 알려주세요.

② LATEx기반으로 문제 입력시 (1)문장 속 수식은 `$수식$`, (2)블록 수식은 `$$ 수식 $$` 형식으로 입력해주세요.

③ 인공지능은 문제 해결에 필요한 수학 개념, 공식, 해결 전략, 접근 방향을 단계적으로 안내할 거예요. 궁금한 점은 언제든지 질문하세요.

④ 궁금한 걸 다 물어봤다면 ‘궁금한 건 다 물어봤어’라고 말해주세요. 또는 [마침] 버튼을 눌러주세요.

⑤ 인공지능이 충분히 대화가 이루어졌다고 판단되면 [다음] 버튼을 눌러도 된다고 안내할 거예요. 그때 버튼을 눌러주세요.
        """)

    # 버튼
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("이전"):
            st.session_state["step"] = 1
            st.rerun()

    with col2:
        if st.button("다음", key="page2_next_button"):
            st.session_state["step"] = 3
            st.rerun()

# 페이지 3: GPT와 대화
def page_3():
    st.title("수학여행 도우미 활용하기")
    st.write("수학여행 도우미와 대화를 나누며 수학을 설계하세요.")

    if not st.session_state.get("user_number") or not st.session_state.get("user_name"):
        st.error("학번과 이름이 누락되었습니다. 다시 입력해주세요.")
        st.session_state["step"] = 1
        st.rerun()

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "user_input_temp" not in st.session_state:
        st.session_state["user_input_temp"] = ""

    if "recent_message" not in st.session_state:
        st.session_state["recent_message"] = {"user": "", "assistant": ""}

    user_input = st.text_area(
        "You: ",
        value=st.session_state["user_input_temp"],
        key="user_input",
        on_change=lambda: st.session_state.update({"user_input_temp": st.session_state["user_input"]}),
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("전송"):
            if user_input.strip():
                assistant_response = get_chatgpt_response(user_input)
                st.session_state["recent_message"] = {"user": user_input, "assistant": assistant_response}
                st.session_state["user_input_temp"] = ""
                st.rerun()

    with col2:
        if st.button("마침"):
            # 마침 버튼 클릭 시 내부적으로 '궁금한 건 다 물어봤어' 전송
            final_input = "궁금한 건 다 물어봤어"
            assistant_response = get_chatgpt_response(final_input)
            st.session_state["recent_message"] = {"user": final_input, "assistant": assistant_response}
            st.session_state["user_input_temp"] = ""
            st.rerun()

    # 최근 대화 출력
    st.subheader("📌 최근 대화")
    if st.session_state["recent_message"]["user"] or st.session_state["recent_message"]["assistant"]:
        st.write(f"**You:** {st.session_state['recent_message']['user']}")
        st.write(f"**수학여행 도우미:** {st.session_state['recent_message']['assistant']}")
    else:
        st.write("아직 최근 대화가 없습니다.")

    # 누적 대화 출력
    st.subheader("📜 누적 대화 목록")
    if st.session_state["messages"]:
        for message in st.session_state["messages"]:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**수학여행 도우미:** {message['content']}")
    else:
        st.write("아직 대화 기록이 없습니다.")

    col3, col4 = st.columns([1, 1])
    with col3:
        if st.button("이전"):
            st.session_state["step"] = 2
            st.rerun()
    with col4:
        if st.button("다음", key="page3_next_button"):
            st.session_state["step"] = 4
            st.session_state["feedback_saved"] = False
            st.rerun()

# 페이지 4: 문제 풀이 과정 출력
def page_4():
    st.title("수학여행 도우미의 제안")
    st.write("수학여행 도우미가 대화 내용을 정리 중입니다. 잠시만 기다려주세요.")

    # 페이지 4로 돌아올 때마다 새로운 피드백 생성
    if not st.session_state.get("feedback_saved", False):
        # 대화 기록을 기반으로 풀이 과정 작성
        chat_history = "\n".join(f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"])
        prompt = f"""
다음은 학생과 수학여행 도우미의 대화 기록입니다:

{chat_history}

---

1. 아래 조건을 반드시 확인하세요:

- 대화 중에 **"[다음] 버튼을 눌러도 됩니다"** 또는 이와 같은 의미의 문장이 포함되어 있는지 철저히 확인하세요.
- 포함되어 있지 않다면, 아래 문장을 그대로 출력하고 종료하세요:
  → "[이전] 버튼을 눌러 수학여행 도우미와 더 대화해야 합니다"
- 실수 방지를 위해 **대화를 끝까지 정밀하게 검토**하세요.

---

2. [다음] 버튼을 눌러도 된다는 내용이 포함된 경우, 아래 3가지를 포함하여 피드백을 작성하세요:

📌 **1. 대화 내용 요약**  
- 학생이 어떤 개념을 시도했고, 어떤 실수를 했으며 어떻게 수정했는지를 중심으로 요약하세요.  
- 가독성을 위해 문단마다 줄바꿈을 사용하세요.

💬 **2. 문제해결 능력 피드백**  
- 개념 적용, 전략적 사고, 자기주도성, 오개념 교정 등의 측면에서 평가하세요.

🧾 **3. 수학적 결과 또는 전략 정리 (조건 분기)**

- **학생이 정확한 정답을 제시한 경우**:
  - 문제 풀이 과정을 간결히 요약하고, LaTeX 수식으로 최종 정답을 제시하세요.

- **정답을 제시하지 못했거나 오답을 제시한 경우**:
- 문제 해결에 필요한 핵심 개념, 공식, 전략만 정리하세요. 설명은 생략하고 수식만 제시하세요.

반드시 위 형식을 따르고, 항목 순서를 변경하지 마세요.
"""  
        # OpenAI API 호출
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": prompt}]
        )
        st.session_state["experiment_plan"] = response.choices[0].message.content

    # 피드백 출력
    st.subheader("📋 생성된 피드백")
    st.write(st.session_state["experiment_plan"])

    # 새로운 변수에 대화 내용과 피드백을 통합
    if "all_data" not in st.session_state:
        st.session_state["all_data"] = []

    all_data_to_store = st.session_state["messages"] + [{"role": "assistant", "content": st.session_state["experiment_plan"]}]

    # 중복 저장 방지: 피드백 저장 여부 확인
    if "feedback_saved" not in st.session_state:
        st.session_state["feedback_saved"] = False  # 초기화

    if not st.session_state["feedback_saved"]:
        # 새로운 데이터(all_data_to_store)를 MongoDB에 저장
        if save_to_db(all_data_to_store):  # 기존 save_to_db 함수에 통합된 데이터 전달
            st.session_state["feedback_saved"] = True  # 저장 성공 시 플래그 설정
        else:
            st.error("저장에 실패했습니다. 다시 시도해주세요.")

    # 이전 버튼 (페이지 3으로 이동 시 피드백 삭제)
    if st.button("이전", key="page4_back_button"):
        st.session_state["step"] = 3
        if "experiment_plan" in st.session_state:
            del st.session_state["experiment_plan"]  # 피드백 삭제
        st.session_state["feedback_saved"] = False  # 피드백 재생성 플래그 초기화
        st.rerun()

# 메인 로직
if "step" not in st.session_state:
    st.session_state["step"] = 1

if st.session_state["step"] == 1:
    page_1()
elif st.session_state["step"] == 2:
    page_2()
elif st.session_state["step"] == 3:
    page_3()
elif st.session_state["step"] == 4:
    page_4()

