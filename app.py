import os
import openai
import streamlit as st

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = "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"
openai.api_key = os.environ.get("OPENAI_API_KEY")

# Streamlit UI
st.title("블로그 치트키🤖")

keyword = st.text_input("키워드를 입력하세요")

mining = st.subheader("키워드 마이닝을 해봅시다!", divider="gray")
writer = st.text_input("글을 쓰는 사람이나 업체의 경력, 전문성을 기반으로 누구인지 소개해주세요.")
target = st.text_input("글을 읽는 사람은 누구인가요?")
problem = st.text_input("글을 읽는 사람이 겪는 어려움은 무엇인가요?")
struckture = st.subheader("글의 소제목을 지어주세요!", divider="gray")
story1 = st.text_input("글의 첫번째 소제목을 구성해주세요")
story2 = st.text_input("글의 두번째 소제목을 구성해주세요")
story3 = st.text_input("글의 세번째 소제목을 구성해주세요")
story4 = st.text_input("글의 네번째 소제목을 구성해주세요")
story5 = st.text_input("글의 다섯번째 소제목을 구성해주세요")

if st.button("생성하기"):
    with st.spinner('생성 중입니다...'):
        # 조건 구성
        system_message = f"""
        아래 ‘{keyword}’ 주제로 블로그 게시글을 2500자로 작성해주고 아래 조건에 맞춰줘:
        
        1. 타겟에게 이 게시글이 도움이 되는 내용이 있다고 느낄 수 있도록 서론을 글 맨 앞에 공백을 제외하고 최소 500자 작성해줘.
        2. 서론 내용에는 타겟들이 평소 '{keyword}'에 대해 어떤 고민이 있는지 '타겟이 겪는 어려움'을 먼저 공감해주고 글쓴이({writer})의 전문성으로 어떻게 해결할 수 있는지 기대 할 수 있도록 작성해줘.
        3. 서론 맨 앞에 타겟({target})에게 인사말은 작성하지 말아줘.
        4. 서론 말미에는 끝까지 읽어보고 유익한 정보를 얻어가라는 후킹맨트를 넣어줘.
        5. 소주제({story1}, {story2}, {story3}, {story4}, {story5})마다 최소 500자의 글을 작성해줘.
        6. 효과를 설명하는 소주제 내용을 작성할 때 정량적인 지표를 넣어주고 아래 2개의 예시를 사용해서 문맥상 자연스럽게 작성해줘:
            - 1. ~했을 때 평균적으로 ~% 상승하는 효과를 보인 (출처)의 연구자료가 있습니다.
            - 2. (출처)의 연구에 따르면 ~% 상승하는 효과를 보였습니다.
        7. 효과를 설명할 때 너의 견해가 아니라 객관적인 사실을 언급해줘.
        8. '{keyword}'를 본문 내에 적절하게 5번 배치해줘.
        9. '{keyword}'를 띄어쓰기로 구분한 형태소를 본문 내에 최소 15번 최대 20번 배치해줘.
        10. 본문이 신뢰와 전문성을 느낄 수 있도록 어투를 "~습니다.", "~입니다." 어투로 작성해줘.
        11. 영어로 생각하고 한국어로 작성해줘.
        12. 블로그에 복사할 때 보기 좋도록 제목과 함께 섹션을 구분해서 작성해줘.
        """

        # OpenAI API 호출
        chat_completion = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"키워드: {keyword}, 글쓴이: {writer}, 타겟: {target}"}
            ]
        )
        
        # 결과 출력
        result = chat_completion.choices[0].message.content
        st.write(result)
 