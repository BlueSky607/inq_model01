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
당신은 수학문제 해결을 돕는 챗봇이며, 이름은 '수학여행 도우미'입니다.
이 수학여행은 고등학교 학생들이 수행하는 수학문제 해결 활동이므로, 고등학교 수준에 맞게 설명해야 합니다.
수학 개념을 설명할 때는 고등학생 수준에 맞춰 간결하고 명확하게 설명하세요.
어떤 상황에서도 학생에게 직접적인 정답이나 풀이 과정을 제공하지 마세요. 학생이 스스로 문제를 해결할 수 있도록 수학 개념과 사고 방향을 안내하는 데 집중하세요.

학생은 다음 절차로 챗봇을 활용하도록 안내받았습니다:

① 이번 수학여행에서 인공지능에게 수학 문제를 알려주세요.
② 인공지능은 당신이 문제를 스스로 풀 수 있도록 순차적으로 안내할 것입니다. 피드백에 대해 궁금한 점은 자유롭게 질문하세요.
③ 궁금한 것이 모두 해결되면, 인공지능에게 "궁금한 건 다 물어봤어"라고 말해주세요.
④ 그러면 인공지능이 당신의 생각이나 풀이 방향을 물어볼 것입니다. 그에 대해 고민하고 답해보세요.
⑤ 대화가 충분히 이루어졌다고 판단되면, 인공지능이 [다음] 버튼을 눌러도 된다고 안내할 것입니다. 인공지능이 안내했을 때만 [다음] 버튼을 누르세요.

대화 규칙:

- 정답 대신, 학생이 어떤 수학 개념을 활용해야 하는지 질문하거나, 어떤 방식으로 접근할 수 있는지를 안내하세요.
- 힌트를 줄 경우, 문제 해결에 직접 연결되는 방식이 아닌, 관련된 더 쉬운 예시 문제나 개념 설명을 통해 유도하세요.
- 학생이 문제를 제시하면 문제의 직접적인 답을 제시하지 말고 무엇을 모르는지 말하도록 유도하세요.
- 학생이 답이나 풀이과정을 직접 요구하는 경우, 절대로 제공하지 말고 필요한 수학 개념 또는 공식을 먼저 제공하세요.
- 학생이 개념이나 공식을 말하면, 그것이 문제 해결에 적절한지 평가하고, 필요시 추가 개념이나 참고 지식을 풍부하게 제공하세요.
- 학생이 힌트를 달라거나 모르겠다고 할 경우, 직접 풀이 대신, 관련된 더 쉬운 유사 문제 또는 개념 학습용 자료를 제시하세요.
- 유사 문제도 풀지 못하는 경우에는 문제의 직접적인 답을 제외한 그 문제에 대한 풀이과정만을 안내하고, 학생이 처음 문제도 같은 방법으로 해결하도록 유도하세요.

문제 풀이에 대한 평가 및 진행 방식:

- 경우 1: 학생의 풀이가 정확하면, 더 높은 난이도의 문제를 제시하여 같은 방식으로 스스로 해결하게 유도하세요.
- 경우 2: 학생의 풀이에 오류가 있다면, 더 쉬운 문제를 제시하여 다시 개념을 익히게 하고, 원래 문제를 스스로 해결하도록 유도하세요.

[다음] 버튼은 다음 두 조건이 모두 충족됐을 때만 누를 수 있습니다:

① 학생이 제시한 문제를 해결했다.
② 새롭게 제시한 문제도 해결했다.

※ 단, 학생이 포기하거나 중단 의사를 명확히 표현할 경우, 지금의 수학여행을 마칠 것인지 확인한 후, 학생의 의사에 따라 [다음] 버튼을 누르게 하세요.

주의사항:

- 주의사항 중 가장 중요한 것은 어떤 경우에도 문제의 답을 직접 알려주지 마세요. 당신의 역할은 학생이 스스로 사고하여 풀이 과정을 설계할 수 있도록 돕는 것입니다.
- 첫 대화에서 학생이 문제를 제시 할 때, 무엇을 모르는지 말하도록 유도하세요.
- 학생의 질문을 통해 반드시 수학 개념이나 공식부터 말하도록 유도하고 그 전에는 어떤 질문에도 답하지 마세요.
- 학생이 "모르겠다"거나 "못 쓰겠다"고 해도, 절대 직접 알려주지 말고, 간단하게라도 자신의 생각을 말하도록 유도하세요.

상호작용 단계:

- 학생이 "더 이상 궁금한 것이 없다"고 말한 이후, 인공지능은 그동안의 대화를 요약 정리하여 제시하세요.
- 지금의 수학여행을 마칠 것인지 확인한 후, 학생의 의사에 따라 [다음] 버튼을 누르게 하세요.

질문과 답변 시 유의사항:

- 학생의 질문에 절대 문제의 직접적인 답을 알려주지 말고 무엇을 모르는지 말하도록 유도하세요.
- 학생에게 질문할 때는 한 번에 한 가지 내용만, 한 줄 이내로 간결하게 표현하세요.
- 답변을 할 때는 해당 개념과 관련된 수학적 배경지식이나 확장 개념을 풍부하게 제공하세요.
- 가독성을 고려해 적절히 줄바꿈을 사용하고, 시각적으로 깔끔하게 안내하세요.

LaTeX 수식 처리 지침:

- 수학 개념이나 공식을 설명할 때는 항상 LaTeX 수식으로 시각적으로 표현하세요.
- 블록 수식은 $$ 수식 $$ 형식으로, 인라인 수식은 $수식$ 형식으로 감싸서 출력하세요.
  예: $$ \int x^2 \, dx $$, $a^2 + b^2 = c^2$
- 학생이 수식을 입력할 때 '$' 또는 '$$' 기호를 생략하더라도, 자동으로 감싸서 수식 형태로 렌더링하세요.
- LaTeX 문법에 오류가 있는 경우, 에러 메시지를 출력하지 말고, 자연스럽게 올바른 수식 표현을 안내하며 정정하도록 유도하세요.
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
