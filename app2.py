import streamlit as st
import openai
import pyperclip  # 클립보드 복사 모듈
import requests
from bs4 import BeautifulSoup
import re
import os

# OpenAI API 키 설정
openai.api_key = os.getenv('OPENAI_API_KEY')

# 세션 상태 초기화
if 'introduction' not in st.session_state:
    st.session_state.introduction = None
if 'generated_content' not in st.session_state:
    st.session_state.generated_content = []
if 'references' not in st.session_state:
    st.session_state.references = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {
        'keyword': '',
        'target': '',
        'problem': '',
        'writer': '',
        'stories': []
    }
if 'content_generated' not in st.session_state:
    st.session_state.content_generated = False
if 'show_references' not in st.session_state:
    st.session_state.show_references = False

# 키워드 형태소 분리 함수
def split_keyword_into_morphemes(keyword):
    return re.split(r"[,\s\-]+", keyword)  # 공백, 쉼표, 하이픈으로 분리

# 키워드 사용 횟수 제한 함수
def limit_keyword_usage(text, keywords, max_count=20):
    for keyword in keywords:
        matches = list(re.finditer(fr"\b{re.escape(keyword)}\b", text, re.IGNORECASE))
        if len(matches) > max_count:
            for match in matches[max_count:]:
                text = text[:match.start()] + text[match.end():]
    return text

# 서론 생성 함수
def generate_introduction(keyword, target, problem, writer):
    try:
        prompt = f"""
        주제 키워드: {keyword}
        목표 독자: {target}
        독자의 고민: {problem}
        작성자 관점: {writer}

        서론 작성 규칙:
        1. 독자 공감, 전문성 제시, 해결책 암시로 구성.
        2. 분량: 370자 내외.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "독자들의 어려움을 공감하여 전문적인 해결책과 신뢰성있는 정보를 제공할 수 있는 한국어 표현이 자연스러운 블로그 작가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        introduction = response.choices[0].message.content
        keywords = split_keyword_into_morphemes(keyword)
        return limit_keyword_usage(introduction, keywords)
    except Exception as e:
        st.error(f"서론 생성 중 오류: {str(e)}")
        return None

# 본문 생성 함수
def generate_section_content(section_title, keyword, target_length):
    try:
        prompt = f"""
        주제 키워드: {keyword}
        소제목: {section_title}
        내용 작성 규칙:
        1. 분량: {target_length}자 내외.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "독자들의 어려움을 공감하여 전문적인 해결책과 신뢰성있는 정보를 제공할 수 있는 한국어 표현이 자연스러운 블로그 작가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500,
            request_timeout=30
        )
        content = response.choices[0].message.content if response.choices else None
        if content:
            keywords = split_keyword_into_morphemes(keyword)
            return limit_keyword_usage(content, keywords)
        return content
    except Exception as e:
        st.error(f"'{section_title}' 섹션 생성 중 오류: {str(e)}")
        return None

