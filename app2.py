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

# App metadata
APP_TITLE = "Transact Customer Support"
APP_DESCRIPTION = "Welcome to **Transact Customer Support** — your multilingual assistant for all inquiries about language courses.\n\nSelect a sample question from the list below, or type your own in the chat."

# Example prompts
EXAMPLES = {
    "General Inquiry": [
        "I saw your ad on Instagram — can you tell me more about your courses?",
        "Which languages do you offer?",
        "Are there any cultural activities included?"
    ],
    "Pricing & Discounts": [
        "How much does the Arabic beginner course cost?",
        "Do you have student discounts?"
    ],
    "Course Schedule": [
        "When do the next English conversation classes start?",
        "Do you have evening classes for Turkish?"
    ],
    "Registration Assistance": [
        "I tried to sign up online but it didn’t go through — can you help?"
    ],
    "Change / Cancel Enrollment": [
        "I want to cancel my enrollment — what is the refund policy?"
    ],
    "Technical Support (Digital Platform)": [
        "I can’t log in to my account.",
        "The video lessons are not loading."
    ],
    "Certificate Request": [
        "How can I get my certificate for the Arabic course?"
    ],
    "Placement Test Request": [
        "Do I need to take a level test before enrolling?"
    ],
    "Trial Class Booking": [
        "I’d like to book a free trial class for Arabic."
    ],
    "Course Format Inquiry": [
        "Do you offer Turkish courses both online and in person?"
    ],
    "Teacher Info": [
        "Who teaches the advanced English courses?"
    ],
    "Language Availability": [
        "Do you offer Arabic courses for French-speaking students?"
    ],
    "Payment Issues": [
        "My card was charged twice — can you check?"
    ],
    "Children’s Courses": [
        "Do you offer Turkish courses for kids aged 8–10?"
    ],
    "Referral / Gift Questions": [
        "I received a gift card — how do I use it?"
    ]
}

# Multilingual UI texts
UI_TEXTS = {
    "en": {
        "page_title": APP_TITLE,
        "title": APP_TITLE,
        "description": APP_DESCRIPTION,
        "input_placeholder": "Type your question here...",
        "bot_typing": "_Bot is typing..._"
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

# Configure Streamlit page
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

# Layout: show logos in two columns
col1, col2 = st.columns([1, 1])
with col1:
    st.image("logo1.png", width=120)  # replace with your logo path
with col2:
    st.image("logo2.png", width=120)  # replace with your logo path

# App title & description
st.title(ui_text["title"])
st.write(ui_text["description"])

# Example Prompts (Collapsible)
with st.expander("💡 Show Example Questions"):
    for category, prompts in EXAMPLES.items():
        st.subheader(category)
        for example in prompts:
            if st.button(example, key=example):
                # Clear chat & start new with this example
                thread = client.beta.threads.create()
                st.session_state.thread_id = thread.id
                st.session_state.messages = []
                st.session_state.detected_language = detect_language(example)
                st.session_state.language_detected_done = True
                st.session_state.first_message_content = example
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
