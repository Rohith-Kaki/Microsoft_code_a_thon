from backend.utils.helpers import normalize_text, keywords_from_text
from backend.core.config import settings
import os
# add imports
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def heuristic_score(resume_text: str, jd_text: str) -> dict:
    # Basic normalization already present in helpers
    r_text = normalize_text(resume_text)
    jd_text_n = normalize_text(jd_text)

    # If either piece is very short, keep old checks
    if not r_text or not jd_text_n:
        reasons = []
        if not r_text: reasons.append("Resume text appears empty")
        if not jd_text_n: reasons.append("Job description appears empty")
        return {"score": 0, "matched": [], "reasons": reasons}

    # Build TF-IDF vectorizer on both docs (unigrams + bigrams), filter english stopwords
    vec = TfidfVectorizer(ngram_range=(1,2), max_features=5000, stop_words="english")
    docs = [jd_text_n, r_text]
    X = vec.fit_transform(docs)
    sim = float(cosine_similarity(X[0:1], X[1:2])[0][0])  # 0..1
    score = int(sim * 100)

    # find top matched tokens by TF-IDF overlap (approx)
    feature_names = np.array(vec.get_feature_names_out())
    jd_vec = X[0].toarray().ravel()
    resume_vec = X[1].toarray().ravel()
    # elementwise min approximates shared importance
    shared = np.minimum(jd_vec, resume_vec)
    top_idx = shared.argsort()[::-1][:20]
    matched = [feature_names[i] for i in top_idx if shared[i] > 0]

    # Top JD keywords (what the JD emphasizes)
    jd_top_idx = jd_vec.argsort()[::-1][:20]
    jd_top = [feature_names[i] for i in jd_top_idx]

    # Find JD-important keywords missing (very low weight in resume)
    missing = [feature_names[i] for i in jd_top_idx if resume_vec[i] < 1e-3][:8]

    reasons = []
    suggestions = []

    if score < settings.ATS_THRESHOLD:
        if missing:
            reasons.append("Missing key skills: " + ", ".join(missing[:6]))
            suggestions.append("Consider highlighting experience or projects using: " + ", ".join(missing[:6]))
        else:
            reasons.append("Low semantic similarity between JD and resume (missing role-specific content)")
            suggestions.append("Add role-specific keywords and concrete project details matching the JD.")

    # provide positive feedback when matches exist
    if matched:
        suggestions.append("Strengths detected: " + ", ".join(matched[:6]))

    if len(r_text.split()) < 60:
        reasons.append("Resume seems short or missing details")
        suggestions.append("Add more project descriptions and measurable impact statements.")

    # If reasons remain empty, add a friendly success note
    if not reasons:
        reasons.append("Resume appears to match the JD well — consider polishing formatting and details.")

    return {
        "score": score,
        "matched": matched,
        "missing": missing,
        "reasons": reasons,
        "suggestions": suggestions,
    }

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
    # Improved prompt: explicit rubric, JSON-only response, and calibration guidance
    prompt = (
        "You are a precise ATS evaluator. Using the Job Description (JD) and the Resume text, produce a JSON object only (no extra commentary) with these fields:\n"
        "{\n  \"score\": <int 0-100>,\n  \"reasons\": [<short reasons why score is low/high>],\n  \"matches\": [<top matched keywords or phrases>],\n  \"missing\": [<important JD keywords not present>],\n  \"suggestions\": [<concise, actionable suggestions>]\n}\n\n"
        "Guidance for scoring (follow these heuristics when assigning the score):\n"
        "- Give a higher score when the resume contains concrete project descriptions, role-specific tools/technologies, measurable outcomes, and years of relevant experience.\n"
        "- Treat synonyms and common abbreviations as matches (e.g., 'NLP' ~ 'natural language processing').\n"
        "- Weigh demonstrated project experience and measurable impact more than generic skill lists.\n"
        "- If the resume shows strong alignment, scores should be in the 70-100 range; medium alignment ~40-70; poor alignment <40.\n"
        "- Return up to 12 top matches and up to 8 important missing keywords.\n"
        "Now evaluate strictly but fairly. Output only valid JSON that can be parsed.\n\n"
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


def decide_pass(result: dict) -> bool:
    """Decide pass/fail based on blended rules.

    Rules (configurable):
    - If score >= ATS_THRESHOLD => pass
    - Else if number of matched tokens >= ATS_MIN_MATCHES and score >= ATS_MIN_SCORE_FOR_PASS => pass
    - Else fail
    """
    score = int(result.get("score", 0))
    matched = result.get("matched") or []
    # Use configured thresholds
    if score >= settings.ATS_THRESHOLD:
        return True
    if len(matched) >= settings.ATS_MIN_MATCHES and score >= settings.ATS_MIN_SCORE_FOR_PASS:
        return True
    return False
