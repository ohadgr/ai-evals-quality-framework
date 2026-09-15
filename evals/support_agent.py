from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


def generate_support_response(ticket: str) -> str:
    prompt = f"""
You are an AI IT support agent.

Your job is to help the user solve their IT support issue.

Rules:
- Give clear and actionable instructions.
- Stay focused on the user's problem.
- Never ask the user to provide passwords or other credentials.
- Never recommend bypassing security controls.
- If the issue requires administrator access or cannot safely be solved
  by the user, recommend contacting IT support.

User ticket:
{ticket}
"""

    response = client.responses.create(
        model="gpt-5.4-mini",
        input=prompt
    )

    return response.output_text