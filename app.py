import os
import json
import datetime
import ast
import operator
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(
    page_title="SmartTask AI Agent",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 SmartTask AI Agent")
st.write(
    "An AI agent with Calculator, Date & Time, and Task Manager tools."
)

# -----------------------------
# Gemini API
# -----------------------------

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.warning(
        "GEMINI_API_KEY is not configured. "
        "The application code is ready, but an API key is required to run it."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)

# -----------------------------
# Session State
# -----------------------------

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------
# Calculator Tool
# -----------------------------

def calculator(expression):
    """
    Safely calculate basic mathematical expressions.
    """

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg
    }

    def evaluate(node):

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid number")

        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)

            operation = allowed_operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operation")

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):
            operand = evaluate(node.operand)

            operation = allowed_operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operation")

            return operation(operand)

        raise ValueError("Invalid mathematical expression")

    try:
        tree = ast.parse(expression, mode="eval")
        return evaluate(tree.body)

    except Exception as e:
        return f"Calculation error: {e}"


# -----------------------------
# Date & Time Tool
# -----------------------------

def get_datetime():
    now = datetime.datetime.now()

    return {
        "date": now.strftime("%d-%m-%Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "day": now.strftime("%A")
    }


# -----------------------------
# Task Manager Tools
# -----------------------------

def add_task(task):
    task = task.strip()

    if task:
        st.session_state.tasks.append(task)

        return f"Task added successfully: {task}"

    return "Task cannot be empty."


def list_tasks():

    if not st.session_state.tasks:
        return "No tasks available."

    result = []

    for index, task in enumerate(st.session_state.tasks, start=1):
        result.append(f"{index}. {task}")

    return "\n".join(result)


def remove_task(task_number):

    try:
        index = int(task_number) - 1

        if index < 0 or index >= len(st.session_state.tasks):
            return "Invalid task number."

        removed = st.session_state.tasks.pop(index)

        return f"Task removed: {removed}"

    except Exception:
        return "Please provide a valid task number."


# -----------------------------
# Agent Tools
# -----------------------------

tools = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="calculator",
                description="Calculate a mathematical expression.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "expression": types.Schema(
                            type="STRING",
                            description="Mathematical expression such as 25*8"
                        )
                    },
                    required=["expression"]
                )
            ),

            types.FunctionDeclaration(
                name="get_datetime",
                description="Get the current date, time and day.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={}
                )
            ),

            types.FunctionDeclaration(
                name="add_task",
                description="Add a new task to the task list.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "task": types.Schema(
                            type="STRING",
                            description="The task to add"
                        )
                    },
                    required=["task"]
                )
            ),

            types.FunctionDeclaration(
                name="list_tasks",
                description="Show all saved tasks.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={}
                )
            ),

            types.FunctionDeclaration(
                name="remove_task",
                description="Remove a task using its task number.",
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "task_number": types.Schema(
                            type="STRING",
                            description="Task number to remove"
                        )
                    },
                    required=["task_number"]
                )
            )
        ]
    )
]


# -----------------------------
# Tool Execution
# -----------------------------

def execute_tool(name, args):

    if name == "calculator":
        return calculator(args["expression"])

    if name == "get_datetime":
        return get_datetime()

    if name == "add_task":
        return add_task(args["task"])

    if name == "list_tasks":
        return list_tasks()

    if name == "remove_task":
        return remove_task(args["task_number"])

    return "Unknown tool."


# -----------------------------
# AI Agent
# -----------------------------

SYSTEM_PROMPT = """
You are SmartTask AI Agent.

Your job is to understand the user's request, decide whether a tool is required,
use the correct tool, process the tool result, and provide a clear final answer.

Available tools:
1. calculator - mathematical calculations
2. get_datetime - current date and time
3. add_task - add tasks
4. list_tasks - display tasks
5. remove_task - remove tasks

Follow this workflow:

Understand Task
-> Decide Action
-> Use Tool if required
-> Process Result
-> Respond

Do not invent calculation results.
Use the calculator tool for calculations.

Use the task tools when the user wants to manage tasks.
Use the date/time tool when the user asks for current date or time.
"""


def run_agent(user_message):

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part(text=SYSTEM_PROMPT + "\n\nUser request:\n" + user_message)
            ]
        )
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            tools=tools,
            temperature=0.2
        )
    )

    # Handle tool calls
    if response.function_calls:

        tool_results = []

        for function_call in response.function_calls:

            name = function_call.name
            args = function_call.args

            result = execute_tool(name, args)

            tool_results.append(
                types.Part.from_function_response(
                    name=name,
                    response={
                        "result": result
                    }
                )
            )

        contents.append(response.candidates[0].content)

        contents.append(
            types.Content(
                role="tool",
                parts=tool_results
            )
        )

        final_response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        )

        return final_response.text

    return response.text


# -----------------------------
# Chat Interface
# -----------------------------

user_input = st.chat_input(
    "Ask SmartTask AI something..."
)

if user_input:

    st.session_state.chat_history.append(
        ("user", user_input)
    )

    with st.spinner("SmartTask Agent is thinking..."):

        try:
            answer = run_agent(user_input)

        except Exception as e:
            answer = f"Error: {e}"

    st.session_state.chat_history.append(
        ("assistant", answer)
    )


# -----------------------------
# Display Chat
# -----------------------------

for role, message in st.session_state.chat_history:

    with st.chat_message(role):
        st.write(message)


# -----------------------------
# Sidebar
# -----------------------------

with st.sidebar:

    st.header("🛠️ Available Tools")

    st.write("🧮 Calculator")
    st.write("🕒 Date & Time")
    st.write("➕ Add Task")
    st.write("📋 List Tasks")
    st.write("🗑️ Remove Task")

    st.divider()

    st.subheader("Current Tasks")

    if st.session_state.tasks:

        for index, task in enumerate(
            st.session_state.tasks,
            start=1
        ):
            st.write(f"{index}. {task}")

    else:
        st.write("No tasks yet.")