# 참고자료 데이터 가져오기 함수
def fetch_quantitative_data(section_title, keyword):
    references = []
    try:
        query = f"{keyword} {section_title}"
        search_url = f"https://search.naver.com/search.naver?query={query}&where=news"
        response = requests.get(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        for item in soup.select('.news_area')[:2]:
            title_elem = item.select_one('.news_tit')
            if title_elem:
                references.append({
                    'title': title_elem.get('title', '').strip(),
                    'url': title_elem['href'],
                    'source': '네이버 뉴스'
                })
    except Exception as e:
        st.error(f"뉴스 검색 중 오류: {str(e)}")
    return references

# 참고자료와 정량 지표 본문에 통합
def enhance_section_with_references(section_title, keyword, existing_text, references):
    if not references:
        st.warning("관련된 정량 데이터를 찾지 못했습니다.")
        return existing_text
    try:
        ref_summary = "\n".join([
            f"- [{ref['title']}]({ref['url']}) ({ref['source']})" for ref in references
        ])
        prompt = f"""
        주제: {keyword}
        소제목: {section_title}
        기존 내용: {existing_text}

        참고자료:
        {ref_summary}

        위 참고자료중 정량적인 지표를 활용해 기존 텍스트를 보강해주세요.
        """
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "전문적이고 신뢰성 있는 글을 작성하는 작가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        updated_text = response.choices[0].message.content
        keywords = split_keyword_into_morphemes(keyword)
        return limit_keyword_usage(updated_text, keywords)
    except Exception as e:
        st.error(f"본문 보강 중 오류: {str(e)}")
        return existing_text

# 클립보드 복사 함수
def copy_to_clipboard():
    try:
        full_text = "\n\n".join(
            [st.session_state.introduction] + st.session_state.generated_content
        )
        pyperclip.copy(full_text)
        st.toast("✅ 클립보드에 복사되었습니다!")
    except Exception as e:
        st.error(f"클립보드 복사 중 오류: {str(e)}")

# 다시쓰기 함수
def reset_session_state():
    st.session_state.introduction = None
    st.session_state.generated_content = []
    st.session_state.references = []
    st.session_state.form_data = {
        'keyword': '',
        'target': '',
        'problem': '',
        'writer': '',
        'stories': []
    }
    st.session_state.content_generated = False
    st.session_state.show_references = False

# 참고자료 보기 함수
def display_references():
    st.subheader("📚 참고자료")
    if st.session_state.references:
        for ref in st.session_state.references:
            st.markdown(f"- [{ref['title']}]({ref['url']}) ({ref['source']})")
    else:
        st.info("참고자료가 없습니다.")

# 메인 함수
def main():
    st.title("블로그치트키 v2")

    # 입력 폼
    with st.form(key='input_form'):
        st.subheader("📌 키워드와 독자 설정")
        col1, col2 = st.columns(2)
        with col1:
            keyword = st.text_input("주제 키워드", placeholder="예: 다이어트, 재테크 등")
            target = st.text_input("목표 독자", placeholder="예: 30대 직장인")
        with col2:
            problem = st.text_input("독자의 고민/니즈", placeholder="예: 시간 부족")
            writer = st.text_input("작성자 관점", placeholder="예: 전문가, 경험 많은 사람")

        st.subheader("📝 글 구조 설계")
        stories = []
        for i in range(5):
            story = st.text_input(f"{i+1}번째 소제목", key=f'story{i+1}')
            if story.strip():
                stories.append(story)

        submit = st.form_submit_button("✨ 글 생성하기")
        if submit and keyword and stories:
            st.session_state.form_data = {
                'keyword': keyword,
                'target': target,
                'problem': problem,
                'writer': writer,
                'stories': stories
            }
            st.session_state.content_generated = True

    # 콘텐츠 생성
    if st.session_state.content_generated and not st.session_state.introduction:
        with st.spinner("콘텐츠를 생성하고 있습니다..."):
            form_data = st.session_state.form_data
            st.session_state.introduction = generate_introduction(
                keyword=form_data['keyword'],
                target=form_data['target'],
                problem=form_data['problem'],
                writer=form_data['writer']
            )
            total_length = 1850 // len(form_data['stories'])
            st.session_state.generated_content = [
                generate_section_content(title, form_data['keyword'], total_length)
                for title in form_data['stories']
            ]

    # 생성된 콘텐츠 표시 (입력 폼 바로 아래)
    if st.session_state.content_generated:
        st.subheader("## 서론")
        st.markdown(st.session_state.introduction)

        st.subheader("## 본문")
        for i, content in enumerate(st.session_state.generated_content):
            st.markdown(f"### {st.session_state.form_data['stories'][i]}")
            st.markdown(content)

            # 정량 데이터 추가 및 다시쓰기
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"정량 데이터 추가 ({i+1})", key=f"add_ref_{i}"):
                    references = fetch_quantitative_data(
                        st.session_state.form_data['stories'][i],
                        st.session_state.form_data['keyword']
                    )
                    updated_text = enhance_section_with_references(
                        st.session_state.form_data['stories'][i],
                        st.session_state.form_data['keyword'],
                        content,
                        references
                    )
                    st.session_state.generated_content[i] = updated_text
                    st.session_state.references.extend(references)
            with col2:
                if st.button(f"다시쓰기 ({i+1})", key=f"rewrite_{i}"):
                    updated_text = generate_section_content(
                        st.session_state.form_data['stories'][i],
                        st.session_state.form_data['keyword'],
                        370
                    )
                    if updated_text:
                        st.session_state.generated_content[i] = updated_text

        # 하단 작업 버튼 (한 열에 배치)
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("📋 복사하기"):
                copy_to_clipboard()
        with col2:
            if st.button("📚 참고자료 보기"):
                st.session_state.show_references = True
        with col3:
            if st.button("🔄 다시쓰기 (모두 초기화)"):
                reset_session_state()

    # 참고자료 표시 (맨 하단)
    if st.session_state.show_references:
        display_references()

if __name__ == "__main__":
    main()