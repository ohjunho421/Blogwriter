import streamlit as st
from transformers import AutoTokenizer, AutoModelForCausalLM

# KoGPT 모델 로드
tokenizer = AutoTokenizer.from_pretrained("kakaobrain/kogpt")
model = AutoModelForCausalLM.from_pretrained("kakaobrain/kogpt")

# Streamlit UI
st.title("블로그 자동 작성 서비스")

# 키워드 입력
keyword = st.text_input("키워드를 입력하세요:", "")

# 추천 소제목
if keyword:
    st.write("### 추천 소제목")
    suggested_topics = [
        f"{keyword}의 정의", 
        f"{keyword}의 장점", 
        f"{keyword}의 활용 사례", 
        f"{keyword}와 관련된 최신 트렌드"
    ]
    
    selected_topics = []
    
    # 추천 소제목 체크박스
    for i, topic in enumerate(suggested_topics):
        if st.checkbox(topic, key=f"recommended_{i}"):
            selected_topics.append(topic)
    
    # 사용자 추가 소제목 입력
    st.write("### 추가 소제목")
    
    # 동적으로 텍스트 필드를 추가할 리스트
    user_topics = []
    
    # 세션 상태로 텍스트 필드 관리
    if "user_topic_count" not in st.session_state:
        st.session_state.user_topic_count = 1  # 초기 1개 필드
    
    # 기존 필드 출력
    for i in range(st.session_state.user_topic_count):
        user_topic = st.text_input(f"소제목 {i+1}:", key=f"user_topic_{i}")
        if user_topic:
            user_topics.append(user_topic)
    
    # 텍스트 필드 추가 버튼
    if st.button("소제목 추가"):
        st.session_state.user_topic_count += 1
    
    # 추천 소제목과 사용자 추가 소제목에서 최대 4개 선택
    st.write("### 최종 선택")
    all_topics = suggested_topics + user_topics
    selected_final_topics = []
    
    for i, topic in enumerate(all_topics):
        if st.checkbox(topic, key=f"final_{i}"):
            selected_final_topics.append(topic)
    
    # 최대 4개 제한 경고
    if len(selected_final_topics) > 4:
        st.warning("최대 4개의 소제목만 선택할 수 있습니다. 선택을 줄여주세요.")
    
    # 글 생성 버튼
    if st.button("글 생성"):
        if len(selected_final_topics) == 0:
            st.error("최소 1개의 소제목을 선택해야 합니다.")
        elif len(selected_final_topics) > 4:
            st.error("소제목은 최대 4개까지만 선택 가능합니다.")
        else:
            st.write("### 생성된 글")
            # 프롬프트 생성
            prompt = f"키워드 '{keyword}'를 중심으로 다음 소제목에 따라 글을 작성하세요:\n"
            prompt += "\n".join([f"- {topic}" for topic in selected_final_topics])
            prompt += "\n\n글자 수는 2000자를 초과하지 않도록 제한합니다."
            
            # KoGPT로 글 생성
            inputs = tokenizer(prompt, return_tensors="pt")
            outputs = model.generate(inputs["input_ids"], max_length=512, temperature=0.7)
            result = tokenizer.decode(outputs[0], skip_special_tokens=True)
            st.text_area("생성된 글:", result, height=300)