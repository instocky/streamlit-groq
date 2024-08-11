import os
import json

import streamlit as st
from groq import Groq

# streamlit page configuration
st.set_page_config(
    page_title="LLAMA 3.1. Chat",
    page_icon="🦙",
    layout="centered"
)

working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))

GROQ_API_KEY = config_data["GROQ_API_KEY"]
SYSTEM_PROMPT = config_data["SYSTEM_PROMPT"]  # Добавляем эту строку

# save the api key to environment variable
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

# initialize the chat history as streamlit session state of not present already
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# streamlit page title
st.title("🦙 LLAMA 3.1. ChatBot")

# display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# input field for user's message:
user_prompt = st.chat_input("Ask LLAMA...")

if user_prompt:
    st.chat_message("user").markdown(user_prompt)
    st.session_state.chat_history.append({"role": "user", "content": user_prompt})

    # send user's message to the LLM and get a response
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},  # Используем системный промпт из config.json
        *st.session_state.chat_history
    ]

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages
    )

    assistant_response = response.choices[0].message.content
    st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

    usage_info = response.usage

    # Отображаем ответ ассистента
    with st.chat_message("assistant"):
        st.markdown(assistant_response)

    # Отображаем информацию об использовании в отдельном блоке
    with st.expander("Информация об использовании"):
        st.json({
            "prompt_tokens": usage_info.prompt_tokens,
            "completion_tokens": usage_info.completion_tokens,
            "total_tokens": usage_info.total_tokens,
            "prompt_time": round(usage_info.prompt_time, 3),
            "completion_time": round(usage_info.completion_time, 3),
            "total_time": round(usage_info.total_time, 3)
            })