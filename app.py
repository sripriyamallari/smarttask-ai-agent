
import os
import ast
import operator
from datetime import datetime

import streamlit as st
from google import genai
from google.genai import types


# ==========================================
# 1. PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="SmartTask AI Agent",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 SmartTask AI Agent")
st.caption("Your intelligent productivity assistant")


# ==========================================
# 2. API CONFIGURATION
# ==========================================

def get_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


API_KEY = get_api_key()
MODEL = "gemini-2.5-flash"

if not API_KEY:
    st.error(
        "Gemini API key is missing. "
        "Add GEMINI_API_KEY to Streamlit Secrets."
    )
    st.stop()

try:
    client = genai.Client(api_key=API_KEY)
except Exception as error:
    st.error(f"API configuration error: {error}")
    st.stop()


# ==========================================
# 3. SESSION STATE
# ==========================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "tasks" not in st.session_state:
    st.session_state.tasks = []


# ==========================================
# 4. CALCULATOR
# ==========================================

def calculate(expression):
    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.FloorDiv: operator.floordiv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Only numbers are allowed.")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in allowed_operators:
                raise ValueError("Unsupported operator.")

            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 100:
                raise ValueError("Exponent is too large.")

            return allowed_operators[op_type](left, right)

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in allowed_operators:
                raise ValueError("Unsupported operator.")
            return allowed_operators[op_type](evaluate(node.operand))

        raise ValueError("Invalid mathematical expression.")

    try:
        tree = ast.parse(expression, mode="eval")
        result = evaluate(tree.body)
        return str(result)
    except Exception as error:
        return f"Calculation error: {error}"


# ==========================================
# 5. DATE AND TIME
# ==========================================

def get_datetime():
    return datetime.now().astimezone().strftime(
        "%A, %d %B %Y, %I:%M:%S %p %Z"
    )


# ==========================================
# 6. TASK MANAGEMENT
# ==========================================

def add_task(task):
    task = task.strip()

    if not task:
        return "Task cannot be empty."

    st.session_state.tasks.append(task)
    return f"Task added successfully: {task}"


def list_tasks():
    tasks = st.session_state.tasks

    if not tasks:
        return "There are no tasks yet."

    return "\n".join(
        f"{i + 1}. {task}"
        for i, task in enumerate(tasks)
    )


def remove_task(number):
    tasks = st.session_state.tasks

    if number < 1 or number > len(tasks):
        return "Invalid task number."

    removed = tasks.pop(number - 1)
    return f"Task removed: {removed}"


# ==========================================
# 7. GEMINI TOOL DECLARATIONS
# ==========================================

tool_declarations = [
    types.FunctionDeclaration(
        name="calculator",
        description="Calculate a mathematical expression.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "expression": {
                    "type": "STRING",
                    "description": "Mathematical expression, e.g. 40*8"
                }
            },
            "required": ["expression"]
        }
    ),
    types.FunctionDeclaration(
        name="get_datetime",
        description="Get the current date and time.",
        parameters={
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    ),
    types.FunctionDeclaration(
        name="add_task",
        description="Add a task to the task list.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "task": {
                    "type": "STRING",
                    "description": "Task to add"
                }
            },
            "required": ["task"]
        }
    ),
    types.FunctionDeclaration(
        name="list_tasks",
        description="Show all saved tasks.",
        parameters={
            "type": "OBJECT",
            "properties": {},
            "required": []
        }
    ),
    types.FunctionDeclaration(
        name="remove_task",
        description="Remove a task by its number.",
        parameters={
            "type": "OBJECT",
            "properties": {
                "number": {
                    "type": "INTEGER",
                    "description": "Task number to remove"
                }
            },
            "required": ["number"]
        }
    )
]

tools = [
    types.Tool(function_declarations=tool_declarations)
]


# ==========================================
# 8. EXECUTE TOOLS
# ==========================================

def execute_tool(name, args):
    try:
        if name == "calculator":
            return calculate(args["expression"])

        elif name == "get_datetime":
            return get_datetime()

        elif name == "add_task":
            return add_task(args["task"])

        elif name == "list_tasks":
            return list_tasks()

        elif name == "remove_task":
            return remove_task(int(args["number"]))

        return "Unknown tool."

    except Exception as error:
        return f"Tool error: {error}"


