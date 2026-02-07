from backend.utils.helpers import normalize_text, keywords_from_text
from backend.core.config import settings
import os


def heuristic_score(resume_text: str, jd_text: str) -> dict:
    r_text = normalize_text(resume_text)
    jd_text_n = normalize_text(jd_text)
    jd_keys = set(keywords_from_text(jd_text_n, limit=80))
    resume_keys = set(keywords_from_text(r_text, limit=200))
    matched = jd_keys.intersection(resume_keys)
    if jd_keys:
        ratio = len(matched) / len(jd_keys)
    else:
        ratio = 0.0
    score = int(ratio * 100)
    reasons = []
    if score < settings.ATS_THRESHOLD:
        reasons.append("Missing role-relevant keywords")
    if len(r_text.split()) < 50:
        reasons.append("Resume seems short or missing details")
    return {"score": score, "matched": list(matched)[:20], "reasons": reasons}


def call_grok(prompt: str) -> str | None:
    # Minimal Grok HTTP adapter using requests. If no GROK_API_KEY is configured
    # the caller should fallback to heuristic.
    key = settings.GROK_API_KEY
    if not key:
        return None
    try:
        import requests
    except Exception:
        return None

    url = "https://api.grok.ai/v1/chat/completions"
    payload = {"model": "grok-1", "messages": [{"role": "user", "content": prompt}], "max_tokens": 600}
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=20)
        r.raise_for_status()
        j = r.json()
        # try typical response shapes
        if "choices" in j and isinstance(j["choices"], list) and j["choices"]:
            c = j["choices"][0]
            if "message" in c and "content" in c["message"]:
                return c["message"]["content"]
            if "text" in c:
                return c["text"]
        if "output" in j:
            return j["output"]
    except Exception:
        return None
    return None


def llm_evaluate(resume_text: str, jd_text: str) -> dict:
    # Try Grok if configured; otherwise fallback to heuristic
    prompt = (
        "You are an expert ATS evaluator. Given a job description and a candidate resume text, produce a JSON output like:\n"
        "{"
        "'score':int,'reasons':[...],'matches':[...]}\n\n"
        f"JD:\n{jd_text}\n\nResume:\n{resume_text}\n"
    )
    grok_text = call_grok(prompt)
    if grok_text:
        import json, re

        js = re.search(r"\{.*\}", grok_text, re.S)
        if js:
            try:
                return json.loads(js.group(0))
            except Exception:
                pass
    return heuristic_score(resume_text, jd_text)


def evaluate(resume_text: str, jd_text: str) -> dict:
    return llm_evaluate(resume_text, jd_text)
