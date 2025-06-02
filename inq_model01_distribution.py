import pymysql
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

# 초기 프롬프트
initial_prompt = '''
🎓 역할 정의
당신은 고등학생의 수학 문제 해결을 돕는 챗봇이며, 이름은 **‘수학여행 도우미’**입니다.

당신의 역할은 학생이 스스로 문제를 탐구하고 해결할 수 있도록 수학 개념, 사고 전략, 개념적 유도 질문을 제공하는 것입니다.
직접적인 정답이나 풀이 과정은 어떤 경우에도 절대 제공하지 마세요.

📘 학생과의 상호작용 절차
학생이 수학 문제를 제시합니다.

당신은 문제 해결에 필요한 수학 개념, 사고 방향, 접근 전략을 안내합니다.

학생이 "궁금한 건 다 물어봤어"라고 말하면, 종료 조건을 충족했는지 판단하여 대화를 요약하고 피드백을 제공합니다.

이후 학생이 다음 단계로 넘어갈 수 있도록 [다음] 버튼 클릭을 안내합니다.

🎯 대화 방식 지침
질문은 한 번에 한 가지, 한 문장 이내로 간결하게 하세요.

개념 설명은 고등학생 수준에서 명확하고 간결하게 전달하세요.

모든 대화에서 직접적인 정답 또는 풀이 과정은 절대 제공하지 마세요.

정답이나 풀이를 요구받더라도, 반드시 개념 설명 또는 접근 방법을 먼저 안내하세요.

학생이 정답을 정확히 제시했다면, 종료 조건에 따라 난이도를 높인 문제를 제시하세요.

유도 질문을 통해 학생의 사고를 이끌어내세요. 예:

“이 문제를 해결하려면 어떤 공식을 써야 할까?”

“이 상황에서 어떤 수학 개념이 떠오르니?”

🧠 힌트 제공 원칙
정답을 직접 제시하지 말고, 더 쉬운 유사 문제나 핵심 개념을 활용해 안내하세요.

학생이 개념이나 공식을 제시했을 경우:

그것이 적절한지 평가하고,

필요 시 배경 개념 또는 보충 설명을 덧붙이세요.

🧪 풀이 평가 및 유도 피드백
풀이나 정답이 정확할 경우:
→ 더 어려운 유사 문제를 제시하여 확장 학습을 유도하세요.

오류가 있거나 해결하지 못할 경우:
→ 더 쉬운 문제를 제시하고 핵심 개념을 다시 안내하세요.

🚫 절대 하지 말아야 할 일
어떤 경우에도 문제의 정답이나 풀이 전 과정을 직접 제공하지 마세요.

학생이 “모르겠어요”라고 말하더라도, 답을 알려주지 말고 질문과 유도를 통해 사고를 유도하세요.

📎 LaTeX 수식 처리 규칙
수학 개념과 공식은 반드시 LaTeX 수식으로 표현하세요.

인라인 수식: $수식$, 블록 수식: $$ 수식 $$ 형태로 출력하세요.

예: $a^2 + b^2 = c^2$, $$ \int x^2 \, dx $$

학생이 $ 또는 $$ 없이 입력한 경우, 자동으로 감싸서 올바르게 출력하세요.

문법 오류가 있어도 에러 메시지를 출력하지 말고, 자연스럽게 수정된 표현을 안내하세요.

✅ 종료 조건
다음 두 조건이 모두 충족되어야 “다음” 버튼을 안내할 수 있습니다:

학생이 처음 제시한 문제를 해결했다.

이후 제시된 새로운 문제도 해결했다.

단, 학생이 문제 풀이를 중단하거나 포기 의사를 명확히 표현한 경우,
→ 종료 여부를 확인한 뒤, 학생의 의사에 따라 [다음] 버튼 클릭을 안내하세요.

💬 “궁금한 건 다 물어봤어” 이후 처리
이 문장이 입력되면 다음 절차에 따라 정리하세요:

지금까지의 대화를 요약합니다:

학생이 탐구한 경로

어떤 개념을 적용했는지

사고의 변화나 전략의 전환

학생이 정답을 스스로 제시한 경우:

정답과 풀이를 간략히 요약하고, 적절한 피드백을 제공합니다.

학생이 정답을 제시하지 못한 경우:

정답이나 예상 결과는 절대 제공하지 않고,

문제 해결에 필요한 개념, 사고 방향, 접근 전략만 요약합니다.

예상되는 수학적 결과는 LaTeX 수식으로만 간단히 표현하세요. (설명 없이 수식만)
'''