# ==========================================
# 9. SYSTEM INSTRUCTIONS
# ==========================================

SYSTEM_PROMPT = """
You are SmartTask AI Agent, a helpful productivity assistant.

Available tools:
- calculator: Perform mathematical calculations.
- get_datetime: Get the current date and time.
- add_task: Add a task.
- list_tasks: Show all tasks.
- remove_task: Remove a task by number.

Rules:
1. Use the calculator for mathematical calculations.
2. Use task tools for task management.
3. Use get_datetime for current date and time.
4. Never claim an action succeeded unless the tool confirms it.
5. Be friendly, concise and accurate.
6. Explain tool results clearly to the user.
"""


# ==========================================
# 10. RUN GEMINI AGENT
# ==========================================

def run_agent(user_message):
    contents = []

    # Add previous conversation
    for message in st.session_state.chat_history:
        role = "model" if message["role"] == "assistant" else "user"

        contents.append(
            types.Content(
                role=role,
                parts=[
                    types.Part.from_text(text=message["content"])
                ]
            )
        )

    # Add current message
    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_message)
            ]
        )
    )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=tools,
        temperature=0.4
    )

    # Handle multiple tool-call rounds
    for _ in range(5):
        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config
        )

        if not response.candidates:
            return "Gemini returned no response. Please try again."

        candidate = response.candidates[0]
        contents.append(candidate.content)

        function_calls = [
            part.function_call
            for part in candidate.content.parts
            if part.function_call is not None
        ]

        # No tools requested: return final answer
        if not function_calls:
            answer = response.text
            return answer or "No text response was received."

        # Execute all requested tools
        response_parts = []

        for call in function_calls:
            name = call.name
            args = dict(call.args or {})

            result = execute_tool(name, args)

            response_parts.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": result}
                )
            )

        # Send results back to Gemini
        contents.append(
            types.Content(
                role="user",
                parts=response_parts
            )
        )

    return "The agent reached its tool-call limit. Please try again."


# ==========================================
# 11. DISPLAY CHAT HISTORY
# ==========================================

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


# ==========================================
# 12. USER INPUT
# ==========================================

user_input = st.chat_input("Ask SmartTask AI something...")

if user_input:
    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                answer = run_agent(user_input)

            st.markdown(answer)

        except Exception as error:
            answer = (
                "Sorry, the AI request failed. "
                "Please check your API key, model, "
                "quota and app logs.\n\n"
                f"Error: {error}"
            )
            st.error(answer)

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


# ==========================================
# 13. SIDEBAR
# ==========================================

with st.sidebar:
    st.header("🛠️ Agent Tools")

    st.subheader("🧮 Calculator")
    expression = st.text_input(
        "Enter calculation",
        placeholder="40*8",
        key="calculator_input"
    )

    if st.button("Calculate", key="calculate_button"):
        if expression.strip():
            st.success(calculate(expression))

    st.divider()

    st.subheader("🕒 Date & Time")
    if st.button("Get Current Date & Time"):
        st.info(get_datetime())

    st.divider()

    st.subheader("➕ Add Task")
    new_task = st.text_input(
        "Enter a task",
        key="new_task"
    )

    if st.button("Add Task"):
        if new_task.strip():
            st.success(add_task(new_task))
            st.rerun()
        else:
            st.warning("Enter a task first.")

    st.divider()

    st.subheader("📋 Current Tasks")

    if st.session_state.tasks:
        for i, task in enumerate(
            st.session_state.tasks,
            start=1
        ):
            st.write(f"{i}. {task}")
    else:
        st.caption("No tasks yet.")

    st.divider()

    st.subheader("🗑️ Remove Task")
    if st.session_state.tasks:
        task_number = st.number_input(
            "Task number",
            min_value=1,
            max_value=len(st.session_state.tasks),
            step=1
        )

        if st.button("Remove Selected Task"):
            st.success(remove_task(int(task_number)))
            st.rerun()

    st.divider()

    if st.button("Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

    st.caption("SmartTask AI Agent")
    st.caption("Powered by Gemini and Streamlit")
