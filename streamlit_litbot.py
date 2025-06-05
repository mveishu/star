# -*- coding: utf-8 -*-
import streamlit as st
from io import BytesIO
from email.message import EmailMessage
import smtplib
import requests
import time

def check_inappropriate_content(user_message):
    """부적절한 발언 감지 (문맥 고려)"""
    
    # 명확히 부적절한 표현들만
    clearly_inappropriate = [
        "ㅂㅅ", "병신", "미친놈", "미친년",
        "꺼져", "씨발", "존나", "개새끼"
    ]
    
    # 차별적 맥락에서 사용될 때만 문제가 되는 표현들 (더 정교하게 체크)
    context_sensitive = {
        "여자는": ["원래", "다", "항상", "역시"],  # "여자는 원래 그래" 같은 표현
        "남자는": ["원래", "다", "항상", "역시"],  # "남자는 다 그래" 같은 표현
        "죽어": ["버려", "라", "야지"],           # "죽어버려" 같은 표현 (소설 인용은 괜찮)
    }
    
    # 명확히 부적절한 표현 체크
    for keyword in clearly_inappropriate:
        if keyword in user_message:
            return True, keyword
    
    # 맥락을 고려한 체크
    for main_word, trigger_words in context_sensitive.items():
        if main_word in user_message:
            for trigger in trigger_words:
                if trigger in user_message:
                    return True, main_word + " " + trigger
    
    return False, None

def create_feedback_message(inappropriate_expression):
    """부적절한 발언에 대한 피드백 메시지 생성"""
    return f"어? 지금 '{inappropriate_expression}' 표현이 좀 그런 것 같아. 우리 서로 존중하면서 문학 이야기하자. 다시 말해줄래?"

def check_off_topic(user_message):
    """소설 <별> 주제 이탈 감지"""
    
    # 소설 관련 키워드들
    novel_keywords = [
        "소년", "누이", "어머니", "별", "과수노파", "죽음", "가족", 
        "소설", "작품", "황순원", "이야기", "인물", "주인공"
    ]
    
    # 완전히 다른 주제들
    off_topic_keywords = [
        "게임", "아이돌", "연예인", "축구", "야구", "음식", "맛집",
        "학교", "선생님", "시험", "숙제", "친구들", "취미", "영화",
        "유튜브", "틱톡", "인스타", "카카오", "네이버"
    ]
    
    # 소설 관련 키워드가 하나도 없고, 다른 주제 키워드가 있으면
    has_novel_keyword = any(keyword in user_message for keyword in novel_keywords)
    has_off_topic = any(keyword in user_message for keyword in off_topic_keywords)
    
    # 메시지가 너무 짧지 않고 (3글자 이상), 소설 관련 없으면서 다른 주제면
    if len(user_message) > 3 and not has_novel_keyword and has_off_topic:
        return True
    
    return False

def create_redirect_message():
    """주제 이탈 시 다시 소설로 유도하는 메시지"""
    redirect_messages = [
        "어? 갑자기 다른 이야기네! 우리 <별> 이야기 계속하자. 아까 얘기하던 부분에서...",
        "아, 그것도 재미있겠지만 우리 소설 토론 시간이야! <별>에서 가장 기억에 남는 장면이 뭐야?",
        "잠깐, 우리 지금 문학 토론 중이잖아! 소설 <별>로 다시 돌아가자.",
        "그런 얘기도 좋지만, 우리 <별> 이야기 마저 하자! 소년이나 누이에 대해 더 얘기해볼래?"
    ]
    
    import random
    return random.choice(redirect_messages)

