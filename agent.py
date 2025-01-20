import os
import streamlit as st
from dataclasses import dataclass
from typing import Annotated, Sequence, Optional

from langchain.callbacks.base import BaseCallbackHandler
# from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
# from langchain_community.llms import Replicate
import os

from tools import retriever_tool
from tools import search, sql_executor_tool
from PIL import Image
from io import BytesIO


@dataclass
class MessagesState:
    messages: Annotated[Sequence[BaseMessage], add_messages]


memory = MemorySaver()


@dataclass
class ModelConfig:
    model_name: str
    api_key: str
    base_url: Optional[str] = None


model_configurations = {
    "gpt-4o-mini": ModelConfig(
        model_name="gpt-4o-mini",
        api_key=os.getenv("OPENAI_API_KEY")
    ),
    # "Gemini Flash 1.5": ModelConfig(
    #     model_name="gemini-1.5-flash",
    #     api_key=st.secrets["GEMINI_API_KEY"],
    #     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    # ),
    # # "Mistral 7B": ModelConfig(
    # #     model_name="mistralai/mistral-7b-v0.1", api_key=st.secrets["REPLICATE_API_TOKEN"]
    # # ),
    # "Qwen 2.5": ModelConfig(
    #     model_name="accounts/fireworks/models/qwen2p5-coder-32b-instruct",
    #     api_key=st.secrets["FIREWORKS_API_KEY"],
    #     base_url="https://api.fireworks.ai/inference/v1",
    # ),
    # "Gemini Exp 1206": ModelConfig(
    #     model_name="gemini-exp-1206",
    #     api_key=st.secrets["GEMINI_API_KEY"],
    #     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    # ),
}
sys_msg = SystemMessage(
    content="""You're an AI assistant specializing in data analysis with Snowflake SQL. When providing responses, strive to exhibit friendliness and adopt a conversational tone, similar to how a friend or tutor would communicate. Do not ask the user for schema or database details. You have access to the following tools:
    - Database_Schema: This tool allows you to search for database schema details when needed to generate the SQL code.
    - Internet_Search: This tool allows you to search the internet for snowflake sql related information when needed to generate the SQL code.
    - Snowflake_SQL_Executor: This tool allows you to execute snowflake sql queries when needed to generate the SQL code. You only have read access to the database, do not modify the database in any way.

    Make sure to always return both the SQL code and the result of the query
    """
)
# tools = [retriever_tool, search, sql_executor_tool]
tools = [search, sql_executor_tool]


def create_agent(callback_handler: BaseCallbackHandler, model_name: str) -> StateGraph:
    config = model_configurations.get(model_name)
    if not config:
        raise ValueError(f"Unsupported model name: {model_name}")

    if not config.api_key:
        raise ValueError(
            f"API key for model '{model_name}' is not set. Please check your environment variables or secrets configuration.")

    llm = ChatOpenAI(
        model=config.model_name,
        api_key=config.api_key,
        callbacks=[callback_handler],
        streaming=True,
        base_url=config.base_url,
        temperature=0.01,
        default_headers={"HTTP-Referer": "https://snowchat.streamlit.app/", "X-Title": "Snowchat"},
    )

    llm_with_tools = llm.bind_tools(tools)

    def llm_agent(state: MessagesState):
        return {"messages": [llm_with_tools.invoke([sys_msg] + state.messages)]}

    builder = StateGraph(MessagesState)
    builder.add_node("llm_agent", llm_agent)
    builder.add_node("tools", ToolNode(tools))
    builder.add_edge(START, "llm_agent")
    builder.add_conditional_edges("llm_agent", tools_condition)
    builder.add_edge("tools", "llm_agent")

    react_graph = builder.compile(checkpointer=memory)

    # png_data = react_graph.get_graph(xray=True).draw_mermaid_png()
    # with open("graph.png", "wb") as f:
    #     f.write(png_data)

    # image = Image.open(BytesIO(png_data))
    # st.image(image, caption="React Graph")

    return react_graph
