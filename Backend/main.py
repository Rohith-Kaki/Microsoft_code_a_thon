from fastapi import FastAPI, UploadFile, File, Form
from resume_parser import extract_text_from_pdf
from ats import evaluate_resume

app = FastAPI()

def load_jd(role):
    with open(f"jd/{role}.txt") as f:
        return f.read()

def load_prompt():
    with open("llm_prompt.txt") as f:
        return f.read()

@app.post("/screen")
async def screen_resume(role: str = Form(...), file: UploadFile = File(...)):
    file_bytes = await file.read()

    resume_text = extract_text_from_pdf(file_bytes)
    jd_text = load_jd(role)
    prompt_template = load_prompt()

    result = evaluate_resume(resume_text, jd_text, prompt_template)

    return {
        "role": role,
        "result": result
    }