def analyze_review_for_final_question(review_content, conversation_messages):
    """감상문에서 아직 다루지 않은 주요 포인트 찾기"""
    
    # 감상문의 주요 키워드들
    review_keywords = {
        "소년": ["소년", "아이", "어린"],
        "누이": ["누이", "누나", "언니"],  
        "별": ["별", "밤하늘", "빛"],
        "어머니": ["어머니", "엄마", "모친"],
        "깨달음": ["깨달", "이해", "알게", "느끼"],
        "슬픔": ["슬프", "아프", "눈물", "울"],
        "가족": ["가족", "형제", "혈육"]
    }
    
    # 대화에서 이미 언급된 키워드 찾기
    conversation_text = " ".join([msg["content"] for msg in conversation_messages])
    
    # 감상문에는 있지만 대화에서 안 다룬 주제 찾기
    unused_topics = []
    for topic, keywords in review_keywords.items():
        in_review = any(keyword in review_content for keyword in keywords)
        in_conversation = any(keyword in conversation_text for keyword in keywords)
        
        if in_review and not in_conversation:
            unused_topics.append(topic)
    
    return unused_topics

def create_final_question(unused_topics, review_content):
    """미사용 주제를 바탕으로 마지막 질문 생성"""
    
    final_questions = {
        "소년": "네가 감상문에서 소년에 대해 썼는데, 소년의 마음 변화 중에서 가장 중요한 순간이 언제였다고 생각해?",
        "누이": "감상문에서 누이를 언급했는데, 누이가 소년에게 끝까지 사랑을 베푼 이유가 뭐라고 생각해?",
        "별": "네가 '별'에 대해 쓴 부분이 인상적이었어. 소설에서 별이 어떤 의미인지 너만의 해석을 들려줄래?",
        "어머니": "감상문에서 어머니를 언급했는데, 어머니의 부재가 이 가족에게 어떤 영향을 줬다고 봐?",
        "깨달음": "네가 쓴 '깨달음' 부분이 궁금해. 소년이 마지막에 진짜 깨달은 게 뭐라고 생각해?",
        "슬픔": "감상문에서 슬픔에 대해 썼는데, 이 소설에서 가장 슬픈 장면이 어디였어?",
        "가족": "가족 관계에 대한 네 생각이 궁금해. 이 소설이 가족의 의미에 대해 뭘 말하고 있다고 봐?"
    }
    
    if unused_topics:
        chosen_topic = unused_topics[0]  # 첫 번째 미사용 주제 선택
        return final_questions.get(chosen_topic, "마지막으로, 이 소설에서 가장 인상 깊었던 부분이 뭐야?")
    else:
        return "마지막으로, 이 소설을 읽고 네가 가장 많이 생각하게 된 건 뭐야?"

# GitHub에서 소설 전문 가져오기
@st.cache_data
def load_novel_from_github():
    try:
        # GitHub raw URL 형식으로 수정 필요
        url = "https://raw.githubusercontent.com/mveishu/star/main/novel_star.txt"
        response = requests.get(url)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text
        else:
            return None
    except Exception as e:
        st.error(f"소설 로딩 오류: {e}")
        return None

# 소설 전문 로딩
novel_full_text = load_novel_from_github()

# 기존 요약 대신 전문 사용 또는 백업 요약
if novel_full_text:
    novel_content = novel_full_text
    st.success("✅ 소설 전문을 성공적으로 로딩했습니다.")
else:
    # 백업 요약
    novel_content = """
    이 소설은 아홉 살 소년이 과수 노파로부터 누이가 돌아간 어머니와 닮았다는 말을 듣고 어머니에 대한 환상을 품게 되지만, 누이의 실제 모습에 실망하며 그녀를 거부하고 냉대하는 과정을 그린다. 소년은 누이가 베푸는 어머니 같은 사랑을 인정하지 않으려 하고, 누이의 연애 사건과 결혼, 그리고 죽음에 이르기까지 지속적으로 그녀를 멀리하지만, 결국 누이의 죽음 후에야 눈물을 흘리며 그녀 역시 어머니처럼 아름다운 별이 될 수 있음을 깨닫는다.
    """
    st.warning("⚠️ 소설 전문 로딩 실패, 요약 사용 중")

