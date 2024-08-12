import os
import json
import re
from datetime import datetime

import streamlit as st
from components.floating_chat import floating_chat_button
from groq import Groq

# Обновляем функцию generate_filename для учета имени агента
def generate_filename():
    now = datetime.now()
    agent_name = st.session_state.selected_agent["name"].replace(" ", "_")
    return f"{now.strftime('%Y-%m-%d-%H%M%S')}_{agent_name}.md"

def sum_daily_tokens():
    today = datetime.now().strftime("%Y-%m-%d")
    chats_dir = "chats"
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_total_tokens = 0

    pattern = r'\*Всего в сессии (\d+):(\d+):(\d+)\*'

    for filename in os.listdir(chats_dir):
        if filename.startswith(today):
            file_path = os.path.join(chats_dir, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for line in reversed(lines):
                    if line.strip():
                        match = re.search(pattern, line)
                        if match:
                            total_prompt_tokens += int(match.group(1))
                            total_completion_tokens += int(match.group(2))
                            total_total_tokens += int(match.group(3))
                        break
    result = round((total_total_tokens * 0.79 * 100 / 1000000), 2)
    return f"Всего токенов за {today}:{total_total_tokens} = ₽{result} [$0.79]" # $0.79/(per 1M Tokens, input/output)
    # return f"Всего за {today} {total_prompt_tokens}:{total_completion_tokens}:{total_total_tokens}=₽{result} [$0.79]" # $0.79/(per 1M Tokens, input/output)

def generate_filename():
    now = datetime.now()
    return now.strftime("%Y-%m-%d-%H%M%S.md")

def write_to_file(filename, content):
    os.makedirs("chats", exist_ok=True)
    file_path = os.path.join("chats", filename)
    
    # Удаляем блок Usage Info из контента перед записью
    content_lines = content.split("\n")
    clean_content = "\n".join([line for line in content_lines if not line.startswith("**Usage Info:**")])
    
    # Удаляем JSON блок
    clean_content = re.sub(r'```json\n.*?```', '', clean_content, flags=re.DOTALL)
    
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(clean_content.strip() + "\n\n")

# streamlit page configuration
st.set_page_config(
    page_title="LLAMA 3.1. Chat",
    page_icon="🦙",
    layout="centered"
)

working_dir = os.path.dirname(os.path.abspath(__file__))
config_data = json.load(open(f"{working_dir}/config.json"))

GROQ_API_KEY = config_data["GROQ_API_KEY"]
# Добавляем загрузку агентов из config.json
AGENTS = config_data["AGENTS"]

# save the api key to environment variable
os.environ["GROQ_API_KEY"] = GROQ_API_KEY

client = Groq()

# initialize the chat history as streamlit session state of not present already
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# В начале скрипта, после инициализации chat_history
if "current_chat_file" not in st.session_state:
    # st.session_state.current_chat_file = generate_filename()
    st.session_state.current_chat_file = None

# Инициализация session totlal tokens 
if "total_prompt_tokens" not in st.session_state:
    st.session_state.total_prompt_tokens = 0
if "total_completion_tokens" not in st.session_state:
    st.session_state.total_completion_tokens = 0
if "total_total_tokens" not in st.session_state:
    st.session_state.total_total_tokens = 0

# streamlit page title
st.title("🦙 LLAMA 3.1. ChatBot")

if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None

if st.session_state.selected_agent is None:
    agent_names = [agent["name"] for agent in AGENTS]
    selected_agent_name = st.selectbox("Выберите AI-агента:", agent_names)
    selected_agent = next(agent for agent in AGENTS if agent["name"] == selected_agent_name)
    if st.button("Начать сессию"):
        st.session_state.selected_agent = selected_agent
        st.session_state.chat_history = []
        st.session_state.current_chat_file = generate_filename()
        st.rerun()

# Отображаем интерфейс чата только если агент выбран
if st.session_state.selected_agent:
    st.write(f"Текущий агент: {st.session_state.selected_agent['name']}")
    
    # Добавляем кнопку завершения сессии
    if st.button("Завершить сессию"):
        st.session_state.selected_agent = None
        st.session_state.chat_history = []
        st.session_state.current_chat_file = None
        st.rerun()

    # Отображение истории чата
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Поле ввода для сообщения пользователя
    user_prompt = st.chat_input("Ask LLAMA...")

    if user_prompt:
        st.chat_message("user").markdown(user_prompt)
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        write_to_file(st.session_state.current_chat_file, f"**User:** {user_prompt}")

        # Отправляем сообщение пользователя в LLM и получаем ответ
        messages = [
            {"role": "system", "content": st.session_state.selected_agent["system_prompt"]},
            *st.session_state.chat_history
        ]

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages
        )

        assistant_response = response.choices[0].message.content
        usage_info = response.usage
        
        # Обновляем суммарные значения
        st.session_state.total_prompt_tokens += usage_info.prompt_tokens
        st.session_state.total_completion_tokens += usage_info.completion_tokens
        st.session_state.total_total_tokens += usage_info.total_tokens

        # Формируем строки с информацией о токенах
        current_tokens_info = f"*Потрачено токенов {usage_info.prompt_tokens}:{usage_info.completion_tokens}:{usage_info.total_tokens}*"
        total_tokens_info = f"*Всего в сессии {st.session_state.total_prompt_tokens}:{st.session_state.total_completion_tokens}:{st.session_state.total_total_tokens}*"

        # Добавляем информацию о токенах к ответу ассистента
        full_response = f"{assistant_response}\n\n---\n{current_tokens_info}\n{total_tokens_info}"

        # Добавляем только один раз в историю чата
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
        
        # Записываем в файл
        write_to_file(st.session_state.current_chat_file, f"**Assistant:** {full_response}")

        # Отображаем ответ ассистента
        with st.chat_message("assistant"):
            st.markdown(full_response)

        # Отображаем информацию об использовании в отдельном блоке
        with st.expander("Информация об использовании"):
            usage_data = {
                "prompt_tokens": usage_info.prompt_tokens,
                "completion_tokens": usage_info.completion_tokens,
                "total_tokens": usage_info.total_tokens,
                "prompt_time": round(usage_info.prompt_time, 3),
                "completion_time": round(usage_info.completion_time, 3),
                "total_time": round(usage_info.total_time, 3)
            }
            st.json(usage_data)

        # Отображаем суммарную информацию за день
        daily_summary = sum_daily_tokens()
        st.info(daily_summary)

# Комментируем эту строку, так как плавающая кнопка чата не используется в текущей версии
# floating_chat_button()