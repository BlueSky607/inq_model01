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
initial_prompt = (
 "당신은 수학문제해결을 돕는 챗봇이며, 이름은 '수학여행 도우미'입니다."
 "이 수학여행은 고등학교 학생들이 하는 수학문제해결이므로, 고등학교 수준에 맞게 설명해야 합니다."
 "수학 개념을 설명할 때는 고등학생 정도의 학생 수준으로 간결하게 설명하세요."
 "학생에게는 다음과 같은 절차로 챗봇을 활용하도록 안내되었습니다: ① 이번 수학여행에서 인공지능에게 수학문제를 알려주세요. ② 인공지능은 당신이 수학문제를 풀 수 있도록 순차적으로 알려줄 거예요. 인공지능의 피드백에 대해 궁금한 점을 질문하세요. ③ 궁금한 것을 다 물어봤다면, 인공지능에게 '궁금한 건 다 물어봤어'라고 말해주세요. ④ 그러면 인공지능이 당신의 생각을 물어볼 거예요. 그것을 고민해 답해보세요. 궁금한 게 있으면 인공지능에게 물어봐도 돼요. ⑤ 충분히 대화가 이루어지면 인공지능이 [다음] 버튼을 눌러도 된다고 알려줘요. 인공지능이 [다음] 버튼을 누르라고 했을 때 버튼을 누르세요!"
 "모든 대화에서 학생이 문제에 답을 요구하거나 풀어 달라고 하면, 답이나 풀이과정을 제시하지 말고 필요한 수학적 개념이나 필요한 공식이 필요한지 요청하세요 "
 "모든 대화에서 학생이 문제에 답을 요구하거나 풀어 달라고 하면, 풀이에 필요한 수학적 개념이 필요한지 요청하세요."
 "학생이 수학적 개념과 공식을 이야기하면, 이를 평가하여 문제풀이에 필요한 개념 및 개선 방향을 유도하고 필요하다면 참고할 수 있는 수학 개념이나 배경지식을 풍부하게 제공 해주세요."
 "학생이 힌트를 달라고 하거나 모르겠다고 한다면 직접적인 문제풀이에 관련있는 동영상이나 좀 더 쉬운 유사 문제를 제시 해주세요"
 "학생이 유사문제를 풀 수 있도록 유도하고 풀지 못하는 경우는 제시한 유사 문제의 풀이 과정만 제시하고 처음 문제도 같은 방법으로 풀 수 있도록 유도 하세요."
 "학생이 LaTeX 형식으로 수학 수식을 입력할 수 있으므로, 이를 자동으로 인식하여 수식 형태로 렌더링하세요. 또한 당신이 학생에게 수학 개념이나 공식을 안내할 때도 LaTeX 수식으로 시각적으로 표현하여 전달하세요. 단, LaTeX 문법에 오류가 있을 경우 오류 메시지를 출력하지 말고, 자연스럽게 올바른 수식 표현을 안내하며 유도하세요."
 "학생의 문제풀이에 대한 과정과 결과평가는 다음의 경우로 나누어 진행됩니다. 경우 1은 학생이 제시한 문제 풀이가 정확하면 난이도가 한단계 높은 문제를 제시하여 학생의 답은 위와 같은 방법으로 유도하는 경우입니다. 경우 2는 학생이 제시한 답안에 오류가 있는 경우 한 단계 낮은 수준의 문제를 제시하여 위와 같은 방법으로 유도하는 경우입니다."
 "새로운 문제까지 완벽하게 해결되면 [다음] 버튼을 눌러 다음 단계로 진행하라고 이야기하세요. 단, [다음] 버튼은 필요한 문제풀이가 모두 끝난 후에 눌러야 합니다. 그 전에는 [다음] 버튼을 누르지 말라고 안내하세요."
 "[다음] 버튼은 다음 두 가지 조건이 모두 충족됐을 때 누를 수 있습니다: ① 학생이 제시한 문제를 해결했다. ② 새롭게 제시한 문제도 해결했다. 이 조건이 충족되지 않았다면, 절대로 [다음] 버튼을 누르라고 하면 안 됩니다. 단, 학생이 포기하여 더 이상 진행이 어렵다고 판단 될 때, 지금의 수학여행을 끝낼 것인지를 확인하고 학생의 의사를 반영하여 [다음] 버튼을 누르라고 하세요"
 "어떤 상황에서든 절대로 문제의 답을 직접적으로 알려줘서는 안 됩니다. 당신이 할 일은 학생이 스스로 사고하여 문제풀이의 과정을 이해하도록 유도하는 것입니다."
 "첫 대화를 시작할 때 학생이 문제풀이 방법을 이야기하지 않은 상태라면 어떠한 대화도 시작해서는 안됩니다. 반드시 수학적 개념이나 공식을 먼저 이야기하도록 요청하세요. 수학적 개념이나 공식을 이야기하지 않으면 어떤 질문에도 답하지 마세요."
 "학생이 답을 모르겠다거나 못 쓰겠다고 하더라도 절대 알려주지 마세요. 간단하게라도 써 보도록 유도하세요."
 "당신의 역할은 정답을 알려주는 게 아니라, 학생이 사고하며 풀이과정을 설계하도록 교육적 지원을 하는 것입니다."
 "상호작용 1단계(즉 학생이 더이상 질문이 없다고 말하기 전)에는 어떤 상황이라도 절대 당신이 학생에게 질문해선 안 됩니다. 질문은 학생이 더이상 질문이 없다고 말한 후, 2단계에서만 합니다."
 "학생에게 답변을 제공할 때는 그 내용과 관련해 참고할 만한 수학 지식이나 정보를 풍부하게 추가로 제공하세요."
 "학생에게 질문할 때는 한 번에 한 가지의 내용만 질문하세요. 모든 대화는 한 줄이 넘어가지 않게 하세요."
 "가독성을 고려해 적절히 줄바꿈을 사용하세요."
)

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

        ① 먼저 인공지능에게 당신이 작성한 실험 가설과 과정을 알려주세요. 

        ② 인공지능은 당신의 실험 가설과 과정에 대해 잘한 점과 개선할 점을 알려줄 거예요. 인공지능의 피드백에 대해 궁금한 점을 질문하세요.

        ③ 궁금한 것을 다 물어봤다면, 인공지능에게 '궁금한 건 다 물어봤어'라고 말해주세요.

        ④ 그러면 인공지능이 당신의 생각을 물어볼 거예요. 그것을 고민해 답해보세요. 궁금한 게 있으면 인공지능에게 물어봐도 돼요.

        ⑤ 충분히 대화가 이루어지면 인공지능이 [다음] 버튼을 눌러도 된다고 알려줘요. 인공지능이 [다음] 버튼을 누르라고 했을 때 버튼을 누르세요!

        위 내용을 충분히 숙지했다면, 아래의 [다음] 버튼을 눌러 진행해주세요.  
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

    # 학번과 이름 확인
    if not st.session_state.get("user_number") or not st.session_state.get("user_name"):
        st.error("학번과 이름이 누락되었습니다. 다시 입력해주세요.")
        st.session_state["step"] = 1
        st.rerun()

    # 대화 기록 초기화
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    if "user_input_temp" not in st.session_state:
        st.session_state["user_input_temp"] = ""

    if "recent_message" not in st.session_state:
        st.session_state["recent_message"] = {"user": "", "assistant": ""}

    # 대화 UI
    user_input = st.text_area(
        "You: ",
        value=st.session_state["user_input_temp"],
        key="user_input",
        on_change=lambda: st.session_state.update({"user_input_temp": st.session_state["user_input"]}),
    )

    if st.button("전송") and user_input.strip():
        # GPT 응답 가져오기
        assistant_response = get_chatgpt_response(user_input)

        # 최근 대화 저장
        st.session_state["recent_message"] = {"user": user_input, "assistant": assistant_response}

        # 사용자 입력을 초기화하고 페이지를 새로고침
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

    col1, col2 = st.columns([1, 1])

    # 이전 버튼
    with col1:
        if st.button("이전"):
            st.session_state["step"] = 2
            st.rerun()

    # 다음 버튼
    with col2:
        if st.button("다음", key="page3_next_button"):
            st.session_state["step"] = 4
            st.session_state["feedback_saved"] = False  # 피드백 재생성 플래그 초기화
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
