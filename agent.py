import streamlit as st
from google import genai

from tools import (
    calculator,
    create_study_plan,
    get_current_time
)


class StudyAgent:

    def __init__(self):

        # Get API key
        api_key = st.secrets["GEMINI_API_KEY"]

        # Gemini client
        self.client = genai.Client(
            api_key=api_key
        )

        # Stable Gemini model
        self.model = "gemini-3.5-flash-lite"

        # Conversation memory
        self.history = []

    def ask_gemini(self, prompt):

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        return response.text

    def ask(self, user_message):

        message = user_message.lower().strip()

        # --------------------------------
        # TOOL 1: CALCULATOR
        # --------------------------------

        if message.startswith("calculate "):

            expression = user_message[10:].strip()

            result = calculator(expression)

            return f"🧮 Calculator Result: {result}"

        # --------------------------------
        # TOOL 2: STUDY PLAN
        # --------------------------------

        if "study plan" in message:

            subject = "General Studies"
            hours = 2

            # Try to detect subject
            if " for " in message:
                subject = user_message.split(" for ", 1)[1]

            # Try to detect hours
            for number in range(1, 13):
                if f"{number} hour" in message:
                    hours = number
                    break

            result = create_study_plan(
                subject,
                hours
            )

            return result

        # --------------------------------
        # TOOL 3: CURRENT TIME
        # --------------------------------

        if (
            "current time" in message
            or "what time is it" in message
            or "current date" in message
        ):

            result = get_current_time()

            return f"🕒 Current date and time: {result}"

        # --------------------------------
        # NORMAL AI QUESTION
        # --------------------------------

        self.history.append(
            f"User: {user_message}"
        )

        conversation = "\n".join(
            self.history[-10:]
        )

        prompt = f"""
You are an AI Study Agent for college students.

Help the student with clear and simple explanations.

Conversation:
{conversation}

Student's question:
{user_message}

Give a useful and easy-to-understand answer.
"""

        response = self.ask_gemini(prompt)

        self.history.append(
            f"Assistant: {response}"
        )

        return response