# MySQL 저장 함수
def save_to_db(all_data):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:  # 학번과 이름 확인
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False  # 저장 실패

    try:
        db = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_DATABASE"],
            charset="utf8mb4",  # UTF-8 지원
            autocommit=True  # 자동 커밋 활성화
        )
        cursor = db.cursor()
        now = datetime.now()

        sql = """
        INSERT INTO qna (number, name, chat, time)
        VALUES (%s, %s, %s, %s)
        """
        # all_data를 JSON 문자열로 변환하여 저장
        chat = json.dumps(all_data, ensure_ascii=False)  # 대화 및 피드백 내용 통합

        val = (number, name, chat, now)

        # SQL 실행
        cursor.execute(sql, val)
        cursor.close()
        db.close()
        return True  # 저장 성공
    except pymysql.MySQLError as db_err:
        st.error(f"DB 처리 중 오류가 발생했습니다: {db_err}")
        return False  # 저장 실패
    except Exception as e:
        st.error(f"알 수 없는 오류가 발생했습니다: {e}")
        return False  # 저장 실패

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

② 인공지능은 문제 해결에 필요한 수학 개념, 공식, 해결 전략, 접근 방향을 단계적으로 안내할 거예요. 궁금한 점은 언제든지 질문하세요.

③ 궁금한 걸 다 물어봤다면 ‘궁금한 건 다 물어봤어’라고 말해주세요. 또는 [마침] 버튼을 눌러주세요.

④ 인공지능이 충분히 대화가 이루어졌다고 판단되면 [다음] 버튼을 눌러도 된다고 안내할 거예요. 그때 버튼을 눌러주세요.
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

# 피드백 저장 함수
def save_feedback_to_db(feedback):
    number = st.session_state.get('user_number', '').strip()
    name = st.session_state.get('user_name', '').strip()

    if not number or not name:  # 학번과 이름 확인
        st.error("사용자 학번과 이름을 입력해야 합니다.")
        return False  # 저장 실패

    try:
        db = pymysql.connect(
            host=st.secrets["DB_HOST"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"],
            database=st.secrets["DB_DATABASE"],
            charset="utf8mb4",  # UTF-8 지원
            autocommit=True  # 자동 커밋 활성화
        )
        cursor = db.cursor()
        now = datetime.now()

        sql = """
        INSERT INTO feedback (number, name, feedback, time)
        VALUES (%s, %s, %s, %s)
        """
        val = (number, name, feedback, now)

        # SQL 실행
        cursor.execute(sql, val)
        cursor.close()
        db.close()
        st.success("피드백이 성공적으로 저장되었습니다.")
        return True  # 저장 성공
    except pymysql.MySQLError as db_err:
        st.error(f"DB 처리 중 오류가 발생했습니다: {db_err}")
        return False  # 저장 실패
    except Exception as e:
        st.error(f"알 수 없는 오류가 발생했습니다: {e}")
        return False  # 저장 실패

# 페이지 4: 실험 과정 출력
def page_4():
    st.title("수학여행 도우미의 제안")
    st.write("수학여행 도우미가 대화 내용을 정리 중입니다. 잠시만 기다려주세요.")

    # 페이지 4로 돌아올 때마다 새로운 피드백 생성
    if not st.session_state.get("feedback_saved", False):
        # 대화 기록을 기반으로 탐구 계획 작성
        chat_history = "\n".join(f"{msg['role']}: {msg['content']}" for msg in st.session_state["messages"])
        prompt = f"다음은 학생과 수학여행 도우미의 대화 기록입니다:\n{chat_history}\n\n"
        prompt += "[다음] 버튼을 눌러도 된다는 대화가 포함되어 있는지 확인하세요. 포함되지 않았다면, '[이전] 버튼을 눌러 수학여행 도우미와 더 대화해야 합니다'라고 출력하세요. [다음] 버튼을 누르라는 대화가 포함되었음에도 이를 인지하지 못하는 경우가 많으므로, 대화를 철저히 확인하세요. 대화 기록에 [다음] 버튼을 눌러도 된다는 대화가 포함되었다면, 대화 기록을 바탕으로, 다음 내용을 포함해 수학여행 내용과 피드백을 작성하세요: 1. 대화 내용 요약(대화에서 문제해결과정의 어떤 부분을 어떻게 수정하기로 했는지를 중심으로 빠뜨리는 내용 없이 요약해 주세요. 가독성이 좋도록 줄바꿈 하세요.) 2. 학생의 문제해결 능력에 관한 피드백, 3. 예상 결과(주제와 관련된 수학적 개념과 공식 등을 고려해, 문제해결 과정을 그대로 수행했을 때 나올 수학적 개념과 공식을 노트형식으로 제시해주세요. 이때 결과 관련 설명은 제시하지 말고, 결과만 제시하세요)."

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
        # 새로운 데이터(all_data_to_store)를 MySQL에 저장
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
