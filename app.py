import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(page_title="SmartCoder AI", layout="wide")
st.title("🤖 SmartCoder AI — Code & Test Case Generator")

LLM_MODELS = {
    "Gemini (Free)": {
        "model": ["gemini-2.0-flash-lite","gemini-2.0-flash","gemini-1.5-flash"],
        "api_key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "requires_key": False
    },
    "Claude (Paid)": {
        "model": ["claude-3-7-sonnet-20250219","claude-3-5-haiku-latest","claude-3-opus-latest"],
        "api_key_env": None,
        "base_url": "https://api.anthropic.com/v1/",  # Example proxy
        "requires_key": True
    },
    "ChatGPT (Paid)": {
        "model": ["gpt-4o","gpt-4.1","gpt-4.1-mini","gpt-4.1-nano","o4-mini","gpt-3.5-turbo"],
        "api_key_env": None,
        "base_url": "https://api.openai.com/v1/",
        "requires_key": True
    },
    "Groq (Paid)": {
        "model": ["gemma2-9b-it","llama-3.3-70b-versatile","llama-3.1-8b-instant","llama-guard-3-8b","llama3-70b-8192","llama3-8b-8192","llama3-8b-8192"],
        "api_key_env": None,
        "base_url": "https://api.groq.com/openai/v1/", 
        "requires_key": True
    },
}

st.sidebar.header("⚙️ LLM Settings")

llm_providers = list(LLM_MODELS.keys()) + ["Other (Custom)"]
selected_provider = st.sidebar.selectbox("Select LLM Provider", llm_providers)

if selected_provider == "Other (Custom)":
    custom_llm_name = st.sidebar.text_input("🔤 Custom LLM Name")
    custom_base_url = st.sidebar.text_input("🌐 Base URL")
    model_options = ["Other"]
    selected_model_option = "Other"
else:
    provider_info = LLM_MODELS[selected_provider]
    model_options = provider_info["model"] + ["Other"]
    selected_model_option = st.sidebar.selectbox("Select Model Version", model_options)

# If model is "Other" → ask for input
if selected_model_option == "Other":
    custom_model = st.sidebar.text_input("🧠 Enter Custom Model Name")
else:
    custom_model = selected_model_option

# Get API Key
if selected_provider == "Other (Custom)" or LLM_MODELS.get(selected_provider, {}).get("requires_key", False):
    user_api_key = st.sidebar.text_input("🔑 API Key", type="password")
else:
    env_key = LLM_MODELS[selected_provider]["api_key_env"]
    user_api_key = os.getenv(env_key)

# Get Base URL
base_url = custom_base_url if selected_provider == "Other (Custom)" else LLM_MODELS[selected_provider]["base_url"]
api_key = user_api_key


# === Session Storage ===
if "history" not in st.session_state:
    st.session_state.history = []

# === Input Query ===
query = st.text_area("💬 Enter your coding query",placeholder="Write a Python code for adding two numbers.", height=150)
run_btn = st.button("🚀 Generate")

# === Tool Definitions ===
def run_command(command_input):
    command = command_input.get("command")
    output = os.popen(command).read()
    return f"Command Output:\n{output}"

def write_to_file(input_data):
    filename = input_data.get("filename")
    content = input_data.get("content")
    return f"📝 **Filename:** `{filename}`\n```python\n{content}\n```"

available_tools = {
    "run_command": run_command,
    "write_to_file": write_to_file,
}

