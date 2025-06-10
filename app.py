# helpdesk_support_bot_assistant_multilang_fixed.py

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
        "page_title": "Helpdesk Support Bot",
        "title": "📞 Helpdesk Support Bot",
        "description": "Ask your question about language courses — the bot will assist you!",
        "input_placeholder": "Type your question here...",
        "bot_typing": "_Bot is typing..._"
    },
    "ar": {
        "page_title": "مساعد الدعم الفني",
        "title": "📞 مساعد الدعم الفني لدورات اللغات",
        "description": "اكتب سؤالك عن دورات اللغات — سأقوم بمساعدتك!",
        "input_placeholder": "اكتب سؤالك هنا...",
        "bot_typing": "_المساعد يكتب..._"
    },
    "tr": {
        "page_title": "Yardım Masası Botu",
        "title": "📞 Yardım Masası Botu (Dil Kursları)",
        "description": "Dil kursları hakkında sorunuzu yazın — size yardımcı olacağım!",
        "input_placeholder": "Sorunuzu buraya yazın...",
        "bot_typing": "_Bot yazıyor..._"
    }
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

# Render UI
st.title(ui_text["title"])
st.write(ui_text["description"])

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

    # Add user message to the Assistant thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    # Run the Assistant on the thread
    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown(ui_text["bot_typing"])

        with st.spinner("Generating response..."):
            run = client.beta.threads.runs.create(
                thread_id=st.session_state.thread_id,
                assistant_id=ASSISTANT_ID
            )

            # Poll for completion
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

            # Retrieve latest messages from thread
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )

            # Get the last assistant message
            for msg in reversed(messages.data):
                if msg.role == "assistant":
                    assistant_reply = msg.content[0].text.value
                    break

            # Replace placeholder with actual reply
            placeholder.markdown(assistant_reply)

            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})

# Chat input
user_input = st.chat_input(ui_text["input_placeholder"])

if user_input:
    if not st.session_state.language_detected_done:
        # First message → detect language → set rerun flow
        st.session_state.detected_language = detect_language(user_input)
        st.session_state.language_detected_done = True
        st.session_state.first_message_content = user_input
        st.session_state.send_first_message_after_rerun = True
        st.rerun()

    else:
        # Normal flow after first message
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

                messages = client.beta.threads.messages.list(
                    thread_id=st.session_state.thread_id
                )

                for msg in reversed(messages.data):
                    if msg.role == "assistant":
                        assistant_reply = msg.content[0].text.value
                        break

                placeholder.markdown(assistant_reply)

                st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
