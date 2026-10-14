from ollama import chat
from tools import search_runbooks

available_tools = {
    'search_runbooks': search_runbooks
}
messages = []  # Initialize empty history

# Each turn:
messages.append({"role": "user", "content": user_input})
response = chat(model='llama3', messages=messages, tools=available_tools.values(), think=True)
messages.append({"role": "assistant", "content": response})

