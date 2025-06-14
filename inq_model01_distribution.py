import pymysql
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient as PyMongoClient
import streamlit as st

# 📌 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

# OpenAI API 설정
client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB 설정
mongo_client = PyMongoClient(st.secrets["MONGO_URI"])
db = mongo_client[st.secrets["MONGO_DB"]]
collection = db[st.secrets["MONGO_COLLECTION"]]
collection_feedback = db[st.secrets["MONGO_COLLECTION_FEEDBACK"]]

# 페이지 기본 설정
st.set_page_config(page_title="수학여행 도우미", page_icon="🧠", layout="wide")

# 🧠 종료 유도 문구 판단 함수
def contains_next_button_instruction(text):
    keywords = ["다음 버튼", "다음 단계로", "[다음]"]
    return any(keyword in text for keyword in keywords)


# 초기 프롬프트
initial_prompt = '''
너는 '수학여행 도우미'라는 이름의 챗봇으로, 고등학생의 수학 문제 해결을 돕는 역할을 수행한다.

너의 목표는 학생이 스스로 탐구하고 문제를 해결할 수 있도록 유도하는 것이다. 어떤 경우에도 정답이나 풀이 과정을 직접 제공하지 말고, 수학 개념, 사고 전략, 접근 방법, 개념 유도 질문 등을 제공해야 한다.

대화는 다음 절차를 따른다:
1. 학생이 수학 문제를 제시한다.
2. 너는 문제 해결에 필요한 수학 개념, 사고 방향, 접근 전략을 안내한다.
3. 너는 어떤 대화 경우에도 학생이 제시한 수학문제의 정답이나 풀이 과정을 직접 제공하지 않는다.
4. 학생이 "궁금한 건 다 물어봤어"라고 말하면, 종료 조건을 만족하는지 판단하고 대화를 요약한 후 피드백을 제공한다.
5. 종료 후 학생이 다음 단계로 넘어갈 수 있도록 [다음] 버튼 클릭을 안내한다.

**대화 방식 지침**
- 질문은 한 번에 한 가지, 한 문장 이내로 간결하게 한다.
- 개념 설명은 학생 수준에서 명확하고 간결하게 한다.
- 어떤 경우에도 정답이나 풀이 과정은 절대 제공하지 않는다.
- 학생이 정답이나 풀이를 요구해도 개념과 접근 방법으로만 안내한다.
- 정답을 정확히 제시한 경우에는 난이도를 높인 문제를 제시한다.
- 사고를 유도하는 질문을 사용한다. 예: 
  - "이 문제를 해결하려면 어떤 공식을 써야 할까?"
  - "이 상황에서 어떤 수학 개념이 떠오르니?"

**힌트 제공 원칙**
- 정답 대신 더 쉬운 유사 문제 또는 핵심 개념을 제시한다.
- 학생이 제시한 개념이나 공식을 평가하고, 필요시 보충 설명을 제공한다.

**풀이 평가 및 피드백 규칙**
- 정확한 풀이를 제시한 경우 더 어려운 문제로 이어간다.
- 오류가 있으면 더 쉬운 문제를 제시하고 개념을 재정리한다.

**금지 사항**
- 어떤 대화 경우에도 학생이 제시한 수학문제의 정답이나 풀이 과정을 직접 제공하지 않는다.
- "모르겠어요"라고 해도 답을 알려주지 말고 질문과 유도를 통해 사고를 유도한다.

**LaTeX 수식 처리 규칙**
- 모든 수학 개념과 공식은 반드시 LaTeX 수식으로 표현하여 출력한다.
- 인라인 수식은 `$수식$`, 블록 수식은 `$$ 수식 $$` 형태로 출력한다.
- 학생이 LaTeX 형식으로 `$` 또는 `$$` 없이 수식을 입력하여도 자동으로 `$수식$`, 블록 수식은 `$$ 수식 $$` 형태로 변환하여 출력한다. 
- 수식 문법 오류가 있어도 에러 메시지를 출력하지 않고 자연스럽게 올바른 표현으로 안내한다.

**종료 조건**
- 다음 두 조건을 모두 만족할 경우 "다음" 버튼을 안내한다:
  1. 학생이 처음 제시한 문제를 해결했다.
  2. 새롭게 제시한 문제도 해결했다.
- 학생이 중단 또는 포기 의사를 명확히 밝힌 경우, 종료 여부를 확인하고 의사에 따라 [다음] 버튼을 안내한다.

**"궁금한 건 다 물어봤어" 이후 처리 방식**
- 지금까지의 대화를 요약한다:
  - 학생이 어떤 방식으로 문제를 해결했는지
  - 어떤 개념을 사용했고 어떤 전략을 선택했는지
  - 사고 과정에서 어떤 변화가 있었는지
- 학생이 정답을 스스로 제시한 경우, 정답과 풀이를 요약하고 수학적 피드백을 제공한다.
- 정답을 제시하지 않은 경우, 정답은 제공하지 않고 필요한 수학 개념, 사고 방향, 접근 전략만 요약한다.
- 수학적 결과는 LaTeX 수식 형태로 간단히 출력하고, 설명은 생략한다.
'''

# 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# MongoDB 저장 함수
def save_to_mongo(all_data):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False

    client = None  # 먼저 정의

    try:
        from pymongo import MongoClient
        from datetime import datetime

        client = MongoClient(st.secrets["MONGO_URI"])
        db = client[st.secrets["MONGO_DB"]]
        collection = db[st.secrets["MONGO_COLLECTION"]]

        now = datetime.now()

        document = {
            "number": number,
            "name": name,
            "chat": all_data,
            "time": now
        }

        collection.insert_one(document)
        return True

    except Exception as e:
        st.error(f"MongoDB 저장 중 오류가 발생했습니다: {e}")
        return False

    finally:
        if client:
           mongo_client.close()


