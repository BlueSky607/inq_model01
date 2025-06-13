import streamlit as st
from pymongo import MongoClient
from bson.objectid import ObjectId
import json

# OpenAI API 키 설정
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# MongoDB 연결 함수
@st.cache_resource
def connect_to_mongo():
    client = MongoClient(st.secrets["MONGO_URI"])
    db = client[st.secrets["DB_DATABASE"]]  # 예: "qna_db"
    return db["qna"]  # 컬렉션 이름: "qna"

# 모든 레코드 가져오기
def fetch_records():
    try:
        collection = connect_to_mongo()
        records = list(collection.find({}, {"number": 1, "name": 1, "time": 1}))
        return records
    except Exception as e:
        st.error(f"MongoDB 오류: {e}")
        return []

# 특정 ID의 레코드 가져오기
def fetch_record_by_id(record_id):
    try:
        collection = connect_to_mongo()
        record = collection.find_one({"_id": ObjectId(record_id)}, {"chat": 1})
        return record
    except Exception as e:
        st.error(f"MongoDB 오류: {e}")
        return None

# Streamlit 앱 시작
st.title("학생의 인공지능 사용 내역(교사용)")

# 비밀번호 입력
password = st.text_input("비밀번호를 입력하세요", type="password")

# 디버깅용 로그 (선택적 출력)
# st.write("🛠️ 입력한 비밀번호:", password)
# st.write("🔒 설정된 비밀번호 (secrets):", st.secrets["PASSWORD"])

if password == st.secrets["PASSWORD"]:
    records = fetch_records()

    if records:
        record_options = [
            f"{record['number']} ({record['name']}) - {record['time']}" for record in records
        ]
        selected_record = st.selectbox("내역을 선택하세요:", record_options)

        selected_record_id = records[record_options.index(selected_record)]["_id"]

        record = fetch_record_by_id(selected_record_id)
        if record and "chat" in record:
            try:
                chat = record["chat"]
                # chat이 문자열이면 파싱
                if isinstance(chat, str):
                    chat = json.loads(chat)

                st.write("### 학생의 대화 기록")
                for message in chat:
                    if message["role"] == "user":
                        st.write(f"**You:** {message['content']}")
                    elif message["role"] == "assistant":
                        st.write(f"**수학여행 도우미:** {message['content']}")
            except json.JSONDecodeError:
                st.error("대화 기록을 불러오는 데 실패했습니다. JSON 형식이 잘못되었습니다.")
        else:
            st.warning("선택된 레코드에 대화 기록이 없습니다.")
    else:
        st.warning("MongoDB에 저장된 내역이 없습니다.")
else:
    st.error("비밀번호가 틀렸습니다.")

