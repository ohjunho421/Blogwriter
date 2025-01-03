import streamlit as st
import openai
import requests
import re
import os
import pyperclip  # 클립보드 복사 모듈
from bs4 import BeautifulSoup  # 구글 학술검색용

# 네이버 API 설정
NAVER_API_ID = st.secrets["api_keys"]["naver_id"]
NAVER_API_SECRET = st.secrets["api_keys"]["naver_secret"]

# OpenAI API 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 세션 초기화
if "introduction" not in st.session_state:
    st.session_state.introduction = None
if "generated_content" not in st.session_state:
    st.session_state.generated_content = []
if "references" not in st.session_state:
    st.session_state.references = []
if "form_data" not in st.session_state:
    st.session_state.form_data = {
        "keyword": "",
        "target": "",
        "problem": "",
        "business_name": "",
        "expertise": "",
        "additional_words": "",
    }
if "recommended_subtopics" not in st.session_state:
    st.session_state.recommended_subtopics = []
if "user_subtopics" not in st.session_state:
    st.session_state.user_subtopics = []
if "selected_subtopics" not in st.session_state:
    st.session_state.selected_subtopics = []
if "content_generated" not in st.session_state:
    st.session_state.content_generated = False

# HTML 태그 제거
def remove_html_tags(text):
    clean = re.compile("<.*?>")
    return re.sub(clean, "", text)

# 소제목 추천
def recommend_subtopics(keyword):
    prompt = f"""
    주제 키워드: {keyword}
    아래 규칙에 따라 소제목 4개를 추천하세요:
    1. 소제목은 짧고 간결해야 합니다.
    2. 키워드와 관련성이 높아야 합니다.
    3. 독자에게 흥미로운 정보를 제공해야 합니다.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "소제목 추천 도우미입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        subtopics = response.choices[0].message.content.strip().split("\n")
        return list(set(topic.strip() for topic in subtopics if topic.strip()))  # 중복 제거
    except Exception as e:
        st.error(f"소제목 추천 오류: {e}")
        return []

# 네이버 API 정량 데이터 검색
def fetch_quantitative_data(section_title, keyword):
    references = []
    try:
        query = f"{keyword} {section_title}"
        url = f"https://openapi.naver.com/v1/search/news.json?query={query}&display=2"
        headers = {
            "X-Naver-Client-Id": NAVER_API_ID,
            "X-Naver-Client-Secret": NAVER_API_SECRET
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            items = response.json().get("items", [])
            for item in items:
                references.append({
                    "title": remove_html_tags(item["title"]),
                    "url": item["link"],
                    "snippet": item["description"],
                    "source": "네이버 뉴스"
                })
        else:
            st.error(f"네이버 API 오류: {response.status_code}")
    except Exception as e:
        st.error(f"네이버 API 검색 오류: {e}")
    return references

# 구글 학술검색 대체 데이터 크롤링
def fetch_google_scholar_data(keyword):
    url = f"https://scholar.google.com/scholar?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    references = []
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        for item in soup.select(".gs_rt")[:2]:
            title = item.text
            link = item.find("a")["href"] if item.find("a") else "링크 없음"
            snippet = item.find_next("div", class_="gs_rs").text if item.find_next("div", class_="gs_rs") else ""
            references.append({"title": title, "url": link, "snippet": snippet, "source": "구글 학술검색"})
    except Exception as e:
        st.error(f"구글 학술검색 크롤링 오류: {e}")
    return references

# 본문 생성 및 참고자료 포함
def generate_section_content_with_references(section_title, keyword, additional_words):
    references = fetch_quantitative_data(section_title, keyword)
    if not references:  # 네이버 API에서 데이터가 없으면 구글 학술검색 사용
        references = fetch_google_scholar_data(keyword)

    ref_summary = "\n".join([
        f"- [{remove_html_tags(ref['title'])}]({ref['url']}) ({ref['source']}): {ref['snippet']}"
        for ref in references
    ]) if references else "참고자료 없음."

    prompt = f"""
    주제 키워드: {keyword}
    소제목: {section_title}
    참고자료: {ref_summary}

    작성 규칙:
    1. 독자가 검색하는 주요 키워드로 구성된 유용한 정보를 제공하세요.
    2. 참고자료를 바탕으로 정량 데이터를 포함하여 신뢰성을 높이세요.
    3. 추가 단어: {additional_words}
    4. 400자 내외로 작성하세요.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "전문적이고 신뢰성 있는 글을 작성하는 블로그 작가입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=700
        )
        content = response.choices[0].message.content
        return content, references
    except Exception as e:
        st.error(f"본문 생성 중 오류: {e}")
        return "본문 생성 오류 발생.", []

# 서론 생성
def generate_introduction(keyword, target, problem, expertise, additional_words):
    prompt = f"""
    주제 키워드: {keyword}
    목표 독자: {target}
    독자의 고민: {problem}
    업체 전문성: {expertise}

    작성 규칙:
    1. 독자가 키워드와 관련하여 겪고있는 어려움을 이블로그에서 제공하는 유용한 정보로 해결 할 수 있다는 기대를 하게 작성해 주세요.
    2. 지금 독자가 겪고 있는 어려움을 공감하고 효과적인 꿀팁이 있다는 내용을 언급하세요.
    3. 추가 단어: {additional_words}
    4. 분량: 300자 내외.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "전문적인 블로그 서론 작성 도우미입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"서론 생성 오류: {e}")
        return None

# 결론 생성
def generate_conclusion(business_name, expertise):
    prompt = f"""
    업체명: {business_name}
    전문성: {expertise}

    작성 규칙:
    1. 글의 주요 내용을 요약하고 전문성을 강조하며 홍보하세요.
    2. 독자에게 신뢰를 주며 서비스를 직접 이용해 어려움을 해결해보라는 문구를 포함하세요.
    3. 300자 내외로 작성하세요.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "전문적인 결론 작성 도우미입니다."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"결론 생성 오류: {e}")
        return None

