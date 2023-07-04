import sys

sys.path.append("../")

from typing import List
from typing import Optional

import os
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    BaseMessage,
)

from agent.camel_agent import CAMELAgent
from agent.prompt_templates import (
    other_side_inception_prompt,
    user_inception_prompt,
    summary_prompt,
)


class Rehearsal:
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model_name: Optional[str] = "gpt-3.5-turbo",
        user_role_name: str = None,
        other_side_role_name: str = None,
        other_characteristics: List[str] = [],
        user_characteristics: List[str] = [],
        argument_basis: str = None,
        minimum_goal: str = None,
        topic: str = None,
        temperature: float = 0.5,
        chat_turn_limit: int = 10,
    ):
        # initialize template variables
        self.user_role_name = user_role_name
        self.other_side_role_name = other_side_role_name
        self.topic = topic
        self.user_characteristics = user_characteristics
        self.other_characteristics = other_characteristics

        if argument_basis is None:
            self.argument_basis = ""
        else:
            self.argument_basis = argument_basis
        if minimum_goal is None:
            self.minimum_goal = ""
        else:
            self.minimum_goal = minimum_goal

        # initialize maximum number of turns to complete dialogue
        self.chat_turn_limit = chat_turn_limit

        # initialize llm
        self.llm = self._init_llm(
            openai_api_key=openai_api_key,
            model_name=model_name,
            temperature=temperature,
        )

        self.other_side_sys_msg, self.user_sys_msg = self._get_sys_msgs()

        # initialize CAMEL agents
        self._init_agents()

        # initialize chat transcript
        self.transcipt = []

    def _init_llm(
        self,
        openai_api_key: Optional[str] = None,
        model_name: Optional[str] = "gpt-3.5-turbo",
        temperature: Optional[float] = 0.5,
    ):
        if openai_api_key is None and "OPENAI_API_KEY" not in os.environ:
            raise Exception("No OpenAI API key provided")
        openai_api_key = openai_api_key or os.environ["OPENAI_API_KEY"]
        llm = ChatOpenAI(
            model=model_name, temperature=temperature, openai_api_key=openai_api_key
        )
        return llm

    def _get_sys_msgs(self):
        if (
            len(self.user_characteristics) == 1 and self.user_characteristics[0] == ""
        ) or len(self.user_characteristics) == 0:
            user_characteristics_str = ""
        else:
            user_characteristics_str = ", ".join(self.user_characteristics) + "."
        if (
            len(self.other_characteristics) == 1 and self.other_characteristics[0] == ""
        ) or len(self.other_characteristics) == 0:
            other_characteristics_str = ""
        else:
            other_characteristics_str = ", ".join(self.other_characteristics) + "."

        user_inception_prompt_final = user_inception_prompt
        other_side_inception_prompt_final = other_side_inception_prompt

        if self.argument_basis == "":
            user_inception_prompt_final = user_inception_prompt_final.replace(
                "You will try to persuade me with your arguments and I will try to challenge your arguments. You will base your argument around the following ideas:",
                "",
            )

        if self.minimum_goal == "":
            user_inception_prompt_final = user_inception_prompt_final.replace(
                "Do not compromise with anything else than the following minimum goal:",
                "",
            )

        if user_characteristics_str == "":
            user_inception_prompt_final = user_inception_prompt_final.replace(
                "with the following characteristics:",
                ".",
            )

        if other_characteristics_str == "":
            other_side_inception_prompt_final = (
                other_side_inception_prompt_final.replace(
                    "with the following characteristics:",
                    ".",
                )
            )

        other_side_sys_template = SystemMessagePromptTemplate.from_template(
            template=other_side_inception_prompt_final
        )
        other_side_sys_msg = other_side_sys_template.format_messages(
            other_side_role_name=self.other_side_role_name,
            user_role_name=self.user_role_name,
            topic=self.topic,
            other_characteristics=other_characteristics_str,
        )[0]

        user_sys_template = SystemMessagePromptTemplate.from_template(
            template=user_inception_prompt_final
        )
        user_sys_msg = user_sys_template.format_messages(
            other_side_role_name=self.other_side_role_name,
            user_role_name=self.user_role_name,
            topic=self.topic,
            argument_basis=self.argument_basis,
            minimum_goal=self.minimum_goal,
            user_characteristics=user_characteristics_str,
        )[0]

        return other_side_sys_msg, user_sys_msg

    def _init_agents(self):
        self.other_side_agent = CAMELAgent(self.other_side_sys_msg, self.llm)
        self.user_agent = CAMELAgent(self.user_sys_msg, self.llm)
        # Reset agents
        self.other_side_agent.reset()
        self.user_agent.reset()

    def start_discussion(self):
        # Initialize chats
        other_side_msg = HumanMessage(
            content=(
                f"{self.user_sys_msg.content}. "
                "Now start to give me your opinion on the topic and the supporting arguments. "
            )
        )
        user_msg = HumanMessage(content=f"{self.other_side_sys_msg.content}")

        n = 0
        while n < self.chat_turn_limit:
            n += 1
            user_ai_msg = self.user_agent.step(other_side_msg)
            user_msg = HumanMessage(content=user_ai_msg.content)
            print_msg = f"{self.user_role_name}:\n\n{user_msg.content}\n\n"
            print(print_msg)
            self.transcipt.append(print_msg)

            other_side_ai_msg = self.other_side_agent.step(user_msg)
            other_side_msg = HumanMessage(content=other_side_ai_msg.content)
            print_msg = f"{self.other_side_role_name}:\n\n{other_side_msg.content}\n\n"
            print(print_msg)
            self.transcipt.append(print_msg)
            if "<CAMEL_TASK_DONE>" in user_msg.content:
                break

    def generate_summary(self):
        if len(self.transcipt) < 1:
            print("No conversation found. Please run discussion first.")
            return None

        transcript_str = " ".join(self.transcipt)

        prompt_template = PromptTemplate(
            input_variables=[
                "other_side_role_name",
                "user_role_name",
                "topic",
                "transcript",
            ],
            template=summary_prompt,
        )

        llm_chain = LLMChain(llm=self.llm, prompt=prompt_template)

        summary = llm_chain.predict(
            other_side_role_name=self.other_side_role_name,
            user_role_name=self.user_role_name,
            topic=self.topic,
            transcript=transcript_str,
        )

        return summary
