from typing import List, Dict


def generate_scenarios(jd_text: str, n: int = 3) -> List[Dict]:
    # Simple scenario generation based on JD keywords; can be improved with LLM
    keywords = [k for k in jd_text.split()[:10]]
    scenarios = []
    for i in range(n):
        scenarios.append({
            "id": i + 1,
            "title": f"Scenario {i+1}",
            "prompt": f"You are given this role context: {keywords[:6]}. Describe how you'd approach a real-world problem related to this role (scenario {i+1}).",
            "points": 20,
        })
    return scenarios


def evaluate_response(response_text: str) -> Dict:
    # Primitive rubric: length & presence of action words
    score = 0
    if len(response_text.split()) > 50:
        score += 15
    action_words = ["design", "deploy", "optimize", "test", "monitor", "scale"]
    hits = sum(1 for w in action_words if w in response_text.lower())
    score += min(20, hits * 5)
    return {"score": score, "notes": f"action_hits={hits}"}
