from datetime import datetime


def calculator(expression: str) -> str:
    """
    Calculates a mathematical expression.

    Args:
        expression: A mathematical expression such as 25 * 4.

    Returns:
        The calculated result.
    """
    try:
        allowed = "0123456789+-*/(). %"

        if not all(char in allowed for char in expression):
            return "Invalid mathematical expression."

        result = eval(expression, {"__builtins__": {}}, {})

        return str(result)

    except Exception:
        return "Could not calculate the expression."


def create_study_plan(subject: str, hours: int) -> str:
    """
    Creates a simple study plan.

    Args:
        subject: Subject the student wants to study.
        hours: Number of hours available.

    Returns:
        A simple study plan.
    """

    if hours <= 0:
        return "Please provide a positive number of hours."

    if hours == 1:
        return (
            f"Study plan for {subject}:\n"
            "• 20 minutes - Learn concepts\n"
            "• 25 minutes - Practice questions\n"
            "• 15 minutes - Quick revision"
        )

    if hours == 2:
        return (
            f"Study plan for {subject}:\n"
            "• 45 minutes - Learn concepts\n"
            "• 45 minutes - Practice problems\n"
            "• 30 minutes - Revision and notes"
        )

    return (
        f"Study plan for {subject} ({hours} hours):\n"
        "• 40% - Learn concepts\n"
        "• 40% - Practice problems\n"
        "• 20% - Revision and self-test"
    )


def get_current_time() -> str:
    """
    Returns the current date and time.

    Returns:
        Current date and time.
    """

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