# 메인 함수
def main():
    st.title("블로그 치트키 - 개선된 기능 포함")
    # 입력 폼, 소제목 추천, 사용자 추가 소제목, 글 생성, 콘텐츠 표시 코드는 위에서 다뤘던 부분을 그대로 가져옵니다.

if __name__ == "__main__":
    main()

    # 입력 폼
    with st.form("input_form"):
        st.subheader("📌 키워드와 독자 설정")
        keyword = st.text_input("주제 키워드", placeholder="예: 다이어트")
        target = st.text_input("목표 독자", placeholder="예: 30대 직장인")
        problem = st.text_input("독자의 고민/니즈", placeholder="예: 시간 부족")
        business_name = st.text_input("업체명", placeholder="예: 건강한 생활")
        expertise = st.text_input("업체 전문성", placeholder="예: 10년 경력과 고객 만족도 1위")
        additional_words = st.text_input("추가 단어들 (띄어쓰기 구분)", placeholder="예: 전문가 검증, 효율성")
        submit = st.form_submit_button("소제목 추천")

        if submit:
            st.session_state.form_data.update({
                "keyword": keyword,
                "target": target,
                "problem": problem,
                "business_name": business_name,
                "expertise": expertise,
                "additional_words": additional_words
            })
            st.session_state.recommended_subtopics = recommend_subtopics(keyword)
            st.session_state.content_generated = False

    # 추천된 소제목 체크박스
    if st.session_state.recommended_subtopics:
        st.subheader("추천된 소제목")
        for subtopic in st.session_state.recommended_subtopics:
            if st.checkbox(subtopic, key=f"rec_{subtopic}"):
                if len(st.session_state.selected_subtopics) < 4:
                    if subtopic not in st.session_state.selected_subtopics:
                        st.session_state.selected_subtopics.append(subtopic)
                else:
                    st.warning("최대 4개의 소제목만 선택 가능합니다!")

    # 사용자 추가 소제목
    st.subheader("사용자 추가 소제목")
    for i, subtopic in enumerate(st.session_state.user_subtopics):
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.checkbox("", key=f"user_cb_{i}"):
                if len(st.session_state.selected_subtopics) < 4:
                    if subtopic not in st.session_state.selected_subtopics:
                        st.session_state.selected_subtopics.append(subtopic)
                else:
                    st.warning("최대 4개의 소제목만 선택 가능합니다!")
        with col2:
            updated_text = st.text_input(f"추가 소제목 {i+1}", value=subtopic, key=f"user_input_{i}")
            if updated_text != subtopic:
                st.session_state.user_subtopics[i] = updated_text

    if st.button("소제목 추가"):
        if len(st.session_state.user_subtopics) < 4:  # 최대 4개 제한
            st.session_state.user_subtopics.append("")
        else:
            st.warning("사용자 추가 소제목은 최대 4개까지 가능합니다.")

    # 글 생성
    if st.button("글 생성 시작"):
        with st.spinner("글을 생성 중입니다..."):
            st.session_state.introduction = generate_introduction(
                st.session_state.form_data["keyword"],
                st.session_state.form_data["target"],
                st.session_state.form_data["problem"],
                st.session_state.form_data["expertise"],
                st.session_state.form_data["additional_words"]
            )
            st.session_state.generated_content = []
            st.session_state.references = []

            for subtopic in st.session_state.selected_subtopics:
                content, references = generate_section_content_with_references(
                    subtopic,
                    st.session_state.form_data["keyword"],
                    st.session_state.form_data["additional_words"]
                )
                st.session_state.generated_content.append(content)
                st.session_state.references.append(references)

            st.session_state.content_generated = True

    # 생성된 콘텐츠 표시
    if st.session_state.content_generated:
        st.subheader("## 서론")
        st.markdown(st.session_state.introduction or "서론 생성 중 오류 발생.")

        st.subheader("## 본문")
        for idx, (content, references) in enumerate(zip(st.session_state.generated_content, st.session_state.references)):
            st.markdown(f"### {st.session_state.selected_subtopics[idx]}")
            st.markdown(content)
            if references:
                st.markdown("#### 참고자료")
                for ref in references:
                    st.markdown(f"- [{remove_html_tags(ref['title'])}]({ref['url']}) ({ref['source']})")

        st.subheader("## 결론")
        conclusion = generate_conclusion(
            st.session_state.form_data["business_name"],
            st.session_state.form_data["expertise"]
        )
        st.markdown(conclusion or "결론 생성 중 오류 발생.")

        # 하단 작업 버튼
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("📋 클립보드 복사"):
                full_text = (
                    f"## 서론\n\n{st.session_state.introduction}\n\n"
                    + "\n\n".join(st.session_state.generated_content)
                    + f"\n\n## 결론\n\n{conclusion}"
                )
                try:
                    pyperclip.copy(full_text)
                    st.toast("✅ 클립보드에 복사되었습니다!")
                except Exception as e:
                    st.error(f"복사 오류: {e}")
        with col2:
            if st.button("🔄 모두 초기화"):
                st.write(
                    '<script>location.reload()</script>',
                    unsafe_allow_html=True
                )
        with col3:
            if st.button("📚 참고자료 보기"):
                st.subheader("## 참고자료")
                for idx, refs in enumerate(st.session_state.references):
                    st.markdown(f"### {st.session_state.selected_subtopics[idx]} 참고자료")
                    for ref in refs:
                        st.markdown(f"- [{remove_html_tags(ref['title'])}]({ref['url']}) ({ref['source']})")