# === System Prompt ===
sys_message = """
You are an helpful AI Assistant who is specialized in solving competitive coding problems in a optimized way for the given problem statement,
By default write code in python if user asks for any specific language then write in that language.
format the code based on the language you wrote.
make sure to import necessary libraries
Explore examples to understand the input-output relationship and identify potential edge cases
Develop a optimized solution for time and space complexity, and consider alternative algorithms if necessary
Important thing is it is not supposed to give time limit exceeded write very optimized code
Walk through your code with examples to test and debug, and discuss your thought process.
Once you generate the final implementation, write it to a file.
After generating code next step is to write unittest cases for the generated code.
Finally give the command to the user how to run the code 

rules:
1. follow the output json format
2. Always perform one step at a time and wait for next input
3. carefully analyse the user query

Always output json format:{{"step":"string",
"content":"string",
"function":"the name of the function if the step is action",
"input":"the input parameter for the function"}}

Available_Tools:
    - run_command: Takes a command as input to execute on system and returns output and when adding any code in the file check and add in specific coding format in the file
    - write_to_file: Takes code and append it into a file

example: 
user query: write a code for adding two numbers
output:{{"step":"plan","content":"The user is asking for code that adds two numbers and return the output"}}
output:{{"step":"plan","content":"To solve this, we need to use addition operator."}}
output:{{"step":"observe","content":"from typing import int\n class Solution:\n    def add(self, num1: int, num2: int) -> int:\n        return num1+num2 This is the optimized code to add two numbers"}}
output:{{"step":"action", "function":"write_to_file", "input":{{"filename": "add.py", "content": "class Solution:\n    def add(self, num1: int, num2: int) -> int:\n        return num1+num2"}}}}
output:{{"step":"observe","content":"successfully written code into add.py file you can run it using python add.py command"}}
output:{{"step":"plan","content":"Now I will start writing testcases for the generated code"}}
output:{{"step":"action", "function":"write_to_file", "input":{{"filename": "test_add.py", "content": "import unittest\n\n from add import Solution \n  TestAddFunction(unittest.TestCase):\n    def setUp(self):\n    self.solution = Solution()    def test_normal_cases(self):\n        self.assertEqual(self.solution.add(1, 2), 3)\n        self.assertEqual(self.solution.add(-1, 1), 0)\n        self.assertEqual(self.solution.add(0, 0), 0)\n    \n    def test_edge_cases(self):\n        self.assertEqual(self.solution.add(999999, 1), 1000000)\n        self.assertEqual(self.solution.add(-999999, 999999), 0)\n    \n    def test_error_handling(self):\n        with self.assertRaises(TypeError):\n            self.solution.add('a', 1)"}}}}
output:{{"step":"output","content":"successfully written test cases into test_add.py file you can run it using python test_add.py command"}}
"""

# === Run LLM ===
if run_btn and query.strip():
    if not api_key:
        st.error("❌ API key missing or not set in environment.")
        st.stop()

    client = OpenAI(api_key=api_key, base_url=base_url)
    messages = [{"role": "system", "content": sys_message}, {"role": "user", "content": query}]
    logs = []
    log_placeholder = st.empty()


    try:
        while True:
            response = client.chat.completions.create(
                model=custom_model,
                response_format={"type": "json_object"},
                messages=messages
            )
            parsed_res = json.loads(response.choices[0].message.content)
            messages.append({"role": "assistant", "content": json.dumps(parsed_res)})

            step = parsed_res.get("step")
            content = parsed_res.get("content", "")

            if step == "plan":
                logs.append(f"🧠 **Plan**:\n{content}")
                log_placeholder.markdown("\n\n".join(logs), unsafe_allow_html=True)
            elif step == "observe":
                logs.append(f"👀 **Observation**:\n{content}")
                log_placeholder.markdown("\n\n".join(logs), unsafe_allow_html=True)
            elif step == "action":
                tool = parsed_res.get("function")
                tool_input = parsed_res.get("input")

                if tool in available_tools:
                    result = available_tools[tool](tool_input)
                    logs.append(f"⚙️ **Action: `{tool}`**\n\n{result}")
                    log_placeholder.markdown("\n\n".join(logs), unsafe_allow_html=True)
                    messages.append({
                        "role": "assistant",
                        "content": json.dumps({"step": "observe", "content": result})
                    })
                else:
                    logs.append(f"❌ Unknown tool: {tool}")
                    log_placeholder.markdown("\n\n".join(logs), unsafe_allow_html=True)
                    break
            elif step == "output":
                logs.append(f"🤖 **Final Output**:\n{content}")
                log_placeholder.markdown("\n\n".join(logs), unsafe_allow_html=True)
                break
            else:
                logs.append(f"⚠️ Unexpected step: {step}")
                log_placeholder.markdown("\n\n".join(logs), unsafe_allow_html=True)
                break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state.history.insert(0, {"query": query, "log": logs, "time": timestamp})

    except Exception as e:
        st.error(f"❌ Error: {e}")

st.markdown("## 📤 Output Console")
if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
        st.markdown("---")
        st.markdown(f"### ⏱️ Query Time: {item['time']}")
        st.markdown(f"**🔍 Query:** `{item['query']}`")
        for log in item["log"]:
            st.markdown(log, unsafe_allow_html=True)
else:
    st.info("No results yet. Submit a query above.")
