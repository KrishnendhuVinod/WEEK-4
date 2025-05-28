import sympy as sp
from sympy import Eq, solve, Symbol, diff, simplify
from typing import Dict, Any
import autogen
import os
from dotenv import load_dotenv

# Load API Key
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

# Define math tools
def solve_math_problem(problem: str) -> str:
    x = Symbol('x')
    try:
        if "differentiate" in problem.lower() or "derivative" in problem.lower():
            expr = problem.split("of")[1]
            result = diff(sp.sympify(expr.strip()))
        elif "=" in problem:
            lhs, rhs = problem.split("=")
            equation = Eq(sp.sympify(lhs.strip()), sp.sympify(rhs.strip()))
            result = solve(equation)
        else:
            result = simplify(problem)
        return str(result)
    except Exception as e:
        return f"Error solving problem: {str(e)}"

def verify_solution(problem: str, proposed_solution: str) -> str:
    try:
        if "=" in problem:
            lhs, rhs = problem.split("=")
            expr = Eq(sp.sympify(lhs.strip()), sp.sympify(rhs.strip()))
            solutions = eval(proposed_solution)
            all_verified = all(expr.subs(Symbol('x'), sol).doit() == True for sol in solutions)
            return "Verified" if all_verified else "Incorrect"
        else:
            recomputed = solve_math_problem(problem)
            return "Verified" if recomputed == proposed_solution else "Incorrect"
    except Exception as e:
        return f"Error verifying solution: {str(e)}"

# Gemini config for Autogen
config_list = [
    {
        "model": "models/gemini-1.5-flash-latest",
        "api_key": gemini_api_key,
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "api_type": "google",
    }
]

llm_config = {
    "config_list": config_list,
    "temperature": 0.3,
}

# Define agents
problem_solver = autogen.AssistantAgent(
    name="ProblemSolver",
    llm_config=llm_config,
    system_message="Solve the given math problem using SymPy. Reply in plain text. Return the result only. Format math using LaTeX if needed."
)

verifier = autogen.AssistantAgent(
    name="Verifier",
    llm_config=llm_config,
    system_message="Check the solution using SymPy. Verify correctness. If incorrect, ask for correction. Say 'TERMINATE' when verified."
)

group_chat = autogen.GroupChat(
    agents=[problem_solver, verifier],
    messages=[],
    max_round=5,
    speaker_selection_method="round_robin"
)

group_chat_manager = autogen.GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config
)

# Start chat session
def run_math_tutor(problem: str):
    user_proxy = autogen.UserProxyAgent(
        name="User",
        human_input_mode="NEVER",
        code_execution_config=False
    )
    user_proxy.initiate_chat(
        group_chat_manager,
        message=f"Solve and verify: {problem}"
    )

#Main function
if __name__ == "__main__":
    print(" Math Tutor! Type 'exit' to quit.\n")
    while True:
        user_input = input("Enter a math problem: ").strip()
        if user_input.lower() == "exit":
            print(" Exiting Math Tutor.")
            break
        run_math_tutor(user_input)
