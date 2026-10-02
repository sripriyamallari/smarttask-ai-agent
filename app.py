import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="SmartTask AI Agent",
    page_icon="🤖",
    layout="centered"
)

# Store tasks
if "tasks" not in st.session_state:
    st.session_state.tasks = []


# Calculator Tool
def calculator(expression):
    try:
        expression = expression.replace("calculate", "").strip()
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except:
        return "Please enter a valid calculation."


# Date and Time Tool
def get_current_datetime():
    return datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")


# Add Task Tool
def add_task(task):
    task = task.strip()

    if not task:
        return "Please enter a task."

    st.session_state.tasks.append(task)

    return f"✅ Task added successfully: {task}"


# View Tasks Tool
def view_tasks():
    if not st.session_state.tasks:
        return "📝 No tasks available."

    result = "📝 Your Tasks:\n\n"

    for i, task in enumerate(st.session_state.tasks, 1):
        result += f"{i}. {task}\n"

    return result


# AI Agent
def ai_agent(user_input):

    text = user_input.lower().strip()

    # Calculator
    if text.startswith("calculate"):
        expression = text.replace("calculate", "", 1).strip()

        return (
            "🧮 Calculator Tool\n\n"
            + "Result: "
            + calculator(expression)
        )

    # Date and Time
    elif "time" in text or "date" in text:

        return (
            "🕐 Date & Time Tool\n\n"
            + get_current_datetime()
        )

    # Add Task
    elif text.startswith("add task"):

        task = user_input[8:].strip()

        return add_task(task)

    # View Tasks
    elif "show tasks" in text or "view tasks" in text:

        return view_tasks()

    # Help
    elif text == "help":

        return """🤖 SmartTask AI Agent

Available commands:

🧮 calculate 25 * 4

🕐 what is the current time?

📝 add task Complete AI Agent project

📋 show tasks
"""

    # Unknown request
    else:

        return """🤖 I don't understand that request yet.

Try one of these:

• calculate 25 * 4
• what is the current time?
• add task Complete AI Agent project
• show tasks
"""


# UI
st.title("🤖 SmartTask AI Agent")

st.write(
    "AI Agent with Calculator, Date & Time, "
    "and Task Manager tools"
)

st.divider()

user_input = st.text_input(
    "Enter your task",
    placeholder="Example: calculate 25 * 4"
)

if st.button("Run Agent"):

    if user_input:

        response = ai_agent(user_input)

        st.success(response)

    else:

        st.warning("Please enter a task.")


st.divider()

st.subheader("📝 Current Tasks")

if st.session_state.tasks:

    for i, task in enumerate(st.session_state.tasks, 1):

        st.write(f"{i}. {task}")

else:

    st.write("No tasks added yet.")


st.divider()

st.caption(
    "SmartTask AI Agent | Module 5 - AI Agents, Tools & Automation"
)
