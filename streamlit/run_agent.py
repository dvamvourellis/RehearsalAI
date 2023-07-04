# import sys

# sys.path.append("../")

import streamlit as st
import os

path = os.getcwd()
dir_list = os.listdir(path)
st.write(path)
st.write(dir_list)

from agent.rehearsal import Rehearsal
from streamlit_chat import message
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)

st.title("Rehearsal AI")

with st.sidebar:
    openai_api_key = st.text_input(
        "Enter your OpenAI API Key",
        key="user_key_input",
        type="password",
        autocomplete="current-password",
    )

    user_role_name = st.text_input("Input role 1", key="user_role_name")
    other_side_role_name = st.text_input("Input role 2", key="other_side_role_name")

    topic = st.text_input(
        "Input a few words about the topic of the discussion.", key="topic"
    )

    user_role_characteristics = st.text_input(
        f"What are the characteristics of {user_role_name}? Please enter comma separated list of adjectives.",
        key="user_chars",
    )
    user_characteristics = user_role_characteristics.split(",")

    other_side_role_characteristics = st.text_input(
        f"What are the characteristics of {other_side_role_name}? Please enter comma separated list of adjectives.",
        key="other_side_chars",
    )
    other_side_characteristics = other_side_role_characteristics.split(",")

    argument_basis = st.text_input(
        f"Input a few points that you would like the {user_role_name} to use as an argument basis. (Optional)",
        key="argument_basis",
    )

    minimum_goal = st.text_input(
        f"Write the minimum outcome that the {user_role_name} would like to achieve after the end of this debate. (Optional)",
        key="minimum_goal",
    )

if openai_api_key == "":
    st.write("Please provide a valid OpenAI API key.")

else:
    if st.button("Generate Discussion"):
        rehearsal = Rehearsal(
            openai_api_key=openai_api_key,
            model_name="gpt-3.5-turbo",
            user_role_name=user_role_name,
            other_side_role_name=other_side_role_name,
            other_characteristics=other_side_characteristics,
            user_characteristics=user_characteristics,
            argument_basis=argument_basis,
            minimum_goal=minimum_goal,
            topic=topic,
            temperature=0.5,
            chat_turn_limit=5,
        )

        with st.container():
            # Initialize chats
            other_side_msg = HumanMessage(
                content=(
                    f"{rehearsal.user_sys_msg.content}. "
                    "Now start to give me your opinion on the topic and the supporting arguments. "
                )
            )
            user_msg = HumanMessage(content=f"{rehearsal.other_side_sys_msg.content}")

            # Storing the chat
            if "generated" not in st.session_state:
                st.session_state["generated"] = []

            if "past" not in st.session_state:
                st.session_state["past"] = other_side_msg

            n = 0
            while n < rehearsal.chat_turn_limit:
                n += 1
                user_ai_msg = rehearsal.user_agent.step(other_side_msg)
                user_msg = HumanMessage(content=user_ai_msg.content)
                print_msg = f"{rehearsal.user_role_name}:\n\n{user_msg.content}\n\n"
                st.write(print_msg)
                rehearsal.transcipt.append(print_msg)
                # st.session_state.generated.append(user_msg.content)

                other_side_ai_msg = rehearsal.other_side_agent.step(user_msg)
                other_side_msg = HumanMessage(content=other_side_ai_msg.content)
                print_msg = (
                    f"{rehearsal.other_side_role_name}:\n\n{other_side_msg.content}\n\n"
                )
                st.write(print_msg)
                rehearsal.transcipt.append(print_msg)
                # st.session_state.past.append(other_side_msg.content)

                if "<CAMEL_TASK_DONE>" in user_msg.content:
                    break

        st.header("Debate Critique")

        with st.container():
            summary = rehearsal.generate_summary()
            st.write(summary)
