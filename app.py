import streamlit as st
import openai
from dotenv import load_dotenv
import os
import time
from langdetect import detect

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Assistant ID
ASSISTANT_ID = "asst_eCbjATL3G2EJ9oLaXqz5HZEX"

# Multilingual UI texts
UI_TEXTS = {
    "en": {
        "page_title": "Transact Customer Support",
        "title": "📞 Transact Customer Support",
        "description": "Welcome to **Transact Customer Support** — your multilingual assistant for all inquiries about language courses.\n\nSelect a sample question from the list below, or type your own in the chat.",
        "input_placeholder": "Type your question here...",
        "bot_typing": "_Bot is typing..._"
    },
    "ar": {
        "page_title": "Transact Customer Support",
        "title": "📞 Transact Customer Support",
        "description": "مرحباً بك في **Transact Customer Support** — مساعدك متعدد اللغات لجميع الاستفسارات حول دورات اللغة. يمكنك اختيار سؤال نموذجي من القائمة أدناه أو كتابة سؤالك الخاص في المحادثة.",
        "input_placeholder": "اكتب سؤالك هنا...",
        "bot_typing": "_المساعد يكتب..._"
    },
    "tr": {
        "page_title": "Transact Customer Support",
        "title": "📞 Transact Customer Support",
        "description": "**Transact Customer Support**'a hoş geldiniz — dil kurslarıyla ilgili tüm sorularınız için çok dilli asistanınız. Aşağıdaki örnek sorulardan birini seçebilir veya kendi sorunuzu sohbet kutusuna yazabilirsiniz.",
        "input_placeholder": "Sorunuzu buraya yazın...",
        "bot_typing": "_Bot yazıyor..._"
    }
}

# Example prompts
EXAMPLES = {
    "General Inquiry": [
        "I saw your ad on Instagram — can you tell me more about your courses?",
        "Which languages do you offer?",
        "Are there any cultural activities included?",
        "فيك تخبرني شو الكورسات المتوفرة عندكن؟",
        "Türkçe kurslarının içeriği hakkında bilgi alabilir miyim?"
    ],
    "Pricing & Discounts": [
        "How much does the Arabic beginner course cost?",
        "Do you have student discounts?",
        "ممكن أعرف قديش تكلفة كورس العربي للمبتدئين؟",
        "Arapça başlangıç seviyesi kursunun fiyatı nedir?"
    ],
    "Course Schedule": [
        "When do the next English conversation classes start?",
        "Do you have evening classes for Turkish?",
        "إيمتى بتبلش دورات المحادثة بالإنجليزي؟",
        "Türkçe için akşam dersleri var mı?"
    ],
    "Registration Assistance": [
        "I tried to sign up online but it didn’t go through — can you help?",
        "جربت سجل أونلاين وما زبط — ممكن تساعديني؟",
        "Online kaydolmaya çalıştım ama olmadı — yardımcı olabilir misiniz?"
    ],
    "Change / Cancel Enrollment": [
        "I want to cancel my enrollment — what is the refund policy?",
        "بدي غيّر وقت الصف — في مجال؟",
        "Ders saatimi değiştirebilir miyim?"
    ]
    # You can continue adding all 15 categories here (just copy your list)
}

# Detect language of input
def detect_language(text):
    try:
        lang = detect(text)
    except:
        return "en"
    if lang.startswith("ar"):
        return "ar"
    elif lang.startswith("tr"):
        return "tr"
    return "en"

# Configure Streamlit page (default EN)
st.set_page_config(page_title=UI_TEXTS["en"]["page_title"], page_icon="🤖")

# Initialize session state
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []
if "language_detected_done" not in st.session_state:
    st.session_state.language_detected_done = False
if "detected_language" not in st.session_state:
    st.session_state.detected_language = "en"
if "send_first_message_after_rerun" not in st.session_state:
    st.session_state.send_first_message_after_rerun = False
if "first_message_content" not in st.session_state:
    st.session_state.first_message_content = ""

# Select UI texts
ui_text = UI_TEXTS[st.session_state.detected_language]

# Show logos
col1, col2 = st.columns([1, 1])
with col1:
    st.image("logo1.png", use_container_width=True)
with col2:
    st.image("logo2.png", use_container_width=True)

# Render UI
st.title(ui_text["title"])
st.write(ui_text["description"])

# Show example prompts (safe: no nested expanders)
with st.expander("📋 Show Example Questions"):
    for category, prompts in EXAMPLES.items():
        st.markdown(f"### {category}")  # Safe: no nested expander
        for prompt in prompts:
            if st.button(prompt):
                st.session_state.detected_language = detect_language(prompt)
                st.session_state.language_detected_done = True
                st.session_state.first_message_content = prompt
                st.session_state.send_first_message_after_rerun = True
                st.rerun()

# Show chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# First run after language detection rerun
if st.session_state.send_first_message_after_rerun:
    user_input = st.session_state.first_message_content
    st.session_state.send_first_message_after_rerun = False
    st.session_state.first_message_content = ""

    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append({"role": "user", "content": user_input})

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(ui_text["bot_typing"])

        with st.spinner("Generating response..."):
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID
            )
            while True:
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                )
                if run_status.status == "completed":
                    break
                elif run_status.status in ["failed", "expired", "cancelled"]:
                    st.error(f"Run failed with status: {run_status.status}")
                    break
                time.sleep(1)
            time.sleep(2)
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            assistant_reply = None
            for msg in messages.data:
                if msg.role == "assistant":
                    assistant_reply = msg.content[0].text.value
                    break
            if assistant_reply is None:
                assistant_reply = "_Error: No assistant reply found._"

            placeholder.markdown(assistant_reply)
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# Chat input
user_input = st.chat_input(ui_text["input_placeholder"])

if user_input:
    if not st.session_state.language_detected_done:
        st.session_state.detected_language = detect_language(user_input)
        st.session_state.language_detected_done = True
        st.session_state.first_message_content = user_input
        st.session_state.send_first_message_after_rerun = True
        st.rerun()
    else:
        with st.chat_message("user"):
            st.markdown(user_input)

        st.session_state.messages.append({"role": "user", "content": user_input})

        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=user_input
        )

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown(ui_text["bot_typing"])

            with st.spinner("Generating response..."):
                run = client.beta.threads.runs.create(
                    thread_id=st.session_state.thread_id,
                    assistant_id=ASSISTANT_ID
                )
                while True:
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state.thread_id,
                        run_id=run.id
                    )
                    if run_status.status == "completed":
                        break
                    elif run_status.status in ["failed", "expired", "cancelled"]:
                        st.error(f"Run failed with status: {run_status.status}")
                        break
                    time.sleep(1)
                time.sleep(2)
                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )
                assistant_reply = None
                for msg in messages.data:
                    if msg.role == "assistant":
                        assistant_reply = msg.content[0].text.value
                        break
                if assistant_reply is None:
                    assistant_reply = "_Error: No assistant reply found._"

                placeholder.markdown(assistant_reply)
                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
