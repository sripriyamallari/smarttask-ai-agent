
import ast
import operator
import datetime
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
# 2. GEMINI API CONFIGURATION
# ==========================================

try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
except (KeyError, FileNotFoundError):
    API_KEY = ""

if not API_KEY:
    st.error(
        "Gemini API key is missing. "
        "Add GEMINI_API_KEY in Streamlit Secrets."
    )
    st.stop()

client = genai.Client(api_key=API_KEY)

# Change this only if this model is unavailable
# for your API key.
MODEL = "gemini-3.8-flash"


# ==========================================
# 3. SESSION STATE
# ==========================================

if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# ==========================================
# 4. CALCULATOR TOOL
# ==========================================

def calculator(expression):
    """Safely calculate basic arithmetic."""

    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos
    }

    def evaluate(node):
        if isinstance(node, ast.Constant):
            if type(node.value) in (int, float):
                return node.value
            raise ValueError("Invalid number")

        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Pow) and abs(right) > 10:
                raise ValueError("Exponent is too large")

            operation = operators.get(type(node.op))
            if operation is None:
                raise ValueError("Unsupported operator")

            result = operation(left, right)

            if isinstance(result, complex):
                raise ValueError("Complex results are not supported")

            if isinstance(result, (int, float)) and abs(result) > 1e100:
                raise ValueError("Result is too large")

            return result

        if isinstance(node, ast.UnaryOp):
            operation = operators.get(type(node.op))
            if operation is None:
                raise ValueError("Unsupported operator")
            return operation(evaluate(node.operand))

        raise ValueError("Invalid mathematical expression")

    try:
        tree = ast.parse(expression, mode="eval")
        result = evaluate(tree.body)
        return {"success": True, "result": result}
    except Exception as error:
        return {"success": False, "error": str(error)}


# ==========================================
# 5. DATE AND TIME TOOL
# ==========================================

def get_datetime():
    """Get current server date and time."""

    now = datetime.datetime.now().astimezone()

    return {
        "date": now.strftime("%d-%m-%Y"),
        "time": now.strftime("%I:%M:%S %p"),
        "day": now.strftime("%A"),
        "timezone": str(now.tzinfo)
    }


# ==========================================
# 6. TASK MANAGER TOOLS
# ==========================================

def add_task(task):
    """Add a task."""

    task = task.strip()

    if not task:
        return {"success": False, "message": "Task is empty."}

    if len(task) > 300:
        return {"success": False, "message": "Task is too long."}

    st.session_state.tasks.append(task)

    return {
        "success": True,
        "message": "Task added successfully.",
        "task": task
    }


def list_tasks():
    """List all tasks."""

    return {
        "tasks": [
            {"number": i, "task": task}
            for i, task in enumerate(
                st.session_state.tasks, start=1
            )
        ]
    }


def remove_task(task_number):
    """Remove a task by number."""

    try:
        index = int(task_number) - 1

        if index < 0 or index >= len(st.session_state.tasks):
            return {
                "success": False,
                "message": "Invalid task number."
            }

        removed = st.session_state.tasks.pop(index)

        return {
            "success": True,
            "message": "Task removed.",
            "task": removed
        }

    except (ValueError, TypeError):
        return {
            "success": False,
            "message": "Provide a valid task number."
        }


# ==========================================
# 7. TOOL DECLARATIONS
# ==========================================

def parameter_schema(properties, required=None):
    return types.Schema(
        type="OBJECT",
        properties=properties,
        required=required or []
    )


tools = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="calculator",
                description="Calculate basic arithmetic expressions.",
                parameters=parameter_schema(
                    {
                        "expression": types.Schema(
                            type="STRING",
                            description="Example: 25*8"
                        )
                    },
                    ["expression"]
                )
            ),
            types.FunctionDeclaration(
                name="get_datetime",
                description="Get current date, time and day.",
                parameters=parameter_schema({})
            ),
            types.FunctionDeclaration(
                name="add_task",
                description="Add a task to the user's task list.",
                parameters=parameter_schema(
                    {
                        "task": types.Schema(
                            type="STRING",
                            description="Task to add"
                        )
                    },
                    ["task"]
                )
            ),
            types.FunctionDeclaration(
                name="list_tasks",
                description="Show all tasks in the task list.",
                parameters=parameter_schema({})
            ),
            types.FunctionDeclaration(
                name="remove_task",
                description="Remove a task by its number.",
                parameters=parameter_schema(
                    {
                        "task_number": types.Schema(
                            type="INTEGER",
                            description="Number of task to remove"
                        )
                    },
                    ["task_number"]
                )
            )
        ]
    )
]