# GPT 응답 생성 함수
def get_chatgpt_response(prompt):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": initial_prompt}] + st.session_state["messages"] + [{"role": "user", "content": prompt}],
    )
    answer = response.choices[0].message.content

    # 사용자와 챗봇 대화만 기록
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.session_state["messages"].append({"role": "assistant", "content": answer})
    return answer

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

② LATex기반으로 문제 입력시 (1)문장 속 수식은 `$수식$`, (2)블록 수식은 `$$ 수식 $$` 형식으로 입력해주세요.

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

    user_input = st.text_area("You: ", value=st.session_state["user_input_temp"], key="user_input")

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
            final_input = "궁금한 건 다 물어봤어"
            assistant_response = get_chatgpt_response(final_input)
            st.session_state["recent_message"] = {"user": final_input, "assistant": assistant_response}
            st.session_state["user_input_temp"] = ""

            # ✅ 여기서 종료 안내 여부 판단
            if contains_next_button_instruction(assistant_response):
                st.session_state["step"] = 4
            else:
                st.warning("아직 수학여행 도우미가 '다음 단계로 넘어가도 됩니다'라고 하지 않았어요.")
            st.rerun()

    # 📝 최근 대화 출력
    st.subheader("📌 최근 대화")
    if st.session_state["recent_message"]["user"] or st.session_state["recent_message"]["assistant"]:
        st.write(f"**You:** {st.session_state['recent_message']['user']}")
        st.write(f"**수학여행 도우미:** {st.session_state['recent_message']['assistant']}")
    else:
        st.write("아직 최근 대화가 없습니다.")

    # 💬 누적 대화 출력
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
            st.warning("‘마침’ 버튼을 눌러 수학여행 도우미가 대화를 종료해도 된다고 해야 합니다.")

# 페이지 4: 문제 풀이 과정 출력
# 🔼 기존 import 유지
import pymysql
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from pymongo import MongoClient as PyMongoClient
import streamlit as st

# 📌 환경 변수 로드
load_dotenv()
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
MODEL = 'gpt-4o'

# OpenAI API 설정
client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB 설정
mongo_client = PyMongoClient(st.secrets["MONGO_URI"])
db = mongo_client[st.secrets["MONGO_DB"]]
collection = db[st.secrets["MONGO_COLLECTION"]]
collection_feedback = db[st.secrets["MONGO_COLLECTION_FEEDBACK"]]

# 페이지 기본 설정
st.set_page_config(page_title="수학여행 도우미", page_icon="🧠", layout="wide")

# 🧠 종료 유도 문구 판단 함수
def contains_next_button_instruction(text):
    keywords = ["다음 버튼", "다음 단계로", "[다음]"]
    return any(keyword in text for keyword in keywords)

# ✏️ 초기 프롬프트
initial_prompt = '''(생략: 기존 initial_prompt 내용 그대로 유지)'''

# 세션 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# ... 생략: save_to_mongo(), get_chatgpt_response(), page_1(), page_2() 함수는 기존과 동일

# 🧠 page_3: 대화
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

    user_input = st.text_area("You: ", value=st.session_state["user_input_temp"], key="user_input")

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
            final_input = "궁금한 건 다 물어봤어"
            assistant_response = get_chatgpt_response(final_input)
            st.session_state["recent_message"] = {"user": final_input, "assistant": assistant_response}
            st.session_state["user_input_temp"] = ""

            # ✅ 여기서 종료 안내 여부 판단
            if contains_next_button_instruction(assistant_response):
                st.session_state["step"] = 4
            else:
                st.warning("아직 수학여행 도우미가 '다음 단계로 넘어가도 됩니다'라고 하지 않았어요.")
            st.rerun()

    # 📝 최근 대화 출력
    st.subheader("📌 최근 대화")
    if st.session_state["recent_message"]["user"] or st.session_state["recent_message"]["assistant"]:
        st.write(f"**You:** {st.session_state['recent_message']['user']}")
        st.write(f"**수학여행 도우미:** {st.session_state['recent_message']['assistant']}")
    else:
        st.write("아직 최근 대화가 없습니다.")

    # 💬 누적 대화 출력
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
            st.warning("‘마침’ 버튼을 눌러 수학여행 도우미가 대화를 종료해도 된다고 해야 합니다.")

# 🧠 page_4: 요약 및 피드백
def page_4():
    st.title("수학여행 도우미의 제안")

    if not st.session_state.get("feedback_saved", False):
        st.write("수학여행 도우미가 대화 내용을 정리 중입니다. 잠시만 기다려주세요...")

        # 마지막 assistant 메시지를 그대로 사용
        summary_response = st.session_state["messages"][-1]["content"]
        st.session_state["experiment_plan"] = summary_response

    st.subheader("📋 생성된 피드백")
    st.write(st.session_state["experiment_plan"])

    if "all_data" not in st.session_state:
        st.session_state["all_data"] = []

    if "feedback_saved" not in st.session_state:
        st.session_state["feedback_saved"] = False

    if not st.session_state["feedback_saved"]:
        if save_to_mongo(st.session_state["all_data"] + [{"role": "assistant", "content": st.session_state["experiment_plan"]}]):
            st.session_state["feedback_saved"] = True
        else:
            st.error("저장에 실패했습니다. 다시 시도해주세요.")

    if st.button("이전"):
        st.session_state["step"] = 3
        st.rerun()
    if st.button("다음"):
        st.session_state["step"] = 5
        st.rerun()

# 메인 실행 로직
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










