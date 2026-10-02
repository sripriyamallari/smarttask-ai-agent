
import gradio as gr
from datetime import datetime

tasks = []

def calculator(expression):
    try:
        expression = expression.replace("calculate", "").strip()
        result = eval(expression, {"__builtins__": {}}, {})
        return str(result)
    except:
        return "Please enter a valid calculation."

def get_current_datetime():
    return datetime.now().strftime("%d-%m-%Y %I:%M:%S %p")

def add_task(task):
    task = task.strip()

    if not task:
        return "Please enter a task."

    tasks.append(task)
    return f"Task added: {task}"

def view_tasks():
    if not tasks:
        return "No tasks available."

    result = "Your Tasks:\n"
    for i, task in enumerate(tasks, 1):
        result += f"{i}. {task}\n"

    return result

def ai_agent(user_input):

    text = user_input.lower().strip()

    if text.startswith("calculate"):
        expression = text.replace("calculate", "", 1).strip()
        return "Calculator Result: " + calculator(expression)

    elif "time" in text or "date" in text:
        return "Current Date & Time: " + get_current_datetime()

    elif text.startswith("add task"):
        task = user_input[8:].strip()
        return add_task(task)

    elif "view tasks" in text or "show tasks" in text:
        return view_tasks()

    elif text == "help":
        return """SmartTask AI Agent

Try:
calculate 25 * 4
what is the current time?
add task Complete my project
show tasks
"""

    else:
        return """I don't understand that request yet.

Try:
calculate 25 * 4
what is the current time?
add task Complete my project
show tasks
"""

demo = gr.Interface(
    fn=ai_agent,
    inputs=gr.Textbox(
        label="Enter your task",
        placeholder="Example: calculate 25 * 4"
    ),
    outputs=gr.Textbox(label="AI Agent Response"),
    title="SmartTask AI Agent",
    description="AI Agent with Calculator, Date & Time, and Task Manager tools"
)

demo.launch(share=True)