# ==========================================
# 8. TOOL EXECUTION
# ==========================================

def execute_tool(name, args):
    """Run the selected tool."""

    try:
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

        return {"error": "Unknown tool."}

    except Exception as error:
        return {"error": str(error)}


# ==========================================
# 9. AI AGENT
# ==========================================

SYSTEM_PROMPT = """
You are SmartTask AI Agent, a helpful productivity assistant.

Your workflow:
1. Understand the user's request.
2. Decide which action is needed.
3. Call the appropriate tool when necessary.
4. Read and process the tool result.
5. Give a clear final answer.

Available tools:
- calculator: mathematical calculations
- get_datetime: current date and time
- add_task: add a task
- list_tasks: show tasks
- remove_task: delete a task by number

Rules:
- Always use the calculator for calculations.
- Use task tools for task management.
- Never claim a task was added or removed unless
  the tool confirms it.
- Never invent tool results.
- Be friendly, concise and accurate.
"""


def run_agent(user_message):
    """Run the Gemini agent and process tool calls."""

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
        tools=tools
    )

    # Allow several tool-call rounds.
    for _ in range(5):

        response = client.models.generate_content(
            model=MODEL,
            contents=contents,
            config=config
        )

        candidate = (
            response.candidates[0]
            if response.candidates
            else None
        )

        if candidate is None or candidate.content is None:
            return response.text or "No response received."

        # Keep the model response in the conversation.
        contents.append(candidate.content)

        function_calls = response.function_calls or []

        # No more tools needed.
        if not function_calls:
            return response.text or "Task completed."

        function_response_parts = []

        # Execute requested tools.
        for function_call in function_calls:
            name = function_call.name
            args = dict(function_call.args or {})

            result = execute_tool(name, args)

            function_response_parts.append(
                types.Part.from_function_response(
                    name=name,
                    response={"result": result}
                )
            )

        # Send tool results back to Gemini.
        contents.append(
            types.Content(
                role="user",
                parts=function_response_parts
            )
        )

    return "The agent reached its tool-call limit. Please try again."


# ==========================================
# 10. CHAT INPUT
# ==========================================

user_input = st.chat_input(
    "Ask SmartTask AI something..."
)

if user_input:
    st.session_state.chat_history.append(
        {"role": "user", "content": user_input}
    )

    with st.spinner("🤖 Agent is thinking..."):
        try:
            answer = run_agent(user_input)
        except Exception as error:
            # Do not expose credentials or sensitive details.
            answer = (
                "Sorry, the AI request failed. "
                "Please check the model, API key, "
                "quota and app logs."
            )
            st.error(f"Request error: {type(error).__name__}")

    st.session_state.chat_history.append(
        {"role": "assistant", "content": answer}
    )


# ==========================================
# 11. DISPLAY CHAT
# ==========================================

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])


# ==========================================
# 12. SIDEBAR
# ==========================================

with st.sidebar:
    st.header("🛠️ Agent Tools")

    st.write("🧮 Calculator")
    st.write("🕒 Date & Time")
    st.write("➕ Add Task")
    st.write("📋 List Tasks")
    st.write("🗑️ Remove Task")

    st.divider()

    st.subheader("📋 Current Tasks")

    if st.session_state.tasks:
        for i, task in enumerate(
            st.session_state.tasks, start=1
        ):
            st.write(f"{i}. {task}")
    else:
        st.caption("No tasks yet.")

    st.divider()

    if st.button("Clear chat"):
        st.session_state.chat_history = []
        st.rerun()

    st.caption("SmartTask AI Agent")
    st.caption("Powered by Gemini and Streamlit")
