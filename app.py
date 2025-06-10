# helpdesk_support_bot_assistant.py

import streamlit as st
import openai
from dotenv import load_dotenv
import os
import time

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Your Assistant ID from the screenshot
ASSISTANT_ID = "asst_eCbjATL3G2EJ9oLaXqz5HZEX"

# Streamlit App Config
st.set_page_config(page_title="Transact Support Agent", page_icon="🤖")
st.title("📞 Support Agent")
st.write("Ask your question about language courses — the bot will assist you!")

# Initialize Thread ID in session state
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.messages = []

# Display chat messages so far
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.markdown(msg["content"])
    elif msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Type your question here...")

if user_input:
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Append user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Add user message to the Assistant thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_input
    )

    # Run the Assistant on the thread
    with st.chat_message("assistant"):
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
                time.sleep(1)  # wait before polling again

            # Retrieve latest messages from thread
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )

            # Get the last assistant message
            for msg in reversed(messages.data):
                if msg.role == "assistant":
                    assistant_reply = msg.content[0].text.value
                    break

            st.markdown(assistant_reply)

            # Append assistant reply to chat history
            st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
