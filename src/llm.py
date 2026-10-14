from ollama import chat
from tools import search_runbooks

available_tools = {
    'search_runbooks': search_runbooks,
}

SYSTEM_PROMPT = "You are an AI assistant that helps with searching runbooks for troubleshooting steps and incident procedures."

userPrompt =""


messages = []  # Initialize empty history
messages.append({"role": "system", "content": SYSTEM_PROMPT})
# Each turn:

messages.append({"role": "user", "content": userPrompt})
response = chat(model='llama3', messages=messages, tools=available_tools.values(), think=True)
messages.append({"role": "assistant", "content": response})

