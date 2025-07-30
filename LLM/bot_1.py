
from typing import Annotated

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from llm_config import llm
from IPython.display import Image, display

class State(TypedDict):
    messages: Annotated[list, add_messages]


graph_builder = StateGraph(State)


def chatbot(state: State):
    print("------")
    print(len(state["messages"]))
    return {"messages": [llm.invoke(state["messages"])]}


    

def should_continue(state: State):
    last_message = state["messages"][-1]["content"].lower()
    if last_message in {"exit", "quit", "q"}:
        return "end"
    return "chatbot"  # loop again


# The first argument is the unique node name
# The second argument is the function or object that will be called whenever
# the node is used.
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")

graph_builder.add_conditional_edges(
    "chatbot",
    should_continue,
    {
        "chatbot": "chatbot",  # loop
        "end": END             # finish
    }
)

graph = graph_builder.compile()


with open("graph.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())


state = {"messages": []}
while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        state["messages"].append({"role": "user", "content": user_input})
        state = graph.invoke(state)
        last_message = state["messages"][-1]
        print("Assistant:", last_message["content"])
    except:
        print("An error occurred. Please try again.")
        break