from turtle import update
from typing import Annotated

from langchain.chat_models import init_chat_model
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from llm_config import llm
from langgraph.checkpoint.memory import InMemorySaver
from IPython.display import display, Image
from langchain_core.messages import HumanMessage, AIMessage
from typing import Literal




class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)
memory = InMemorySaver()


def chatbot(state: State):

    return {"messages": [llm.invoke(state["messages"])]}

def user_input(state: State):

    user_input = input("\n\nUser: ")
    return {"messages": [HumanMessage(content= user_input)]}


def should_continue(state: State) -> Literal["chatbot", END]:
    last_user_message = state["messages"][-1]
    if last_user_message.content.lower() in ["quit", "exit", "q"]:
        print("Exiting chat...")
        return END
    return "chatbot"

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("user_input", user_input)
graph_builder.add_edge(START, "user_input")
graph_builder.add_conditional_edges("user_input", should_continue)
graph_builder.add_edge("chatbot", "user_input")

graph = graph_builder.compile()

image_data = graph.get_graph().draw_mermaid_png()
# save the image to a file
with open("graph.png", "wb") as f:
    f.write(image_data)


def run_chat():

    for chunk, meta in graph.stream(  {"messages": []},stream_mode="messages"):

        if meta["langgraph_node"] != "chatbot":
            print("\nChatbot: ", end='', flush=True)
            continue

        print(chunk.content if hasattr(chunk, "content") else str(chunk), end='', flush=True)



run_chat()