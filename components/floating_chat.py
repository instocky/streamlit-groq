# components/floating_chat.py

import streamlit as st

def floating_chat_button():
    # Пользовательский CSS для стилизации expander'а
    st.markdown("""
    <style>
    .chat-expander {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 300px;
        z-index: 1000;
    }
    .chat-expander .streamlit-expander {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

    # Создаем плавающее окно (expander)
    with st.container():
        st.markdown('<div class="chat-expander">', unsafe_allow_html=True)
        with st.expander("💬 Чат", expanded=False):
            st.write("Это содержимое чата.")
            user_input = st.text_input("Введите сообщение:")
            if st.button("Отправить"):
                st.write(f"Вы отправили: {user_input}")
        st.markdown('</div>', unsafe_allow_html=True)