import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def evaluate_resume(resume_text, jd_text, prompt_template):
    prompt = f"""
{prompt_template}

Job Description:
{jd_text}

Resume:
{resume_text}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content
