import streamlit as st
from agent import StudyAgent


st.set_page_config(
    page_title="AI Study Agent",
    page_icon="🤖",
    layout="centered"
)


st.title("🤖 AI Study Agent")

st.write(
    "An intelligent agent that understands tasks, "
    "selects tools and generates useful responses."
)


if "agent" not in st.session_state:

    try:
        st.session_state.agent = StudyAgent()

    except Exception as e:

        st.error(str(e))
        st.stop()


if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.write(message["content"])


user_input = st.chat_input(
    "Ask your AI Study Agent..."
)


if user_input:

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):

        with st.spinner("Agent is thinking..."):

            try:

                response = st.session_state.agent.ask(
                    user_input
                )

                st.write(response)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": response
                    }
                )

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )
