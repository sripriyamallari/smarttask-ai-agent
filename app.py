import ast
import datetime
import operator
import streamlit as st
from google import genai
from google.genai import types


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="SmartTask AI Agent",
    page_icon="🤖",
    layout="centered"
)


# =========================================================
# TITLE
# =========================================================

st.title("🤖 SmartTask AI Agent")

st.write(
    "An AI Agent with Calculator, Date & Time, and Task Manager tools."
)


# =========================================================
# GEMINI API KEY
# =========================================================

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    API_KEY = ""

if not API_KEY:
    st.error(
        "GEMINI_API_KEY is not configured. "
        "Please add it in Streamlit → Manage app → Settings → Secrets."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)


# =========================================================
# SESSION STATE
# =========================================================

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# =========================================================
# CALCULATOR TOOL
# =========================================================

def calculator(expression: str):
    """Safely calculate a basic mathematical expression."""

    allowed_operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
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
                raise ValueError("Unsupported operator")

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)

            operation = allowed_operators.get(type(node.op))

            if operation is None:
                raise ValueError("Unsupported operator")

            return operation(value)

        raise ValueError("Invalid mathematical expression")

    try:
        tree = ast.parse(expression, mode="eval")
        result = evaluate(tree.body)

        return {
            "success": True,
            "result": result
        }

    except Exception as error:
        return {
            "success": False,
            "error": str(error)
        }


# =========================================================
# DATE & TIME TOOL
# =========================================================

def get_datetime():
    """Get the current date, time, and day."""

    now = datetime.datetime.now()

    return {
        "date": now.strftime("%d-%m-%Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "day": now.strftime("%A")
    }


# =========================================================
# ADD TASK TOOL
# =========================================================

def add_task(task: str):
    """Add a new task to the task list."""

    task = task.strip()

    if not task:
        return {
            "success": False,
            "message": "Task cannot be empty."
        }

    st.session_state.tasks.append(task)

    return {
        "success": True,
        "message": f"Task added successfully: {task}",
        "total_tasks": len(st.session_state.tasks)
    }


# =========================================================
# LIST TASKS TOOL
# =========================================================

def list_tasks():
    """Show all saved tasks."""

    if not st.session_state.tasks:
        return {
            "success": True,
            "tasks": [],
            "message": "No tasks available."
        }

    return {
        "success": True,
        "tasks": [
            {
                "number": index,
                "task": task
            }
            for index, task in enumerate(
                st.session_state.tasks,
                start=1
            )
        ]
    }


# =========================================================
# REMOVE TASK TOOL
# =========================================================

def remove_task(task_number: int):
    """Remove a task using its task number."""

    try:
        index = int(task_number) - 1

        if index < 0 or index >= len(st.session_state.tasks):
            return {
                "success": False,
                "message": "Invalid task number."
            }

        removed_task = st.session_state.tasks.pop(index)

        return {
            "success": True,
            "message": f"Task removed: {removed_task}"
        }

    except Exception:
        return {
            "success": False,
            "message": "Please provide a valid task number."
        }


# =========================================================
# TOOL DECLARATIONS
# =========================================================

calculator_tool = {
    "name": "calculator",
    "description": (
        "Calculate a mathematical expression such as "
        "40*8, 100/5, or (20+10)*2."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "The mathematical expression to calculate."
            }
        },
        "required": ["expression"]
    }
}


datetime_tool = {
    "name": "get_datetime",
    "description": (
        "Get the current date, current time, and day of the week."
    ),
    "parameters": {
        "type": "object",
        "properties": {}
    }
}


add_task_tool = {
    "name": "add_task",
    "description": "Add a new task to the user's task list.",
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "The task that should be added."
            }
        },
        "required": ["task"]
    }
}


list_tasks_tool = {
    "name": "list_tasks",
    "description": "Display all tasks currently stored in the task list.",
    "parameters": {
        "type": "object",
        "properties": {}
    }
}


remove_task_tool = {
    "name": "remove_task",
    "description": "Remove a task using its task number.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_number": {
                "type": "integer",
                "description": "The number of the task to remove."
            }
        },
        "required": ["task_number"]
    }
}


tools = types.Tool(
    function_declarations=[
        calculator_tool,
        datetime_tool,
        add_task_tool,
        list_tasks_tool,
        remove_task_tool
    ]
)


# =========================================================
# EXECUTE TOOLS
# =========================================================

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

    return {
        "success": False,
        "message": "Unknown tool."
    }


# =========================================================
# AI AGENT
# =========================================================

SYSTEM_PROMPT = """
You are SmartTask AI Agent.

Your workflow is:

1. Understand the user's task.
2. Decide what action is required.
3. Use a tool when necessary.
4. Process the tool result.
5. Give the user a clear final response.

Available tools:

- calculator
- get_datetime
- add_task
- list_tasks
- remove_task

IMPORTANT RULES:

Use the calculator tool for mathematical calculations.

Use get_datetime when the user asks for the current date,
current time, or day.

Use add_task when the user wants to add a task.

Use list_tasks when the user wants to see their tasks.

Use remove_task when the user wants to remove a task.

Never invent calculation results.

Be concise, helpful, and friendly.
"""


def run_agent(user_message):

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=SYSTEM_PROMPT
                    + "\n\nUser request:\n"
                    + user_message
                )
            ]
        )
    ]

    config = types.GenerateContentConfig(
        tools=[tools]
    )

    # -----------------------------------------------------
    # FIRST MODEL CALL
    # -----------------------------------------------------

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=contents,
        config=config
    )

    # -----------------------------------------------------
    # CHECK FOR TOOL CALLS
    # -----------------------------------------------------
    # CHECK FOR TOOL CALLS

    function_calls = response.function_calls

    if not function_calls:
        return response.text or "No response received."

    contents.append(response.candidates[0].content)

    function_response_parts = []

    for function_call in function_calls:
        tool_name = function_call.name
        tool_args = function_call.args or {}

        result = execute_tool(tool_name, tool_args)

        function_response_parts.append(
            types.Part.from_function_response(
                name=tool_name,
                response={"result": result}
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=function_response_parts
        )
    )

    final_response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=contents,
        config=config
    )

    return final_response.text or "Task completed." -----------------------------------------------------
    # EXECUTE EACH TOOL
    # -----------------------------------------------------

    function_response_parts = []

    for function_call in function_calls:

        tool_name = function_call.name
        tool_args = function_call.args or {}

        result = execute_tool(
            tool_name,
            tool_args
        )
function_response_parts.append(
    types.Part.from_function_response(
        name=tool_name,
        response={
            "result": result
        }
    )
)

        

    # -----------------------------------------------------
    # SEND TOOL RESULTS BACK TO GEMINI
    # -----------------------------------------------------

    contents.append(
        types.Content(
            role="user",
            parts=function_response_parts
        )
    )

    final_response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=contents,
        config=config
    )

    return final_response.text


# =========================================================
# CHAT INPUT
# =========================================================

user_input = st.chat_input(
    "Ask SmartTask AI something..."
)


# =========================================================
# PROCESS USER MESSAGE
# =========================================================

if user_input:

    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": user_input
        }
    )

    with st.spinner("🤖 SmartTask Agent is thinking..."):

        try:

            answer = run_agent(user_input)

        except Exception as error:

            answer = f"Error: {error}"

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )


# =========================================================
# DISPLAY CHAT
# =========================================================

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.write(message["content"])


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("🛠️ Available Tools")

    st.write("🧮 Calculator")
    st.write("🕒 Date & Time")
    st.write("➕ Add Task")
    st.write("📋 List Tasks")
    st.write("🗑️ Remove Task")

    st.divider()

    st.subheader("📋 Current Tasks")

    if st.session_state.tasks:

        for number, task in enumerate(
            st.session_state.tasks,
            start=1
        ):
            st.write(f"{number}. {task}")

    else:

        st.write("No tasks yet.")

    st.divider()

    st.caption("SmartTask AI Agent • GenAI + Tools")