def get_claude_response(conversation_history, system_prompt):
    headers = {
        "x-api-key": st.secrets["claude"]["api_key"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 512,
        "system": system_prompt,
        "messages": conversation_history
    }
    res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    if res.status_code == 200:
        return res.json()["content"][0]["text"]
    else:
        return f"❌ Claude API 오류: {res.status_code} - {res.text}"

def send_email_with_attachment(file, subject, body, filename):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = st.secrets["email"]["user"]
    msg["To"] = "mveishu@gmail.com"
    msg.set_content(body)
    file_bytes = file.read()
    msg.add_attachment(file_bytes, maintype="application", subtype="octet-stream", filename=filename)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(st.secrets["email"]["user"], st.secrets["email"]["password"])
        smtp.send_message(msg)

st.markdown("""
<h1 style='text-align: left;'>📚 문학 토론 챗봇 - 리토</h1>
<h3 style='text-align: right; margin-top: -20px;'>:황순원, <별> 🌟</h3>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    user_lastname = st.text_input("성을 입력해주세요", key="lastname")
with col2:
    user_firstname = st.text_input("이름을 입력해주세요", key="firstname")

if user_lastname and user_firstname:
    user_name = user_firstname
    st.success(f"안녕하세요, {user_name}님! 감상문을 업로드해주세요.")
else:
    st.warning("👤 이름을 입력해주세요.")
    st.stop()

uploaded_review = st.file_uploader("📄 감상문 업로드 (.txt)", type=["txt"], key="review")

if uploaded_review and "review_sent" not in st.session_state:
    file_content = uploaded_review.read().decode("utf-8")
    uploaded_review.seek(0)
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", uploaded_review.name)
    st.session_state.review_sent = True
    st.session_state.file_content = file_content
    st.success("✅ 감상문을 성공적으로 업로드했어요!")

for key in ["messages", "start_time", "chat_disabled", "final_prompt_mode"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else False

if uploaded_review and not st.session_state.start_time:
    st.session_state.start_time = time.time()
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"안녕, {user_name}! 감상문 잘 읽었어. 우리 같이 <별> 이야기 나눠볼까?"
    })

    first_question = get_claude_response(
        [{"role": "user", "content": "감상문에서 인상 깊은 한 문장을 언급하고, 간결하게 느낌을 말한 뒤 짧고 간결하게 질문해줘."}],
        f"""
너는 {user_name}와 함께 소설 <별>을 읽은 동료 학습자야.
작품 요약:
{novel_content}

{user_name}의 감상문 요약:
{st.session_state.file_content[:400]}  # 요약 대신 앞부분 사용 가능
"""
    )
    st.session_state.messages.append({"role": "assistant", "content": first_question})

elapsed = time.time() - st.session_state.start_time if st.session_state.start_time else 0

# 8분 경고 메시지 (한 번만 표시)
if elapsed > 480 and elapsed <= 600 and "eight_min_warning" not in st.session_state:
    st.session_state.eight_min_warning = True
    
    # 감상문 분석해서 맞춤형 질문 생성
    unused_topics = analyze_review_for_final_question(st.session_state.file_content, st.session_state.messages)
    final_question = create_final_question(unused_topics, st.session_state.file_content)
    
    warning_msg = f"우리 대화 시간이 얼마 남지 않았네. 마지막으로, {final_question}"
    st.session_state.messages.append({"role": "assistant", "content": warning_msg})

# 10분 후 종료
if elapsed > 600 and not st.session_state.final_prompt_mode:
    st.session_state.final_prompt_mode = True
    st.session_state.chat_disabled = True

    final_prompt = f"""
지금은 마지막 응답이야. 사용자와 나눈 대화를 정리하고 인사로 마무리해줘.
질문은 하지 마. 짧고 따뜻하게 끝내줘. 3문장 이내로 말해줘.

작품 요약: {novel_content}
감상문 요약: {st.session_state.file_content[:400]}
"""
    claude_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] in ["user", "assistant"]]
    response = get_claude_response(claude_messages, final_prompt)
    st.session_state.messages.append({"role": "assistant", "content": response})

    log_lines = [f"{'리토' if m['role']=='assistant' else user_name}의 말: {m['content']}" for m in st.session_state.messages]
    log_text = "\n".join(log_lines)
    log_file = BytesIO()
    log_file.write(log_text.encode("utf-8"))
    log_file.seek(0)
    log_file.name = f"{user_name}_대화기록.txt"
    send_email_with_attachment(log_file, f"[대화기록] {user_name}_대화기록", "사용자와 챗봇의 전체 대화 기록입니다.", log_file.name)

    st.info("🕰️ 대화 시간이 종료되었습니다. 아래에서 성찰일지를 업로드해주세요.")

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if not st.session_state.chat_disabled and uploaded_review:
    if prompt := st.chat_input("✍️ 대화를 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

# 부적절한 발언 체크
        is_inappropriate, inappropriate_word = check_inappropriate_content(prompt)
        
        if is_inappropriate:
            # 부적절한 발언 시 피드백만 표시
            feedback_msg = create_feedback_message(inappropriate_word)
            st.session_state.messages.append({"role": "assistant", "content": feedback_msg})
            with st.chat_message("assistant"):
                st.markdown(feedback_msg)
        else:
            # 정상 대화 진행
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

if not is_inappropriate:
    # 주제 이탈 체크 추가
    if check_off_topic(prompt):
        redirect_msg = create_redirect_message()
        st.session_state.messages.append({"role": "assistant", "content": redirect_msg})
        with st.chat_message("assistant"):
            st.markdown(redirect_msg)
    else:
        # 정상 소설 토론 진행
        st.session_state.messages.append({"role": "user", "content": prompt})
        # 기존 코드...
        
        system_prompt = f"""
너는 {user_name}와 함께 소설 <별>을 읽은 같은 반 친구야. 
작품 전문/요약: {novel_content}
감상문: {st.session_state.file_content}

대화 방식:
- 친근하고 자연스러운 또래 말투 사용 ("그런데 말이야", "나는 좀 다르게 봤어", "진짜?", "어?")
- 사용자 의견에 때로는 "정말 그럴까?", "다른 관점에서는 어떨까?", "왜 그렇게 생각해?" 같은 가벼운 반문하기
- 교사처럼 가르치려 하지 말고, 진짜 궁금해서 묻는 친구처럼
- 토론 방식: 반대 의견이나 다른 해석을 정중하게 제시하기, 구체적 근거나 예시 요구하기
- "그런데 혹시 이런 가능성은 어떨까?", "작품에서 어떤 부분이 그런 느낌을 줬어?", "소년의 입장에서는 어땠을까?" 같은 질문 활용
- "정답"을 주지 말고 계속 질문으로 생각하게 만들기

예시: "어? 나는 그 장면에서 오히려 누이가 더 슬펐을 것 같은데... 너는 왜 소년이 더 힘들었다고 생각해?"

간결하게 너의 생각을 말하고, 생각해볼 만한 질문으로 마무리해줘.
3~4문장 이내로 자연스럽게 대화해줘.
"""
        
        claude_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] in ["user", "assistant"]]
        response = get_claude_response(claude_messages, system_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

if st.session_state.chat_disabled:
    st.markdown("---")
    st.subheader("📝 성찰일지를 업로드해주세요")
    uploaded_reflection = st.file_uploader("📄 성찰일지 (.txt)", type=["txt"], key="reflection")
    if uploaded_reflection and "reflection_sent" not in st.session_state:
        send_email_with_attachment(uploaded_reflection, f"[성찰일지] {user_name}_성찰일지", "사용자가 업로드한 성찰일지입니다.", uploaded_reflection.name)
        st.success("📩 성찰일지를 성공적으로 전송했어요!")
        st.session_state.reflection_sent = True

    if uploaded_reflection and "reflection_sent" in st.session_state:
        st.success("🎉 모든 절차가 완료되었습니다. 실험에 참여해주셔서 감사합니다!")
        st.stop()
