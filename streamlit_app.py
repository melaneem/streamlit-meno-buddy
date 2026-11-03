import streamlit as st
from openai import OpenAI

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"

system_prompt = """
You are a specialist in analyzing sleep patterns for women in menopause.
"""

st.title("Meno Buddy")
st.caption("Sleep and menopause support assistant")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": "Hi! I'm going to ask you a few questions."},
    ]

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Ask about your sleep symptoms...")

if prompt:
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = OpenAI(api_key=openai_api_key)
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
        ],
        stream=True,
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)

    if isinstance(response, list):
        response = "".join(str(part) for part in response)

    st.session_state.messages.append({"role": "assistant", "content": response})
