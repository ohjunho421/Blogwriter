import os
from openai import OpenAI
import streamlit as st

os.environ["OPENAI_API_KEY"] = "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"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


st.title("슈퍼시나리오봇🤖")

keyword = st.text_input("키워드를 입력하세요")

if st.button("생성하기"):
    with st.spinner('생성 중입니다'):
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": keyword,
                },
                        {
                    "role": "system",
                    "content": "입력받은 키워드에 대한 흥미진진한 300자 이내의 시나리오를 작성해줘",
                }
            ],
            model="gpt-4o",
        )
result = chat_completion.choices[0].message.content
st.write(result)
    