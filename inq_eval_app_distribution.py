import streamlit as st
import pymysql
import json

# OpenAI API 키 설정
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# MySQL 연결 함수
def connect_to_db():
    return pymysql.connect(
        host=st.secrets["DB_HOST"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        database=st.secrets["DB_DATABASE"],
        charset='utf8mb4'
    )

# 모든 레코드 가져오기 함수
def fetch_records():
    try:
        db = connect_to_db()
        cursor = db.cursor()
        query = """
        SELECT id, number, name, time 
        FROM qna
        ORDER BY time
        """
        cursor.execute(query)
        records = cursor.fetchall()
        cursor.close()
        db.close()
        return records
    except pymysql.MySQLError as e:
        st.error(f"데이터베이스 오류: {e}")
        return []

# 특정 ID의 레코드 가져오기 함수
def fetch_record_by_id(record_id):
    try:
        db = connect_to_db()
        cursor = db.cursor()
        cursor.execute("SELECT chat FROM qna WHERE id = %s", (record_id,))
        record = cursor.fetchone()
        cursor.close()
        db.close()
        return record
    except pymysql.MySQLError as e:
        st.error(f"데이터베이스 오류: {e}")
        return None

# Streamlit 애플리케이션 시작
st.title("학생의 인공지능 사용 내역(교사용)")

# 비밀번호 입력
password = st.text_input("비밀번호를 입력하세요", type="password")

# 디버깅용 로그 추가
st.write("🛠️ 입력한 비밀번호:", password)
st.write("🔒 설정된 비밀번호 (st.secrets):", st.secrets["PASSWORD"])

if password == st.secrets["PASSWORD"]:
    records = fetch_records()

    if records:
        record_options = [f"{record[1]} ({record[2]}) - {record[3]}" for record in records]
        selected_record = st.selectbox("내역을 선택하세요:", record_options)

        selected_record_id = records[record_options.index(selected_record)][0]

        record = fetch_record_by_id(selected_record_id)
        if record and record[0]:
            try:
                chat = json.loads(record[0])
                st.write("### 학생의 대화 기록")
                for message in chat:
                    if message["role"] == "user":
                        st.write(f"**You:** {message['content']}")
                    elif message["role"] == "assistant":
                        st.write(f"**과학탐구 도우미:** {message['content']}")
            except json.JSONDecodeError:
                st.error("대화 기록을 불러오는 데 실패했습니다. JSON 형식이 잘못되었습니다.")
        else:
            st.warning("선택된 레코드에 대화 기록이 없습니다.")
    else:
        st.warning("데이터베이스에 저장된 내역이 없습니다.")
else:
    st.error("비밀번호가 틀렸습니다.")
