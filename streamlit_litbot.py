# -*- coding: utf-8 -*-
import streamlit as st
from io import BytesIO
from email.message import EmailMessage
import smtplib
import requests
import time

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

# 토론 패턴 감지 및 반문 생성 함수 추가
import random

def analyze_user_sentiment(text):
    """사용자 의견의 감정과 관점을 분석"""
    positive_keywords = ['좋다', '훌륭하다', '감동', '아름답다', '의미있다']
    negative_keywords = ['아쉽다', '이해안됨', '별로', '지루하다', '불만']
    
    positive_count = sum(1 for word in positive_keywords if word in text)
    negative_count = sum(1 for word in negative_keywords if word in text)
    
    if positive_count > negative_count:
        return "positive"
    elif negative_count > positive_count:
        return "negative"
    else:
        return "neutral"

def get_debate_prompt_type():
    """토론 유형을 랜덤하게 선택"""
    debate_types = [
        "opposing_view",     # 반대 관점 제시
        "evidence_request",  # 근거 요구
        "alternative_interpretation", # 다른 해석 제시
        "deeper_analysis",   # 심화 분석 유도
        "character_perspective" # 인물 관점 전환
    ]
    return random.choice(debate_types)

def create_debate_system_prompt(user_message, sentiment, debate_type, user_name, novel_content, file_content):
    """토론을 위한 시스템 프롬프트 생성"""
    
    base_prompt = f"""
너는 {user_name}와 소설 <별>에 대해 깊이 있는 문학 토론을 하는 동료야.
사용자가 의견을 제시했을 때, 단순히 동조하지 말고 건설적인 반문이나 다른 관점을 제시해서 토론을 발전시켜야 해.

작품 내용: {novel_content}
사용자 감상문: {file_content[:300]}
사용자 현재 의견: {user_message}
사용자 감정 성향: {sentiment}
"""

    if debate_type == "opposing_view":
        return base_prompt + """
토론 방식: 사용자의 의견에 대해 정중하지만 다른 관점을 제시해. 
"그런데 다른 시각에서 보면..." 또는 "혹시 이런 가능성은 어떨까?" 식으로 시작해.
반대 의견을 제시한 후 "너는 이 부분을 어떻게 생각해?" 같은 질문으로 마무리해.
"""

    elif debate_type == "evidence_request":
        return base_prompt + """
토론 방식: 사용자의 의견에 대해 구체적인 근거나 예시를 요구해.
"그렇게 생각하는 구체적인 이유가 있어?" 또는 "작품에서 어떤 부분이 그런 느낌을 줬어?" 식으로 질문해.
"""

    elif debate_type == "alternative_interpretation":
        return base_prompt + """
토론 방식: 같은 장면이나 인물에 대해 완전히 다른 해석을 제시해.
"나는 그 장면을 이렇게 봤는데..." 식으로 시작해서 새로운 해석을 제시하고 의견을 물어봐.
"""

    elif debate_type == "deeper_analysis":
        return base_prompt + """
토론 방식: 사용자의 의견을 더 깊이 파고들어 분석하도록 유도해.
"그런데 왜 작가가 그런 선택을 했을까?" 또는 "그게 전체 주제와 어떤 관련이 있을까?" 같은 심화 질문을 해.
"""

    elif debate_type == "character_perspective":
        return base_prompt + """
토론 방식: 다른 인물의 입장에서 생각해보도록 유도해.
"만약 네가 소년이라면..." 또는 "누이의 입장에서는 어땠을까?" 같은 관점 전환 질문을 해.
"""

    return base_prompt + "간결하게 반응하고 열린 질문으로 마무리해."

# 기존 get_claude_response 함수 수정
def get_claude_response_with_debate(conversation_history, user_message, user_name, novel_content, file_content):
    """토론 기능이 강화된 Claude 응답 생성"""
    
    # 사용자 감정 분석
    sentiment = analyze_user_sentiment(user_message)
    
    # 토론 유형 결정
    debate_type = get_debate_prompt_type()
    
    # 토론용 시스템 프롬프트 생성
    system_prompt = create_debate_system_prompt(
        user_message, sentiment, debate_type, user_name, novel_content, file_content
    )
    
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

# 대화 처리 부분 수정 (기존 코드에서 이 부분을 교체)
if not st.session_state.chat_disabled and uploaded_review:
    if prompt := st.chat_input("✍️ 대화를 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 토론 기능이 강화된 응답 생성
        claude_messages = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] in ["user", "assistant"]]
        
        # 기존 단순 응답 대신 토론 응답 사용
        response = get_claude_response_with_debate(
            claude_messages, 
            prompt, 
            user_name, 
            novel_content, 
            st.session_state.file_content
        )
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# 토론 난이도 조절 옵션 추가 (사이드바)
with st.sidebar:
    st.subheader("🎯 토론 설정")
    debate_intensity = st.selectbox(
        "토론 강도",
        ["순수한 대화", "가벼운 토론", "적극적 토론", "치열한 토론"],
        index=1
    )
    
    if debate_intensity == "순수한 대화":
        st.session_state.debate_mode = False
    else:
        st.session_state.debate_mode = True
        st.session_state.debate_level = debate_intensity

# 토론 통계 표시 (선택사항)
if "debate_stats" not in st.session_state:
    st.session_state.debate_stats = {
        "opposing_views": 0,
        "evidence_requests": 0,
        "alternative_interpretations": 0,
        "deeper_analysis": 0,
        "character_perspectives": 0
    }

# 사이드바에 토론 통계 표시
with st.sidebar:
    if st.session_state.get("debate_mode", False):
        st.subheader("📊 토론 현황")
        st.write(f"반대 의견 제시: {st.session_state.debate_stats['opposing_views']}회")
        st.write(f"근거 요구: {st.session_state.debate_stats['evidence_requests']}회")
        st.write(f"다른 해석 제시: {st.session_state.debate_stats['alternative_interpretations']}회")
        
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

st.title("📚 문학 토론 챗봇 - 리토")
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
if elapsed > 600 and not st.session_state.final_prompt_mode:
    st.session_state.final_prompt_mode = True
    st.session_state.chat_disabled = True

    final_prompt = f"""
지금은 마지막 응답이야. 사용자와 나눈 대화를 정리하고 인사로 마무리해줘.
질문은 하지 마. 짧고 따뜻하게 끝내줘. 3문장 이내로 말해줘.

작품 요약: {novel_summary}
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

        system_prompt = f"""
너는 {user_name}와 <별>을 읽은 동료야.
작품 요약: {novel_content}
감상문 요약: {st.session_state.file_content[:400]}

간결하게 너의 생각을 말하고, 열린 질문으로 마무리해줘.
3~4문장 이내로 응답해줘. 너무 길지 않게.
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
